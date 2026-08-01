from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.common.result import Result
from app.common.auth.deps import get_current_user_dev
from app.infrastructure.database import get_db
from app.modules.schedule.schemas import CreateScheduleRequest, UpdateScheduleRequest, ScheduleResponse
from app.modules.schedule.service import ScheduleService

router = APIRouter(prefix="/api/schedule", tags=["Schedule"])


@router.post("")
async def create_schedule(
    req: CreateScheduleRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ScheduleResponse]:
    service = ScheduleService(db)
    result = await service.create(req, str(user_id))
    return Result.success(result)


@router.put("/{event_id}")
async def update_schedule(
    event_id: str, req: UpdateScheduleRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[ScheduleResponse]:
    service = ScheduleService(db)
    result = await service.update(event_id, req, str(user_id))
    return Result.success(result)


@router.get("/day")
async def get_day(
    date: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[list[ScheduleResponse]]:
    service = ScheduleService(db)
    result = await service.get_by_date(date, str(user_id))
    return Result.success(result)


@router.get("/range")
async def get_range(
    start: str = Query(...), end: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[list[ScheduleResponse]]:
    service = ScheduleService(db)
    result = await service.get_range(start, end, str(user_id))
    return Result.success(result)


@router.delete("/{event_id}")
async def delete_schedule(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[None]:
    service = ScheduleService(db)
    await service.delete(event_id, str(user_id))
    return Result.success(None)
