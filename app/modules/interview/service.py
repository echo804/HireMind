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
from app.modules.interview.agent import generate_question, evaluate_interview
from app.modules.resume.repository import ResumeRepository
from app.modules.knowledgebase.service import KnowledgeService

logger = logging.getLogger(__name__)



def _build_resume_context(resume) -> str:
    if not resume:
        return ""
    parts = []
    if resume.name:
        parts.append(f"??????{resume.name}")
    if resume.position:
        parts.append(f"?????{resume.position}")
    if resume.summary:
        parts.append(f"?????{resume.summary}")
    if resume.skills:
        parts.append(f"???{', '.join(resume.skills)}")
    if resume.experience:
        exp_text = []
        for e in resume.experience:
            exp_text.append(f"{e.get('title', '')} @ {e.get('company', '')} ({e.get('duration', '')}): {e.get('description', '')}")
        parts.append("?????\n" + "\n".join(exp_text))
    if resume.education:
        edu_text = []
        for e in resume.education:
            edu_text.append(f"{e.get('school', '')} - {e.get('degree', '')} ({e.get('major', '')}, {e.get('year', '')})")
        parts.append("?????\n" + "\n".join(edu_text))
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
                    "score": 0, "feedback": "AI 评估暂时不可用，请稍后重试",
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
                                              user_id=str(session.user_id))
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

    async def end_session(self, session_id: str) -> InterviewSessionResponse:
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        if session.status == InterviewStatus.COMPLETED:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED, "完成了部分题目")

        answers = list(session.answers_given or [])
        # ??? 3 ?????? AI ??????????????
        if len(answers) >= 3:
            try:
                report = await evaluate_interview(settings, session.direction, answers,
                                               user_id=str(session.user_id))
                session.report = report
            except Exception as e:
                logger.error(f"Evaluation failed: {e}")
        else:
            # ?????????
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

    async def get_report(self, session_id: str) -> ReportResponse:
        session = await self.repo.find_by_id(uuid.UUID(session_id))
        if not session:
            raise BusinessException(ErrorCode.INTERVIEW_SESSION_NOT_FOUND)
        if session.status != InterviewStatus.COMPLETED:
            raise BusinessException(ErrorCode.INTERVIEW_ALREADY_COMPLETED, "??????")
        report = session.report or {"overall_score": 0, "feedback": "尚未生成评估报告", "dimensions": {}, "per_question": [], "strengths": [], "weaknesses": [], "suggestions": []}
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
            questions_asked=s.questions_asked or [],
            answers_given=s.answers_given or [],
            report=s.report, started_at=s.started_at, completed_at=s.completed_at,
            created_at=s.created_at,
        )
