from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.infrastructure.database import get_db
from app.modules.schedule.schemas import CreateScheduleRequest, UpdateScheduleRequest, ScheduleResponse
from app.modules.schedule.service import ScheduleService

router = APIRouter(prefix="/api/schedule", tags=["Schedule"])


@router.post("")
async def create_schedule(req: CreateScheduleRequest, db: AsyncSession = Depends(get_db)) -> Result[ScheduleResponse]:
    service = ScheduleService(db)
    result = await service.create(req)
    return Result.success(result)


@router.put("/{event_id}")
async def update_schedule(event_id: str, req: UpdateScheduleRequest, db: AsyncSession = Depends(get_db)) -> Result[ScheduleResponse]:
    service = ScheduleService(db)
    result = await service.update(event_id, req)
    return Result.success(result)


@router.get("/day")
async def get_day(date: str = Query(...), db: AsyncSession = Depends(get_db)) -> Result[list[ScheduleResponse]]:
    service = ScheduleService(db)
    result = await service.get_by_date(date)
    return Result.success(result)


@router.get("/range")
async def get_range(start: str = Query(...), end: str = Query(...), db: AsyncSession = Depends(get_db)) -> Result[list[ScheduleResponse]]:
    service = ScheduleService(db)
    result = await service.get_range(start, end)
    return Result.success(result)


@router.delete("/{event_id}")
async def delete_schedule(event_id: str, db: AsyncSession = Depends(get_db)) -> Result[None]:
    service = ScheduleService(db)
    await service.delete(event_id)
    return Result.success(None)
