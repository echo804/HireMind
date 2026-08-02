import uuid, logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.config.settings import settings
from app.modules.interview.models import InterviewSession, InterviewStatus, InterviewType
from app.modules.interview.repository import InterviewRepository
from app.modules.interview.schemas import (
    CreateInterviewRequest, AnswerRequest, InterviewSessionResponse,
    InterviewListItem, NextQuestionResponse, ReportResponse,
)
from app.modules.interview.agent import (
    generate_question, generate_question_stream, evaluate_interview,
    generate_hint, polish_answer as polish_answer_ai,
)
from app.modules.resume.repository import ResumeRepository
from app.modules.knowledgebase.service import KnowledgeService

logger = logging.getLogger(__name__)


def _resolve_difficulty(session, answers: list[dict]) -> str:
    """难度解析：用户选择的固定难度优先；默认 normal 时按已答评估均值自适应"""
    user_choice = getattr(session, "difficulty", None)
    if user_choice in ("easy", "normal", "hard"):
        return user_choice
    prev_evals = [a.get("evaluation") for a in answers if isinstance(a.get("evaluation"), (int, float))]
    if prev_evals:
        avg = sum(prev_evals) / len(prev_evals)
        return "hard" if avg >= 7 else ("easy" if avg < 4 else "normal")
    return "normal"


def _build_resume_context(resume) -> str:
    if not resume:
        return ""
    parts = []
    if resume.name:
        parts.append(f"姓名：{resume.name}")
    if resume.position:
        parts.append(f"职位：{resume.position}")
    if resume.summary:
        parts.append(f"摘要：{resume.summary}")
    if resume.skills:
        parts.append(f"技能：{', '.join(resume.skills)}")
    if resume.experience:
        exp_text = []
        for e in resume.experience:
            exp_text.append(f"{e.get('title', '')} @ {e.get('company', '')} ({e.get('duration', '')}): {e.get('description', '')}")
        parts.append("工作经历：\n" + "\n".join(exp_text))
    if resume.education:
        edu_text = []
        for e in resume.education:
            edu_text.append(f"{e.get('school', '')} - {e.get('degree', '')} ({e.get('major', '')}, {e.get('year', '')})")
        parts.append("教育背景：\n" + "\n".join(edu_text))
    return "\n".join(parts)


class InterviewService:
    def __init__(self, db: AsyncSession):
        self.repo = InterviewRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.kb_service = KnowledgeService(db)

    async def _build_knowledge_context(self, direction: str, user_id: str) -> str:
        """Search knowledge base and return relevant context for interview questions"""
        try:
            results = await self.kb_service.search(direction, top_k=3, user_id=user_id)
            if not results:
                return ""
            chunks = []
            for r in results:
                chunks.append(f"[来源: {r.get('document_name', '未知')}] {r['content']}")
            return "\n---\n".join(chunks)
        except Exception as e:
            logger.warning(f"Knowledge search failed: {e}")
            return ""

    async def create(self, req: CreateInterviewRequest, user_id: str) -> InterviewSessionResponse:
        # Load resume context if provided
        resume_context = ""
        resume_entity = None
        if req.resume_id:
            resume_entity = await self.resume_repo.find_by_id(uuid.UUID(req.resume_id))
            if resume_entity:
                resume_context = _build_resume_context(resume_entity)

        session = InterviewSession(
            user_id=uuid.UUID(user_id),
            resume_id=uuid.UUID(req.resume_id) if req.resume_id else None,
            direction=req.direction,
            interview_type=InterviewType(req.interview_type),
            total_questions=req.total_questions,
            use_knowledge=req.use_knowledge,
            difficulty=req.difficulty,
            interview_style=req.interview_style,
            status=InterviewStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
        )
        created = await self.repo.create(session)

        # Search knowledge base if enabled
        knowledge_context = ""
        if req.use_knowledge:
            knowledge_context = await self._build_knowledge_context(req.direction, user_id)

        # Generate first question
        try:
            q_data = await generate_question(settings, req.direction, req.total_questions, 0, [],
                                              resume_context=resume_context,
                                              knowledge_context=knowledge_context,
                                              difficulty=req.difficulty,
                                              user_id=user_id)
        except Exception as e:
            logger.error(f"generate_question failed: {e}")
            q_data = {"question": f"请介绍一下你在 {req.direction} 领域的技术栈和项目经验"}
        question_entry = {"index": 1, "question": q_data.get("question", "面试未完成，评估不完整")}
        created.questions_asked = [question_entry]
        created.current_question = 1
        await self.repo.save(created)

        return self._to_response(created)

    async def answer(self, session_id: str, req: AnswerRequest) -> NextQuestionResponse:
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        if session.status != InterviewStatus.IN_PROGRESS:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED)

        # Load resume context
        resume_context = ""
        if session.resume_id:
            resume_entity = await self.resume_repo.find_by_id(session.resume_id)
            if resume_entity:
                resume_context = _build_resume_context(resume_entity)

        current_q = session.questions_asked[-1] if session.questions_asked else {}
        answer_entry = {
            "index": session.current_question,
            "question": current_q.get("question", ""),
            "answer": req.answer,
            "evaluation": current_q.get("evaluation", 5),
        }
        answers = list(session.answers_given or [])
        answers.append(answer_entry)
        session.answers_given = answers

        if session.current_question >= session.total_questions:
            try:
                report = await evaluate_interview(settings, session.direction, answers,
                                                   user_id=str(session.user_id))
            except Exception as e:
                logger.error(f"evaluate_interview failed: {e}")
                report = {
                    "overall_score": 0, "feedback": "AI 评估暂时不可用，请稍后重试",
                    "strengths": [], "weaknesses": [], "suggestions": [],
                    "dimensions": {}, "per_question": [],
                }
            session.report = report
            session.status = InterviewStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)
            await self.repo.save(session)
            return NextQuestionResponse(
                question_index=session.current_question, total=session.total_questions,
                question="", session_id=str(session.id), is_completed=True,
            )

        # Load knowledge base context if enabled
        knowledge_context = ""
        if session.use_knowledge:
            knowledge_context = await self._build_knowledge_context(
                session.direction, str(session.user_id))

        try:
            q_data = await generate_question(settings, session.direction, session.total_questions,
                                              session.current_question, answers,
                                              resume_context=resume_context,
                                              knowledge_context=knowledge_context,
                                              user_id=str(session.user_id),
                                              difficulty=_resolve_difficulty(session, answers),
                                              interview_style=session.interview_style or "warm")
        except Exception as e:
            logger.error(f"generate_question (next) failed: {e}")
            q_data = {"question": f"请继续回答第{session.current_question + 1}题"}
        next_idx = session.current_question + 1
        question_entry = {"index": next_idx, "question": q_data.get("question", "面试未完成，评估不完整")}
        questions = list(session.questions_asked or [])
        questions.append(question_entry)
        session.questions_asked = questions
        session.current_question = next_idx
        await self.repo.save(session)

        return NextQuestionResponse(
            question_index=next_idx, total=session.total_questions,
            question=question_entry["question"], session_id=str(session.id),
        )

    async def answer_stream(self, session_id: str, req: AnswerRequest):
        """流式回答：记录答案后逐 token 推送 AI 生成的问题"""
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            yield {"error": "面试会话不存在"}
            return
        if session.status != InterviewStatus.IN_PROGRESS:
            yield {"error": "面试已结束"}
            return

        # Load resume context
        resume_context = ""
        if session.resume_id:
            resume_entity = await self.resume_repo.find_by_id(session.resume_id)
            if resume_entity:
                resume_context = _build_resume_context(resume_entity)

        current_q = session.questions_asked[-1] if session.questions_asked else {}
        answer_entry = {
            "index": session.current_question,
            "question": current_q.get("question", ""),
            "answer": req.answer,
            "evaluation": current_q.get("evaluation", 5),
        }
        answers = list(session.answers_given or [])
        answers.append(answer_entry)
        session.answers_given = answers

        if session.current_question >= session.total_questions:
            try:
                report = await evaluate_interview(settings, session.direction, answers,
                                                   user_id=str(session.user_id))
            except Exception as e:
                logger.error(f"evaluate_interview failed: {e}")
                report = {
                    "overall_score": 0, "feedback": "AI 评估暂时不可用，请稍后重试",
                    "strengths": [], "weaknesses": [], "suggestions": [],
                    "dimensions": {}, "per_question": [],
                }
            session.report = report
            session.status = InterviewStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)
            await self.repo.save(session)
            yield {"is_completed": True, "question_index": session.current_question, "total": session.total_questions}
            return

        # Load knowledge base context if enabled
        knowledge_context = ""
        if session.use_knowledge:
            knowledge_context = await self._build_knowledge_context(
                session.direction, str(session.user_id))

        next_idx = session.current_question + 1
        question_text = ""
        # 难度：用户选择优先，否则按已答题目 evaluation 均值自适应
        difficulty = _resolve_difficulty(session, answers)
        try:
            async for chunk in generate_question_stream(
                settings, session.direction, session.total_questions,
                session.current_question, answers,
                resume_context=resume_context,
                knowledge_context=knowledge_context,
                user_id=str(session.user_id),
                difficulty=difficulty,
                interview_style=session.interview_style or "warm",
            ):
                if "token" in chunk:
                    question_text += chunk["token"]
                    yield {"token": chunk["token"]}
                elif "question" in chunk:
                    # 最终解析结果，更新 session
                    q_data = chunk
                    question_entry = {"index": next_idx, "question": q_data.get("question", question_text)}
                    questions = list(session.questions_asked or [])
                    questions.append(question_entry)
                    session.questions_asked = questions
                    session.current_question = next_idx
                    await self.repo.save(session)
                    yield {
                        "question_index": next_idx,
                        "total": session.total_questions,
                        "question": question_entry["question"],
                        "feedback": q_data.get("feedback", ""),
                        "evaluation": q_data.get("evaluation", 5),
                        "difficulty": difficulty,
                        "session_id": str(session.id),
                    }
                    return
        except Exception as e:
            logger.error(f"generate_question_stream failed: {e}")
            fallback = f"请继续回答第{next_idx}题"
            question_text = fallback
            for char in fallback:
                yield {"token": char}

        # 兜底：如果流式没有正常结束
        question_entry = {"index": next_idx, "question": question_text}
        questions = list(session.questions_asked or [])
        questions.append(question_entry)
        session.questions_asked = questions
        session.current_question = next_idx
        await self.repo.save(session)
        yield {
            "question_index": next_idx,
            "total": session.total_questions,
            "question": question_text,
            "feedback": "",
            "evaluation": 5,
            "difficulty": difficulty,
            "session_id": str(session.id),
        }

    async def skip_question(self, session_id: str):
        """跳过当前题：不记录答案，直接生成下一题（流式）"""
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            yield {"error": "面试会话不存在"}
            return
        if session.status != InterviewStatus.IN_PROGRESS:
            yield {"error": "面试已结束"}
            return

        # 加载简历上下文
        resume_context = ""
        if session.resume_id:
            resume_entity = await self.resume_repo.find_by_id(session.resume_id)
            if resume_entity:
                resume_context = _build_resume_context(resume_entity)

        knowledge_context = ""
        if session.use_knowledge:
            knowledge_context = await self._build_knowledge_context(
                session.direction, str(session.user_id))

        answers = list(session.answers_given or [])
        next_idx = session.current_question + 1
        question_text = ""
        # 难度：用户选择优先，否则自适应
        difficulty = _resolve_difficulty(session, answers)
        try:
            async for chunk in generate_question_stream(
                settings, session.direction, session.total_questions,
                session.current_question, answers,
                resume_context=resume_context,
                knowledge_context=knowledge_context,
                user_id=str(session.user_id),
                difficulty=difficulty,
                interview_style=session.interview_style or "warm",
            ):
                if "token" in chunk:
                    question_text += chunk["token"]
                    yield {"token": chunk["token"]}
                elif "question" in chunk:
                    q_data = chunk
                    question_entry = {"index": next_idx, "question": q_data.get("question", question_text),
                                      "skipped": True}
                    questions = list(session.questions_asked or [])
                    questions.append(question_entry)
                    session.questions_asked = questions
                    session.current_question = next_idx
                    await self.repo.save(session)
                    yield {
                        "question_index": next_idx,
                        "total": session.total_questions,
                        "question": question_entry["question"],
                        "feedback": "你跳过了上一题，继续下一题。",
                        "evaluation": q_data.get("evaluation", 5),
                        "difficulty": difficulty,
                        "skipped": True,
                        "session_id": str(session.id),
                    }
                    return
        except Exception as e:
            logger.error(f"skip_question failed: {e}")
            fallback = f"请回答第{next_idx}题"
            question_text = fallback
            for char in fallback:
                yield {"token": char}

        question_entry = {"index": next_idx, "question": question_text, "skipped": True}
        questions = list(session.questions_asked or [])
        questions.append(question_entry)
        session.questions_asked = questions
        session.current_question = next_idx
        await self.repo.save(session)
        yield {
            "question_index": next_idx,
            "total": session.total_questions,
            "question": question_text,
            "feedback": "你跳过了上一题，继续下一题。",
            "evaluation": 5,
            "difficulty": difficulty,
            "skipped": True,
            "session_id": str(session.id),
        }

    async def hint_question(self, session_id: str):
        """给当前问题生成答题提示（流式返回纯文本）"""
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        if session.status != InterviewStatus.IN_PROGRESS:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED)
        questions = session.questions_asked or []
        if not questions:
            yield {"hint": "请先等待面试官提问。"}
            return
        current_q = questions[-1].get("question", "")
        try:
            hint = await generate_hint(settings, session.direction, current_q,
                                       user_id=str(session.user_id),
                                       interview_style=session.interview_style or "warm")
            for char in hint:
                yield {"token": char}
            yield {"hint": hint}
        except Exception as e:
            logger.error(f"generate_hint failed: {e}")
            yield {"hint": "（提示生成失败，请直接回答或换一题）"}

    async def polish_answer(self, session_id: str, answer: str):
        """润色候选人的回答（一次性返回）"""
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        questions = session.questions_asked or []
        current_q = questions[-1].get("question", "") if questions else ""
        try:
            polished = await polish_answer_ai(settings, current_q, answer,
                                              user_id=str(session.user_id))
            yield {"polished": polished}
        except Exception as e:
            logger.error(f"polish_answer failed: {e}")
            yield {"polished": answer, "error": "润色失败，已返回原回答"}

    async def end_session(self, session_id: str) -> InterviewSessionResponse:
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        if session.status == InterviewStatus.COMPLETED:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED, "完成了部分题目")

        answers = list(session.answers_given or [])
        # 至少回答了 3 道题才让 AI 出评估报告
        if len(answers) >= 3:
            try:
                report = await evaluate_interview(settings, session.direction, answers,
                                               user_id=str(session.user_id))
                session.report = report
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
        else:
            # 回答不足3题，给个兜底?
            if len(answers) == 0:
                session.report = {"overall_score": 0, "feedback": "未回答任何题目，无法评估", "dimensions": {}, "per_question": [], "strengths": [], "weaknesses": ["未完成面试"], "suggestions": ["建议完整参加面试以获得有效评估"]}
            else:
                ratio = len(answers) / session.total_questions
                base_score = max(10, int(ratio * 60))
                session.report = {"overall_score": base_score, "feedback": f"仅回答了 {len(answers)}/{session.total_questions} 道题目，评估仅供参考", "dimensions": {}, "per_question": [], "strengths": ["完成了部分题目"], "weaknesses": ["面试未完成，评估不完整"], "suggestions": ["建议完整回答所有题目以获得全面评估"]}

        session.status = InterviewStatus.COMPLETED
        session.completed_at = datetime.now(timezone.utc)
        await self.repo.save(session)
        return self._to_response(session)

    async def get_session(self, session_id: str) -> InterviewSessionResponse:
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        return self._to_response(session)

    async def delete_session(self, session_id: str):
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        await self.repo.delete(session)

    async def export_pdf(self, session_id: str) -> bytes:
        from weasyprint import HTML
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        if session.status != InterviewStatus.COMPLETED:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED, "面试未完成，无法导出报告")

        report = session.report or {}
        answers = session.answers_given or []
        qa_rows = "".join(
            f"<tr><td style='padding:8px;border:1px solid #ddd;vertical-align:top;font-weight:bold'>第{a['index']}题</td>"
            f"<td style='padding:8px;border:1px solid #ddd;'><strong>{a.get('question','')}</strong><br><br>{a['answer']}</td></tr>"
            for a in answers
        )
        strengths = "".join(f"<li>{s}</li>" for s in report.get("strengths", []))
        weaknesses = "".join(f"<li>{w}</li>" for w in report.get("weaknesses", []))
        suggestions = "".join(f"<li>{s}</li>" for s in report.get("suggestions", []))

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>面试报告</title>
<style>body{{font-family:'WenQuanYi Micro Hei','Noto Sans CJK SC',sans-serif;padding:40px;color:#333}}h1{{text-align:center;color:#1a56db}}h2{{color:#1a56db;border-bottom:2px solid #1a56db;padding-bottom:4px}}.score{{text-align:center;font-size:48px;color:#1a56db;margin:20px 0}}table{{width:100%;border-collapse:collapse;margin:16px 0}}ul{{margin:4px 0;padding-left:20px}}li{{margin:4px 0}}</style></head>
<body>
<h1>AI 面试报告</h1>
<p style="text-align:center">方向: {session.direction} | 题目数: {session.total_questions} | 日期: {session.created_at.strftime('%Y-%m-%d %H:%M') if session.created_at else '-'}</p>
<div class="score">总分: {report.get('overall_score', 0)} / 100</div>
<h2>综合评价</h2>
<p>{report.get('feedback', '无')}</p>
<h2>优势</h2><ul>{strengths or '<li>无</li>'}</ul>
<h2>不足</h2><ul>{weaknesses or '<li>无</li>'}</ul>
<h2>建议</h2><ul>{suggestions or '<li>无</li>'}</ul>
<h2>问答记录</h2>
<table>{qa_rows}</table>
</body></html>"""
        return HTML(string=html).write_pdf()

    async def batch_delete(self, ids: list[str]):
        for sid in ids:
            try:
                session = await self.repo.find_by_id(uuid.UUID(sid))
                if session:
                    await self.repo.delete(session)
            except Exception:
                pass

    async def list_sessions(self, user_id: str) -> list[InterviewListItem]:
        sessions = await self.repo.find_by_user(uuid.UUID(user_id))
        return [InterviewListItem(
            id=str(s.id), direction=s.direction,
            interview_type=s.interview_type.value, status=s.status.value,
            question_count=s.current_question, created_at=s.created_at,
        ) for s in sessions]

    async def review_questions(self, user_id: str) -> list[dict]:
        """聚合所有已完成会话的问题清单，供面试回顾本使用"""
        sessions = await self.repo.find_by_user(uuid.UUID(user_id))
        items: list[dict] = []
        for s in sessions:
            if s.status != InterviewStatus.COMPLETED:
                continue
            answers = s.answers_given or []
            report = s.report or {}
            per_q = {p.get("index"): p for p in (report.get("per_question") or [])}
            for a in answers:
                if not a or a.get("skipped"):
                    continue
                question = (a.get("question") or "").strip()
                answer = (a.get("answer") or "").strip()
                if not question or not answer:
                    continue
                pq = per_q.get(a.get("index")) or {}
                items.append({
                    "session_id": str(s.id),
                    "direction": s.direction,
                    "index": a.get("index", 0),
                    "question": question,
                    "answer": answer,
                    "score": pq.get("score"),
                    "comment": pq.get("comment", ""),
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                })
        # 按时间倒序（最新在前）
        items.sort(key=lambda x: x["created_at"] or "", reverse=True)
        return items

    async def get_report(self, session_id: str) -> ReportResponse:
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        if session.status != InterviewStatus.COMPLETED:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED, "面试未完成，无法查看报告")
        report = session.report or {"overall_score": 0, "feedback": "尚未生成评估报告", "dimensions": {}, "per_question": [], "strengths": [], "weaknesses": [], "suggestions": []}
        return self._build_report_response(session, report)

    async def re_evaluate(self, session_id: str) -> ReportResponse:
        """重新生成评估报告（AI 失败后可重跑）"""
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        answers = list(session.answers_given or [])
        if not answers:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED, "没有可评估的回答记录")
        report = await evaluate_interview(settings, session.direction, answers,
                                          user_id=str(session.user_id))
        session.report = report
        if session.status != InterviewStatus.COMPLETED:
            session.status = InterviewStatus.COMPLETED
            session.completed_at = datetime.now(timezone.utc)
        await self.repo.save(session)
        return self._build_report_response(session, report)

    def _build_report_response(self, session, report: dict) -> ReportResponse:
        return ReportResponse(
            session_id=str(session.id), direction=session.direction,
            total_questions=session.total_questions,
            score=report.get("overall_score", 0),
            feedback=report.get("feedback", ""),
            dimensions=report.get("dimensions", {}),
            per_question=report.get("per_question", []),
            strengths=report.get("strengths", []),
            weaknesses=report.get("weaknesses", []),
            suggestions=report.get("suggestions", []),
            created_at=session.created_at,
        )

    def _to_response(self, s: InterviewSession) -> InterviewSessionResponse:
        return InterviewSessionResponse(
            id=str(s.id), direction=s.direction,
            interview_type=s.interview_type.value, status=s.status.value,
            current_question=s.current_question, total_questions=s.total_questions,
            difficulty=s.difficulty, interview_style=s.interview_style,
            questions_asked=s.questions_asked or [],
            answers_given=s.answers_given or [],
            report=s.report, started_at=s.started_at, completed_at=s.completed_at,
            created_at=s.created_at,
        )
