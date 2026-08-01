from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.common.result import Result
from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.common.auth.deps import get_current_user_dev
from app.infrastructure.database import get_db
from app.modules.knowledgebase.schemas import KnowledgeDocResponse, KnowledgeSearchRequest, KnowledgeSearchResult
from app.modules.knowledgebase.service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[KnowledgeDocResponse]:
    service = KnowledgeService(db)
    content = await file.read()
    result = await service.upload_document(str(user_id), content, file.filename or "document")
    return Result.success(result)


@router.get("")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[list[KnowledgeDocResponse]]:
    service = KnowledgeService(db)
    result = await service.list_documents(str(user_id))
    return Result.success(result)


@router.get("/{doc_id}/status")
async def get_document_status(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    service = KnowledgeService(db)
    result = await service.get_document_status(doc_id, str(user_id))
    return Result.success(result)


@router.post("/{doc_id}/retry")
async def retry_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    service = KnowledgeService(db)
    result = await service.retry_document(doc_id, str(user_id))
    return Result.success(result)


@router.get("/{doc_id}/content")
async def get_document_content(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    service = KnowledgeService(db)
    result = await service.get_document_content(doc_id, str(user_id))
    return Result.success(result)


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[None]:
    service = KnowledgeService(db)
    await service.delete_document(doc_id, str(user_id))
    return Result.success(None)


@router.post("/search")
async def search_knowledge(
    req: KnowledgeSearchRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[list[KnowledgeSearchResult]]:
    service = KnowledgeService(db)
    result = await service.search(req.query, req.top_k, str(user_id))
    return Result.success(result)