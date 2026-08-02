from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import uuid

from app.common.result import Result
from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.common.auth.deps import get_current_user_dev
from app.infrastructure.database import get_db
from app.modules.resume.schemas import ResumeResponse, ResumeListItem, ResumeDetail, UpdateResumeRequest, BatchDeleteRequest
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


@router.post("/batch-delete")
async def batch_delete_resumes(
    req: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[dict]:
    service = ResumeService(db)
    deleted = await service.batch_delete_resumes(str(user_id), req.ids)
    return Result.success({"deleted": deleted})


@router.get("/{resume_id}/duplicate")
async def check_resume_duplicate(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[dict | None]:
    service = ResumeService(db)
    result = await service.get_duplicate(str(user_id), resume_id)
    return Result.success(result)


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


class SavePolishedRequest(BaseModel):
    polished_text: str


@router.post("/{resume_id}/analyze")
async def analyze_resume_quality_endpoint(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[dict]:
    """AI 按面试官手册对简历分层诊断"""
    service = ResumeService(db)
    result = await service.analyze_quality(str(user_id), resume_id)
    return Result.success(result)


@router.post("/{resume_id}/polish")
async def polish_resume_endpoint(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[dict]:
    """AI 润色简历文本"""
    service = ResumeService(db)
    result = await service.polish(str(user_id), resume_id)
    return Result.success(result)


@router.post("/{resume_id}/save-polished")
async def save_polished_resume(
    resume_id: str, req: SavePolishedRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ResumeDetail]:
    """将润色后的简历文本保存回简历"""
    service = ResumeService(db)
    result = await service.save_polished(str(user_id), resume_id, req.polished_text)
    return Result.success(result)


@router.get("/{resume_id}/export")
async def export_resume(
    resume_id: str,
    format: str = Query("txt", pattern="^(txt|docx)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    """导出简历文本（txt 或 docx）"""
    from fastapi.responses import PlainTextResponse, StreamingResponse
    from io import BytesIO

    service = ResumeService(db)
    detail = await service.get_by_id(str(user_id), resume_id)
    text = f"姓名：{detail.name or ''}\n目标岗位：{detail.position or ''}\n\n个人简介：{detail.summary or ''}\n\n技能：{', '.join(detail.skills or [])}\n"
    for x in (detail.experience or []):
        text += f"\n经历：{x.get('title', '')} @ {x.get('company', '')}（{x.get('duration', '')}）\n{x.get('description', '')}\n"
    for x in (detail.education or []):
        text += f"\n教育：{x.get('school', '')} - {x.get('degree', '')}（{x.get('major', '')}, {x.get('year', '')}）\n"
    filename = (detail.name or "resume").replace(" ", "_")
    from urllib.parse import quote
    encoded = quote(filename)
    if format == "docx":
        try:
            from docx import Document
            doc = Document()
            doc.add_heading(f"{detail.name or '简历'}", level=0)
            for line in text.split("\n"):
                doc.add_paragraph(line)
            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)
            return StreamingResponse(
                buf, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}.docx"})
        except ImportError:
            return Result.error(ErrorCode.INTERNAL_ERROR, "docx 支持未安装")
    return PlainTextResponse(
        text, media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}.txt"})
