from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.infrastructure.database import get_db
from app.modules.knowledgebase.schemas import KnowledgeDocResponse, KnowledgeSearchRequest, KnowledgeSearchResult
from app.modules.knowledgebase.service import KnowledgeService

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge Base"])
DEV_USER_ID = "00000000-0000-0000-0000-000000000000"


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> Result[KnowledgeDocResponse]:
    service = KnowledgeService(db)
    content = await file.read()
    result = await service.upload_document(DEV_USER_ID, content, file.filename or "document")
    return Result.success(result)


@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)) -> Result[list[KnowledgeDocResponse]]:
    service = KnowledgeService(db)
    result = await service.list_documents(DEV_USER_ID)
    return Result.success(result)



@router.get("/{doc_id}/content")
async def get_document_content(doc_id: str, db = Depends(get_db)):
    service = KnowledgeService(db)
    result = await service.get_document_content(doc_id, DEV_USER_ID)
    return Result.success(result)

@router.delete("/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)) -> Result[None]:
    service = KnowledgeService(db)
    await service.delete_document(doc_id, DEV_USER_ID)
    return Result.success(None)


@router.post("/search")
async def search_knowledge(req: KnowledgeSearchRequest, db: AsyncSession = Depends(get_db)) -> Result[list[KnowledgeSearchResult]]:
    service = KnowledgeService(db)
    result = await service.search(req.query, req.top_k, DEV_USER_ID)
    return Result.success(result)