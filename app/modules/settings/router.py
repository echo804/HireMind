from fastapi import APIRouter

from app.common.result import Result
from app.modules.settings.service import get_settings, update_settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("")
async def get_ai_settings() -> Result[dict]:
    return Result.success(get_settings())


@router.put("")
async def save_ai_settings(data: dict) -> Result[dict]:
    result = update_settings(data)
    return Result.success(result)
