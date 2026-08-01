"""Auth routes"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.result import Result
from app.infrastructure.database import get_db
from app.modules.auth.schemas import AuthResponse, LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register")
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)) -> Result[AuthResponse]:
    service = AuthService(db)
    result = await service.register(request)
    return Result.success(result)


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)) -> Result[AuthResponse]:
    service = AuthService(db)
    result = await service.login(request)
    return Result.success(result)
