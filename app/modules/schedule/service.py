import uuid, logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.modules.schedule.models import ScheduleEvent, ScheduleStatus, ScheduleType
from app.modules.schedule.repository import ScheduleRepository
from app.modules.schedule.schemas import CreateScheduleRequest, UpdateScheduleRequest, ScheduleResponse

logger = logging.getLogger(__name__)
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.repo = ScheduleRepository(db)

    async def create(self, req: CreateScheduleRequest) -> ScheduleResponse:
        scheduled_at = datetime.fromisoformat(req.scheduled_at.replace("Z", "+00:00"))
        entity = ScheduleEvent(
            user_id=DEV_USER_ID,
            resume_id=uuid.UUID(req.resume_id) if req.resume_id else None,
            candidate_name=req.candidate_name,
            candidate_email=req.candidate_email,
            schedule_type=ScheduleType(req.schedule_type),
            scheduled_at=scheduled_at,
            duration_minutes=req.duration_minutes,
            notes=req.notes,
        )
        created = await self.repo.create(entity)
        return self._to_response(created)

    async def update(self, event_id: str, req: UpdateScheduleRequest) -> ScheduleResponse:
        entity = await self.repo.find_by_id(uuid.UUID(event_id))
        if not entity:
            raise BusinessException(ErrorCode.SCHEDULE_NOT_FOUND)
        if req.candidate_name is not None:
            entity.candidate_name = req.candidate_name
        if req.candidate_email is not None:
            entity.candidate_email = req.candidate_email
        if req.schedule_type is not None:
            entity.schedule_type = ScheduleType(req.schedule_type)
        if req.scheduled_at is not None:
            entity.scheduled_at = datetime.fromisoformat(req.scheduled_at.replace("Z", "+00:00"))
        if req.duration_minutes is not None:
            entity.duration_minutes = req.duration_minutes
        if req.notes is not None:
            entity.notes = req.notes
        if req.status is not None:
            entity.status = ScheduleStatus(req.status)
        await self.repo.save(entity)
        return self._to_response(entity)

    async def get_by_date(self, date_str: str) -> list[ScheduleResponse]:
        date = datetime.fromisoformat(date_str[:10])
        events = await self.repo.find_by_date(DEV_USER_ID, date)
        return [self._to_response(e) for e in events]

    async def get_range(self, start_str: str, end_str: str) -> list[ScheduleResponse]:
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        events = await self.repo.find_range(DEV_USER_ID, start, end)
        return [self._to_response(e) for e in events]

    async def delete(self, event_id: str):
        entity = await self.repo.find_by_id(uuid.UUID(event_id))
        if not entity:
            raise BusinessException(ErrorCode.SCHEDULE_NOT_FOUND)
        await self.repo.delete(entity)

    def _to_response(self, e: ScheduleEvent) -> ScheduleResponse:
        return ScheduleResponse(
            id=str(e.id), candidate_name=e.candidate_name,
            candidate_email=e.candidate_email,
            resume_id=str(e.resume_id) if e.resume_id else None,
            schedule_type=e.schedule_type.value, status=e.status.value,
            scheduled_at=e.scheduled_at, duration_minutes=e.duration_minutes,
            notes=e.notes, created_at=e.created_at,
        )
