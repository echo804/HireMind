from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.resume.models import ResumeEntity


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entity: ResumeEntity) -> ResumeEntity:
        self.db.add(entity)
        await self.db.commit()
        await self.db.refresh(entity)
        return entity

    async def find_by_id(self, id) -> ResumeEntity | None:
        result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.id == id))
        return result.scalar_one_or_none()

    async def find_by_user(self, user_id) -> list[ResumeEntity]:
        result = await self.db.execute(
            select(ResumeEntity).where(ResumeEntity.user_id == user_id).order_by(ResumeEntity.created_at.desc())
        )
        return result.scalars().all()

    async def search(self, user_id, query: str) -> list[ResumeEntity]:
        pattern = f"%{query}%"
        result = await self.db.execute(
            select(ResumeEntity).where(
                ResumeEntity.user_id == user_id,
                (ResumeEntity.name.ilike(pattern)) |
                (ResumeEntity.position.ilike(pattern)) |
                (ResumeEntity.summary.ilike(pattern))
            ).order_by(ResumeEntity.created_at.desc())
        )
        return result.scalars().all()

    async def find_by_hash(self, content_hash: str) -> ResumeEntity | None:
        result = await self.db.execute(select(ResumeEntity).where(ResumeEntity.content_hash == content_hash))
        return result.scalars().first()

    async def delete(self, entity: ResumeEntity):
        await self.db.delete(entity)
        await self.db.commit()

    async def save(self, entity: ResumeEntity):
        merged = await self.db.merge(entity)
        await self.db.commit()
        await self.db.refresh(merged)
        return merged
