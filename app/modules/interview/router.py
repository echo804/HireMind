from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid, json

from app.common.result import Result
from app.common.auth.deps import get_current_user_dev
from app.infrastructure.database import get_db
from app.modules.interview.schemas import (
    CreateInterviewRequest, AnswerRequest, InterviewSessionResponse,
    InterviewListItem, NextQuestionResponse, ReportResponse,
)
from app.modules.interview.service import InterviewService
from pydantic import BaseModel

router = APIRouter(prefix="/api/interviews", tags=["Interviews"])


class BatchDeleteRequest(BaseModel):
    ids: list[str]


@router.post("")
async def create_interview(
    req: CreateInterviewRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[InterviewSessionResponse]:
    service = InterviewService(db)
    result = await service.create(req, str(user_id))
    return Result.success(result)


@router.post("/{session_id}/answer")
async def answer_question(
    session_id: str, req: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[NextQuestionResponse]:
    service = InterviewService(db)
    result = await service.answer(session_id, req)
    return Result.success(result)


@router.post("/{session_id}/end")
async def end_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[InterviewSessionResponse]:
    service = InterviewService(db)
    result = await service.end_session(session_id)
    return Result.success(result)


@router.post("/{session_id}/skip")
async def skip_interview_question(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    """跳过当前题，流式生成下一题"""
    async def event_stream():
        service = InterviewService(db)
        async for chunk in service.skip_question(session_id):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{session_id}/hint")
async def hint_interview_question(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    """给当前题生成答题提示（流式）"""
    async def event_stream():
        service = InterviewService(db)
        async for chunk in service.hint_question(session_id):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{session_id}/polish")
async def polish_interview_answer(
    session_id: str, req: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    """润色候选人回答"""
    async def event_stream():
        service = InterviewService(db)
        async for chunk in service.polish_answer(session_id, req.answer):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.delete("/{session_id}")
async def delete_interview(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[None]:
    service = InterviewService(db)
    await service.delete_session(session_id)
    return Result.success(None)


@router.post("/batch-delete")
async def batch_delete_interviews(
    req: BatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[None]:
    service = InterviewService(db)
    await service.batch_delete(req.ids)
    return Result.success(None)


@router.post("/{session_id}/answer-stream")
async def answer_question_stream(
    session_id: str, req: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
):
    """SSE 流式回答问题，逐 token 推送 AI 生成的问题"""
    async def event_stream():
        service = InterviewService(db)
        async for chunk in service.answer_stream(session_id, req):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("")
async def list_interviews(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[list[InterviewListItem]]:
    service = InterviewService(db)
    result = await service.list_sessions(str(user_id))
    return Result.success(result)


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[InterviewSessionResponse]:
    service = InterviewService(db)
    result = await service.get_session(session_id)
    return Result.success(result)


@router.get("/{session_id}/report")
async def get_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ReportResponse]:
    service = InterviewService(db)
    result = await service.get_report(session_id)
    return Result.success(result)


@router.post("/{session_id}/re-evaluate")
async def re_evaluate_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ReportResponse]:
    """重新生成评估报告（AI 失败后可重跑）"""
    service = InterviewService(db)
    result = await service.re_evaluate(session_id)
    return Result.success(result)


@router.get("/{session_id}/export-pdf")
async def export_report_pdf(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Response:
    service = InterviewService(db)
    pdf_bytes = await service.export_pdf(session_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=interview-report-{session_id[:8]}.pdf"},
    )
