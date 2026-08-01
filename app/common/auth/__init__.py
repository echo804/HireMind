"""JWT token creation and verification"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config.settings import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a JWT access token for the given user"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SESSION_SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> uuid.UUID | None:
    """Verify JWT token and return user_id, or None if invalid"""
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        return uuid.UUID(user_id)
    except (JWTError, ValueError):
        return None
