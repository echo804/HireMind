import uuid, os, asyncio, logging
from pathlib import Path

from app.common.exception.handlers import BusinessException
from app.common.exception.error_code import ErrorCode
from app.modules.resume.models import ResumeEntity, ResumeStatus
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.schemas import ResumeDetail, ResumeListItem, ResumeResponse
from app.modules.resume.parser import parse_file
from app.modules.resume.analyzer import analyze_resume, analyze_resume_quality, polish_resume_text
from app.infrastructure.cache import cache_get, cache_set, invalidate_user_cache

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {".pdf": "pdf", ".docx": "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_DIR = Path("./uploads/resumes")


def _build_resume_text(e: ResumeEntity) -> str:
    """将解析后的简历实体拼成纯文本（供 AI 诊断/润色）"""
    parts = []
    if e.name:
        parts.append(f"姓名：{e.name}")
    if e.email:
        parts.append(f"邮箱：{e.email}")
    if e.phone:
        parts.append(f"电话：{e.phone}")
    if e.position:
        parts.append(f"目标岗位：{e.position}")
    if e.summary:
        parts.append(f"个人简介：{e.summary}")
    if e.skills:
        parts.append(f"技能：{', '.join(e.skills)}")
    if e.experience:
        exp_lines = []
        for x in e.experience:
            company = x.get("company", "") if isinstance(x, dict) else ""
            title = x.get("title", "") if isinstance(x, dict) else ""
            duration = x.get("duration", "") if isinstance(x, dict) else ""
            desc = x.get("description", "") if isinstance(x, dict) else ""
            exp_lines.append(f"- {title} @ {company}（{duration}）：{desc}")
        if exp_lines:
            parts.append("工作经历：\n" + "\n".join(exp_lines))
    if e.education:
        edu_lines = []
        for x in e.education:
            school = x.get("school", "") if isinstance(x, dict) else ""
            degree = x.get("degree", "") if isinstance(x, dict) else ""
            major = x.get("major", "") if isinstance(x, dict) else ""
            year = x.get("year", "") if isinstance(x, dict) else ""
            edu_lines.append(f"- {school} - {degree}（{major}, {year}）")
        if edu_lines:
            parts.append("教育背景：\n" + "\n".join(edu_lines))
    return "\n".join(parts)


class ResumeService:
    def __init__(self, db):
        self.repo = ResumeRepository(db)

    async def upload(self, user_id: str, file_content: bytes, filename: str) -> ResumeResponse:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_TYPES:
            raise BusinessException(ErrorCode.STORAGE_INVALID_TYPE, f"Unsupported file type: {ext}")
        if len(file_content) > MAX_FILE_SIZE:
            raise BusinessException(ErrorCode.STORAGE_FILE_TOO_LARGE, "File exceeds 10MB limit")

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid.uuid4())
        save_name = f"{file_id}{ext}"
        save_path = UPLOAD_DIR / save_name
        save_path.write_bytes(file_content)

        entity = ResumeEntity(
            user_id=uuid.UUID(user_id),
            filename=filename,
            file_path=str(save_path),
            file_size=len(file_content),
            file_type=ALLOWED_TYPES[ext],
            status=ResumeStatus.PROCESSING,
        )
        created = await self.repo.create(entity)

        # 上传成功后失效列表缓存，确保新简历立即可见
        await invalidate_user_cache("resume", user_id)

        # 后台异步 AI 分析（使用独立 DB session）
        import asyncio
        from app.infrastructure.database import async_session_factory
        asyncio.create_task(self._process_async(async_session_factory, save_path, created.id, user_id, str(created.user_id)))

        resp = self._to_response(created)
        return resp

    async def _process_async(self, session_factory, save_path: Path, entity_id, user_id: str, owner_id: str):
        """独立 session 的异步处理（不受请求生命周期限制）"""
        async with session_factory() as db:
            repo = ResumeRepository(db)
            entity = await repo.find_by_id(str(entity_id))
            if not entity:
                return
            svc = ResumeService.__new__(ResumeService)
            svc.repo = repo
            await svc._process_resume(save_path, entity, user_id)

    async def _process_resume(self, save_path: Path, entity: ResumeEntity, user_id: str):
        """后台任务：解析 PDF → AI 分析 → 更新状态和进度"""
        try:
            logger.info(f"_process_resume START: entity_id={entity.id}, user_id={user_id}")
            entity.progress = 10
            await self.repo.save(entity)

            text, content_hash = parse_file(str(save_path))
            entity.progress = 30
            await self.repo.save(entity)

            entity.progress = 50
            await self.repo.save(entity)
            analysis = await analyze_resume(text, user_id=user_id)
            entity.progress = 90
            entity.name = analysis.get("name")
            entity.email = analysis.get("email")
            entity.phone = analysis.get("phone")
            entity.position = analysis.get("position")
            entity.skills = analysis.get("skills", [])
            entity.experience = analysis.get("experience", [])
            entity.education = analysis.get("education", [])
            entity.summary = analysis.get("summary", "")
            entity.score = min(max(int(analysis.get("score", 50)), 0), 100)
            entity.content_hash = content_hash
            entity.status = ResumeStatus.DONE
            entity.progress = 100
        except Exception as e:
            logger.error(f"Resume analysis failed: {e}")
            entity.status = ResumeStatus.FAILED
            entity.summary = f"Analysis failed: {str(e)[:200]}"
            entity.progress = 0
            save_path.unlink(missing_ok=True)
        finally:
            await self.repo.save(entity)

    async def get_by_id(self, user_id: str, resume_id: str):
        entity = await self.repo.find_by_id(resume_id)
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "Resume not found")
        if entity.status == ResumeStatus.PROCESSING:
            save_path = Path(entity.file_path) if entity.file_path else None
            if save_path and save_path.exists():
                await self._process_resume(save_path, entity, user_id)
        return self._to_detail(entity)

    async def list_resumes(self, user_id: str, query: str | None = None) -> list[ResumeListItem]:
        # 搜索不走缓存
        if query:
            entities = await self.repo.search(uuid.UUID(user_id), query)
            return [self._to_list_item(e) for e in entities]

        # 读缓存
        cached = await cache_get("resume", "list", user_id)
        if cached is not None:
            return [ResumeListItem(**item) for item in cached]

        entities = await self.repo.find_by_user(uuid.UUID(user_id))
        result = [self._to_list_item(e) for e in entities]
        await cache_set("resume", "list", user_id, data=[item.model_dump() for item in result], ttl=300)
        return result

    async def delete_resume(self, user_id: str, resume_id: str):
        entity = await self.repo.find_by_id(resume_id)
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "Resume not found")
        path = Path(entity.file_path) if entity.file_path else None
        if path and path.exists():
            path.unlink()
        await self.repo.delete(entity)
        await invalidate_user_cache("resume", user_id)

    async def batch_delete_resumes(self, user_id: str, ids: list[str]) -> int:
        """批量删除：逐个校验归属后删除文件与记录，返回实际删除数"""
        deleted = 0
        for rid in ids:
            try:
                await self.delete_resume(user_id, rid)
                deleted += 1
            except BusinessException:
                continue  # 跳过不属于当前用户或不存在的 id
        return deleted

    async def check_duplicate(self, user_id: str, content_hash: str, exclude_id: str | None = None) -> dict | None:
        """按 content_hash 检测同用户是否已有重复简历（精确去重，可排除自身）"""
        if not content_hash:
            return None
        import sqlalchemy as sa
        q = sa.select(ResumeEntity).where(
            ResumeEntity.user_id == uuid.UUID(user_id),
            ResumeEntity.content_hash == content_hash,
            ResumeEntity.status == ResumeStatus.DONE,
        )
        if exclude_id:
            q = q.where(ResumeEntity.id != uuid.UUID(exclude_id))
        result = await self.repo.db.execute(q)
        dup = result.scalars().first()
        if not dup:
            return None
        return {"duplicate_of": str(dup.id), "duplicate_filename": dup.filename or ""}

    async def get_duplicate(self, user_id: str, resume_id: str) -> dict | None:
        """按简历的 content_hash 检测是否存在重复（详情页轮询到 done 后调用）"""
        entity = await self.repo.find_by_id(resume_id)
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "Resume not found")
        return await self.check_duplicate(user_id, entity.content_hash or "", exclude_id=resume_id)

    async def update_resume(self, user_id: str, resume_id: str, req) -> ResumeDetail:
        """简历人工校正：更新可编辑字段"""
        entity = await self.repo.find_by_id(resume_id)
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "Resume not found")
        update_map = {
            "name": "name", "email": "email", "phone": "phone",
            "position": "position", "skills": "skills",
            "experience": "experience", "education": "education",
            "summary": "summary",
        }
        for field, attr in update_map.items():
            val = getattr(req, field, None)
            if val is not None:
                setattr(entity, attr, val)
        if entity.status == ResumeStatus.FAILED:
            entity.status = ResumeStatus.DONE
        await self.repo.save(entity)
        await invalidate_user_cache("resume", user_id)
        return self._to_detail(entity)

    def _to_response(self, e: ResumeEntity) -> ResumeResponse:
        return ResumeResponse(
            id=str(e.id),
            filename=e.filename or "",
            name=e.name,
            position=e.position,
            score=e.score,
            status=e.status.value if e.status else "",
            created_at=e.created_at.isoformat() if e.created_at else "",
        )

    def _to_list_item(self, e: ResumeEntity) -> ResumeListItem:
        return ResumeListItem(
            id=str(e.id),
            filename=e.filename or "",
            name=e.name,
            position=e.position,
            score=e.score,
            status=e.status.value if e.status else "",
            created_at=e.created_at.isoformat() if e.created_at else "",
        )

    def _to_detail(self, e: ResumeEntity) -> ResumeDetail:
        return ResumeDetail(
            id=str(e.id),
            filename=e.filename or "",
            name=e.name,
            email=e.email,
            phone=e.phone,
            position=e.position,
            skills=e.skills or [],
            experience=e.experience or [],
            education=e.education or [],
            summary=e.summary or "",
            score=e.score or 0,
            progress=e.progress or 0,
            status=e.status.value if e.status else "",
            created_at=e.created_at.isoformat() if e.created_at else "",
        )

    async def analyze_quality(self, user_id: str, resume_id: str) -> dict:
        """AI 按面试官手册对简历分层诊断"""
        entity = await self.repo.find_by_id(resume_id)
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "Resume not found")
        text = _build_resume_text(entity)
        if not text.strip():
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "简历内容为空，无法分析")
        return await analyze_resume_quality(text, entity.position or "", user_id)

    async def polish(self, user_id: str, resume_id: str) -> dict:
        """AI 润色简历文本"""
        entity = await self.repo.find_by_id(resume_id)
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "Resume not found")
        text = _build_resume_text(entity)
        if not text.strip():
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "简历内容为空，无法润色")
        return await polish_resume_text(text, user_id)

    async def save_polished(self, user_id: str, resume_id: str, polished_text: str) -> ResumeDetail:
        """将润色后的简历文本保存回简历（更新 summary 与 experience 描述，保留解析结构）"""
        entity = await self.repo.find_by_id(resume_id)
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "Resume not found")
        if not polished_text or not polished_text.strip():
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND, "润色内容为空")
        # 用润色文本替换 summary 字段，保留结构化字段
        entity.summary = polished_text.strip()
        await self.repo.save(entity)
        await invalidate_user_cache("resume", user_id)
        return self._to_detail(entity)
