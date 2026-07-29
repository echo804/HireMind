import uuid, hashlib, os, logging
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.modules.resume.models import ResumeEntity, ResumeStatus
from app.modules.resume.repository import ResumeRepository
from app.modules.resume.schemas import ResumeResponse, ResumeListItem
from app.modules.resume.parser import parse_file
from app.modules.resume.analyzer import analyze_resume

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("./uploads/resumes")
ALLOWED_TYPES = {".pdf": "pdf", ".docx": "docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class ResumeService:
    def __init__(self, db: AsyncSession):
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
            status=ResumeStatus.PENDING,
        )
        created = await self.repo.create(entity)

        # Async parse and analyze in background
        try:
            text, content_hash = parse_file(str(save_path))

            existing = await self.repo.find_by_hash(content_hash)
            if existing:
                created.content_hash = content_hash
                created.status = ResumeStatus.FAILED
                created.summary = "Duplicate resume"
                save_path.unlink(missing_ok=True)
                await self.repo.save(created)
                return self._to_response(created)

            analysis = await analyze_resume(text, user_id=user_id)
            created.name = analysis.get("name")
            created.email = analysis.get("email")
            created.phone = analysis.get("phone")
            created.position = analysis.get("position")
            created.skills = analysis.get("skills", [])
            created.experience = analysis.get("experience", [])
            created.education = analysis.get("education", [])
            created.summary = analysis.get("summary", "")
            created.score = min(max(int(analysis.get("score", 50)), 0), 100)
            created.content_hash = content_hash
            created.status = ResumeStatus.DONE
        except Exception as e:
            logger.error(f"Resume analysis failed: {e}")
            created.status = ResumeStatus.FAILED
            created.summary = f"Analysis failed: {str(e)[:200]}"
            save_path.unlink(missing_ok=True)
            raise

        await self.repo.save(created)
        return self._to_response(created)

    async def list_resumes(self, user_id: str, query: str | None = None) -> list[ResumeListItem]:
        if query:
            entities = await self.repo.search(uuid.UUID(user_id), query)
        else:
            entities = await self.repo.find_by_user(uuid.UUID(user_id))
        return [self._to_list_item(e) for e in entities]

    async def get_resume(self, resume_id: str, user_id: str) -> ResumeResponse:
        entity = await self.repo.find_by_id(uuid.UUID(resume_id))
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND)
        return self._to_response(entity)

    async def delete_resume(self, resume_id: str, user_id: str):
        entity = await self.repo.find_by_id(uuid.UUID(resume_id))
        if not entity or str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.RESUME_NOT_FOUND)
        Path(entity.file_path).unlink(missing_ok=True)
        await self.repo.delete(entity)

    def _to_response(self, e: ResumeEntity) -> ResumeResponse:
        return ResumeResponse(
            id=str(e.id), filename=e.filename, file_size=e.file_size,
            file_type=e.file_type, name=e.name, email=e.email, phone=e.phone,
            position=e.position, skills=e.skills, experience=e.experience,
            education=e.education, summary=e.summary, score=e.score,
            status=e.status.value, created_at=e.created_at,
        )

    def _to_list_item(self, e: ResumeEntity) -> ResumeListItem:
        return ResumeListItem(
            id=str(e.id), filename=e.filename, name=e.name,
            position=e.position, score=e.score, status=e.status.value,
            created_at=e.created_at,
        )
