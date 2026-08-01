from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.common.result import Result
from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.common.auth.deps import get_current_user_dev
from app.infrastructure.database import get_db
from app.modules.resume.schemas import ResumeResponse, ResumeListItem, ResumeDetail, UpdateResumeRequest
from app.modules.resume.service import ResumeService

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ResumeResponse]:
    service = ResumeService(db)
    content = await file.read()
    result = await service.upload(str(user_id), content, file.filename or "resume")
    return Result.success(result)


@router.get("")
async def list_resumes(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
    q: str | None = Query(None, description="搜索关键词（姓名/职位/摘要）"),
) -> Result[list[ResumeListItem]]:
    service = ResumeService(db)
    result = await service.list_resumes(str(user_id), query=q)
    return Result.success(result)


@router.get("/{resume_id}")
async def get_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ResumeDetail]:
    service = ResumeService(db)
    result = await service.get_by_id(str(user_id), resume_id)
    return Result.success(result)


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[None]:
    service = ResumeService(db)
    await service.delete_resume(str(user_id), resume_id)
    return Result.success(None)


@router.put("/{resume_id}")
async def update_resume(
    resume_id: str, req: UpdateResumeRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ResumeDetail]:
    """简历人工校正：更新解析结果字段"""
    service = ResumeService(db)
    result = await service.update_resume(str(user_id), resume_id, req)
    return Result.success(result)
