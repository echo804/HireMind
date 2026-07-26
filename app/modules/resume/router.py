from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.infrastructure.database import get_db
from app.modules.resume.schemas import ResumeResponse, ResumeListItem
from app.modules.resume.service import ResumeService

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

# For now, use a fixed user ID for development
DEV_USER_ID = "00000000-0000-0000-0000-000000000000"


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> Result[ResumeResponse]:
    service = ResumeService(db)
    content = await file.read()
    result = await service.upload(DEV_USER_ID, content, file.filename or "resume")
    return Result.success(result)


@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)) -> Result[list[ResumeListItem]]:
    service = ResumeService(db)
    result = await service.list_resumes(DEV_USER_ID)
    return Result.success(result)


@router.get("/{resume_id}")
async def get_resume(resume_id: str, db: AsyncSession = Depends(get_db)) -> Result[ResumeResponse]:
    service = ResumeService(db)
    result = await service.get_resume(resume_id, DEV_USER_ID)
    return Result.success(result)


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str, db: AsyncSession = Depends(get_db)) -> Result[None]:
    service = ResumeService(db)
    await service.delete_resume(resume_id, DEV_USER_ID)
    return Result.success(None)
