from fastapi import APIRouter, Depends
import uuid

from app.common.result import Result
from app.common.auth.deps import get_current_user_dev
from app.modules.settings.service import get_settings, update_settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("")
async def get_ai_settings(
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[dict]:
    return Result.success(get_settings(str(user_id)))


@router.put("")
async def save_ai_settings(
    data: dict,
    user_id: uuid.UUID = Depends(get_current_user_dev),
) -> Result[dict]:
    result = update_settings(data, str(user_id))
    return Result.success(result)
