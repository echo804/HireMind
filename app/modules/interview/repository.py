from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.interview.models import InterviewSession


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: InterviewSession) -> InterviewSession:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def find_by_id(self, id) -> InterviewSession | None:
        r = await self.db.execute(select(InterviewSession).where(InterviewSession.id == id))
        return r.scalar_one_or_none()

    async def find_by_user(self, user_id) -> list[InterviewSession]:
        r = await self.db.execute(
            select(InterviewSession).where(InterviewSession.user_id == user_id).order_by(InterviewSession.created_at.desc())
        )
        return r.scalars().all()

    async def delete(self, session: InterviewSession):
        await self.db.delete(session)
        await self.db.commit()

    async def save(self, session: InterviewSession):
        await self.db.commit()
        await self.db.refresh(session)
        return session
