import uuid, os, asyncio, logging
from pathlib import Path

from app.common.exception.handlers import BusinessException
from app.common.exception.error_code import ErrorCode
from app.modules.resume.models import ResumeEntity, ResumeStatus
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.schemas import ResumeDetail, ResumeListItem, ResumeResponse
from app.modules.resume.parser import parse_file
from app.modules.resume.analyzer import analyze_resume
from app.infrastructure.cache import cache_get, cache_set, invalidate_user_cache

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {".pdf": "pdf", ".docx": "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024
UPLOAD_DIR = Path("./uploads/resumes")


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

        return self._to_response(created)

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
