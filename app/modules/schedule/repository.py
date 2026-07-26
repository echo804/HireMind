from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.schedule.models import ScheduleEvent


class ScheduleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event: ScheduleEvent) -> ScheduleEvent:
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def find_by_id(self, id) -> ScheduleEvent | None:
        r = await self.db.execute(select(ScheduleEvent).where(ScheduleEvent.id == id))
        return r.scalar_one_or_none()

    async def find_by_date(self, user_id, date: datetime) -> list[ScheduleEvent]:
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        r = await self.db.execute(
            select(ScheduleEvent).where(ScheduleEvent.user_id == user_id,
                                        ScheduleEvent.scheduled_at >= start,
                                        ScheduleEvent.scheduled_at <= end)
            .order_by(ScheduleEvent.scheduled_at)
        )
        return r.scalars().all()

    async def find_range(self, user_id, start: datetime, end: datetime) -> list[ScheduleEvent]:
        r = await self.db.execute(
            select(ScheduleEvent).where(ScheduleEvent.user_id == user_id,
                                        ScheduleEvent.scheduled_at >= start,
                                        ScheduleEvent.scheduled_at <= end)
            .order_by(ScheduleEvent.scheduled_at)
        )
        return r.scalars().all()

    async def save(self, event: ScheduleEvent):
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def delete(self, event: ScheduleEvent):
        await self.db.delete(event)
        await self.db.commit()
