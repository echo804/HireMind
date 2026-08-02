from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import uuid
import logging

logger = logging.getLogger(__name__)

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


class ExportResumeRequest(BaseModel):
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


@router.post("/{resume_id}/export")
async def export_resume(
    resume_id: str, req: ExportResumeRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    """导出 AI 润色后的简历为 .docx（基于原简历模板排版，生成新文件不覆盖原文件）"""
    from fastapi.responses import StreamingResponse
    from io import BytesIO

    service = ResumeService(db)
    detail = await service.get_by_id(str(user_id), resume_id)
    text = (req.polished_text or "").strip()
    if not text:
        return Result.error(ErrorCode.RESUME_NOT_FOUND, "润色内容为空，无法导出")
    original = await service.get_original_path(str(user_id), resume_id)
    filename = (detail.name or "resume").replace(" ", "_") + "_polished"
    from urllib.parse import quote
    encoded = quote(filename)
    try:
        from docx import Document
        from docx.shared import Pt

        original_path, orig_type = (original or (None, None))
        doc = None
        if original_path and orig_type == "docx":
            # 以原 docx 为模板：保留页面设置/样式表，清空正文后重建
            doc = Document(original_path)
            # 删除原正文段落（保留 sectPr 与样式）
            for para in list(doc.paragraphs):
                p = para._element
                p.getparent().remove(p)
        else:
            doc = Document()

        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                doc.add_paragraph()
                continue
            if original_path and orig_type == "pdf":
                # PDF 模板：按行特征推断层级（粗体/标题号）——这里基于润色文本的 markdown 痕迹映射
                if line.startswith("## "):
                    doc.add_heading(line[3:].strip(), level=1)
                elif line.startswith("### "):
                    doc.add_heading(line[4:].strip(), level=2)
                elif line.startswith("# "):
                    doc.add_heading(line[2:].strip(), level=0)
                elif line.startswith("- ") or line.startswith("* "):
                    doc.add_paragraph(line[2:].strip(), style="List Bullet")
                else:
                    doc.add_paragraph(line)
            else:
                # docx 模板或新文档：按 markdown 痕迹映射标题层级
                if line.startswith("## "):
                    doc.add_heading(line[3:].strip(), level=1)
                elif line.startswith("### "):
                    doc.add_heading(line[4:].strip(), level=2)
                elif line.startswith("# "):
                    doc.add_heading(line[2:].strip(), level=0)
                elif line.startswith("- ") or line.startswith("* "):
                    doc.add_paragraph(line[2:].strip(), style="List Bullet")
                else:
                    doc.add_paragraph(line)

        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}.docx"})
    except ImportError:
        return Result.error(ErrorCode.INTERNAL_ERROR, "docx 支持未安装")
    except Exception as e:
        logger.error(f"export_resume failed: {e}")
        return Result.error(ErrorCode.INTERNAL_ERROR, f"导出失败：{str(e)[:100]}")
