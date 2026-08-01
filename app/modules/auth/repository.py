"""Auth data access"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import UserEntity


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_email(self, email: str) -> UserEntity | None:
        result = await self.db.execute(select(UserEntity).where(UserEntity.email == email))
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: str | uuid.UUID) -> UserEntity | None:
        result = await self.db.execute(select(UserEntity).where(UserEntity.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, user: UserEntity) -> UserEntity:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
