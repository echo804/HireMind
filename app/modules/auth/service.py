"""Auth business logic"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exception.error_code import ErrorCode
from app.common.exception.handlers import BusinessException
from app.modules.auth.models import UserEntity
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import AuthResponse, LoginRequest, RegisterRequest

try:
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    pwd = None
    import hashlib


class AuthService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def register(self, request: RegisterRequest) -> AuthResponse:
        existing = await self.repo.find_by_email(request.email)
        if existing:
            raise BusinessException(ErrorCode.BAD_REQUEST, "Email already registered")
        password_hash = self._hash_password(request.password)
        user = UserEntity(email=request.email, password_hash=password_hash, nickname=request.nickname)
        created = await self.repo.create(user)
        return AuthResponse(id=str(created.id), email=created.email, nickname=created.nickname or "")

    async def login(self, request: LoginRequest) -> AuthResponse:
        user = await self.repo.find_by_email(request.email)
        if not user or not self._verify_password(request.password, user.password_hash):
            raise BusinessException(ErrorCode.UNAUTHORIZED, "Invalid email or password")
        return AuthResponse(id=str(user.id), email=user.email, nickname=user.nickname or "")

    def _hash_password(self, password: str) -> str:
        if pwd:
            return pwd.hash(password)
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, hash: str) -> bool:
        if pwd:
            return pwd.verify(password, hash)
        return hashlib.sha256(password.encode()).hexdigest() == hash
