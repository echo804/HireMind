from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.infrastructure.database import get_db
from app.modules.interview.schemas import (
    CreateInterviewRequest, AnswerRequest, InterviewSessionResponse,
    InterviewListItem, NextQuestionResponse, ReportResponse,
)
from app.modules.interview.service import InterviewService

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


@router.post("")
async def create_interview(req: CreateInterviewRequest, db: AsyncSession = Depends(get_db)) -> Result[InterviewSessionResponse]:
    service = InterviewService(db)
    result = await service.create(req)
    return Result.success(result)


@router.post("/{session_id}/answer")
async def answer_question(session_id: str, req: AnswerRequest, db: AsyncSession = Depends(get_db)) -> Result[NextQuestionResponse]:
    service = InterviewService(db)
    result = await service.answer(session_id, req)
    return Result.success(result)


@router.post("/{session_id}/end")
async def end_interview(session_id: str, db: AsyncSession = Depends(get_db)) -> Result[InterviewSessionResponse]:
    service = InterviewService(db)
    result = await service.end_session(session_id)
    return Result.success(result)


@router.delete("/{session_id}")
async def delete_interview(session_id: str, db: AsyncSession = Depends(get_db)) -> Result[None]:
    service = InterviewService(db)
    await service.delete_session(session_id)
    return Result.success(None)


from pydantic import BaseModel

class BatchDeleteRequest(BaseModel):
    ids: list[str]


@router.post("/batch-delete")
async def batch_delete_interviews(req: BatchDeleteRequest, db: AsyncSession = Depends(get_db)) -> Result[None]:
    service = InterviewService(db)
    await service.batch_delete(req.ids)
    return Result.success(None)
async def end_interview(session_id: str, db: AsyncSession = Depends(get_db)) -> Result[InterviewSessionResponse]:
    service = InterviewService(db)
    result = await service.end_session(session_id)
    return Result.success(result)


@router.get("")
async def list_interviews(db: AsyncSession = Depends(get_db)) -> Result[list[InterviewListItem]]:
    service = InterviewService(db)
    result = await service.list_sessions()
    return Result.success(result)


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)) -> Result[InterviewSessionResponse]:
    service = InterviewService(db)
    result = await service.get_session(session_id)
    return Result.success(result)


@router.get("/{session_id}/report")
async def get_report(session_id: str, db: AsyncSession = Depends(get_db)) -> Result[ReportResponse]:
    service = InterviewService(db)
    result = await service.get_report(session_id)
    return Result.success(result)
