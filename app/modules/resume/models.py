import uuid
from enum import StrEnum as _StrEnum
from sqlalchemy import String, Integer, Text, Enum, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.common.model.base import BaseModel


class ResumeStatus(_StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


class ResumeEntity(BaseModel):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)

    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    position: Mapped[str | None] = mapped_column(String(200), nullable=True)
    skills: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    experience: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    education: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[ResumeStatus] = mapped_column(Enum(ResumeStatus), default=ResumeStatus.PENDING)
