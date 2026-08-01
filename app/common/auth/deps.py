"""FastAPI dependencies for auth"""
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth import verify_token
from app.infrastructure.database import get_db
from app.modules.auth.models import UserEntity
from app.modules.auth.repository import UserRepository

security = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserEntity | None:
    """Return current user if token provided, else None (for public endpoints)"""
    if not credentials:
        return None
    user_id = verify_token(credentials.credentials)
    if not user_id:
        return None
    repo = UserRepository(db)
    return await repo.find_by_id(user_id)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserEntity:
    """Require authentication, return current user or raise 401"""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    repo = UserRepository(db)
    user = await repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# DEV mode fallback: if no token, use a fixed dev user
DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


async def get_current_user_dev(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    """Return user_id from JWT, or fall back to DEV_USER_ID in dev mode"""
    if credentials:
        user_id = verify_token(credentials.credentials)
        if user_id:
            repo = UserRepository(db)
            user = await repo.find_by_id(user_id)
            if user:
                return user.id
    return DEV_USER_ID
