import uuid, logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.modules.schedule.models import ScheduleEvent, ScheduleStatus, ScheduleType
from app.modules.schedule.repository import ScheduleRepository
from app.modules.schedule.schemas import CreateScheduleRequest, UpdateScheduleRequest, ScheduleResponse

logger = logging.getLogger(__name__)


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.repo = ScheduleRepository(db)

    async def _check_conflict(self, user_id: uuid.UUID, scheduled_at: datetime,
                              duration_minutes: int, exclude_id: uuid.UUID | None = None):
        new_end = scheduled_at + timedelta(minutes=duration_minutes)
        events = await self.repo.find_by_date(user_id, scheduled_at)
        for e in events:
            if exclude_id and e.id == exclude_id:
                continue
            if e.status == ScheduleStatus.CANCELLED:
                continue
            e_end = e.scheduled_at + timedelta(minutes=e.duration_minutes)
            if scheduled_at < e_end and new_end > e.scheduled_at:
                raise BusinessException(
                    ErrorCode.SCHEDULE_CONFLICT,
                    f"时间冲突：{e.candidate_name} 已安排在 "
                    f"{e.scheduled_at.strftime('%H:%M')}（{e.duration_minutes}分钟）")

    async def create(self, req: CreateScheduleRequest, user_id: str) -> ScheduleResponse:
        scheduled_at = datetime.fromisoformat(req.scheduled_at.replace("Z", "+00:00"))
        await self._check_conflict(uuid.UUID(user_id), scheduled_at, req.duration_minutes)
        entity = ScheduleEvent(
            user_id=uuid.UUID(user_id),
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

    async def update(self, event_id: str, req: UpdateScheduleRequest, user_id: str) -> ScheduleResponse:
        entity = await self.repo.find_by_id(uuid.UUID(event_id))
        if not entity:
            raise BusinessException(ErrorCode.SCHEDULE_NOT_FOUND)
        if str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.SCHEDULE_NOT_FOUND, "无权修改他人日程")
        if req.candidate_name is not None:
            entity.candidate_name = req.candidate_name
        if req.candidate_email is not None:
            entity.candidate_email = req.candidate_email
        if req.schedule_type is not None:
            entity.schedule_type = ScheduleType(req.schedule_type)
        if req.scheduled_at is not None:
            entity.scheduled_at = datetime.fromisoformat(req.scheduled_at.replace("Z", "+00:00"))
        if req.duration_minutes is not None or req.scheduled_at is not None:
            await self._check_conflict(
                entity.user_id, entity.scheduled_at, entity.duration_minutes,
                exclude_id=uuid.UUID(event_id))
        if req.duration_minutes is not None:
            entity.duration_minutes = req.duration_minutes
        if req.notes is not None:
            entity.notes = req.notes
        if req.status is not None:
            entity.status = ScheduleStatus(req.status)
        await self.repo.save(entity)
        return self._to_response(entity)

    async def get_by_date(self, date_str: str, user_id: str) -> list[ScheduleResponse]:
        date = datetime.fromisoformat(date_str[:10])
        events = await self.repo.find_by_date(uuid.UUID(user_id), date)
        return [self._to_response(e) for e in events]

    async def get_range(self, start_str: str, end_str: str, user_id: str) -> list[ScheduleResponse]:
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        events = await self.repo.find_range(uuid.UUID(user_id), start, end)
        return [self._to_response(e) for e in events]

    async def delete(self, event_id: str, user_id: str):
        entity = await self.repo.find_by_id(uuid.UUID(event_id))
        if not entity:
            raise BusinessException(ErrorCode.SCHEDULE_NOT_FOUND)
        if str(entity.user_id) != user_id:
            raise BusinessException(ErrorCode.SCHEDULE_NOT_FOUND, "无权删除他人日程")
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
