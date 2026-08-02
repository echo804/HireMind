import uuid
from enum import StrEnum
from datetime import datetime
from sqlalchemy import String, Integer, Text, Enum, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.common.model.base import BaseModel


class InterviewStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InterviewType(StrEnum):
    TEXT = "text"
    VOICE = "voice"


class InterviewSession(BaseModel):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    direction: Mapped[str] = mapped_column(String(100), nullable=False, comment="e.g. frontend, java, python")
    interview_type: Mapped[InterviewType] = mapped_column(Enum(InterviewType), default=InterviewType.TEXT)
    status: Mapped[InterviewStatus] = mapped_column(Enum(InterviewStatus), default=InterviewStatus.PENDING)
    current_question: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=10)
    questions_asked: Mapped[list] = mapped_column(JSONB, default=list)
    answers_given: Mapped[list] = mapped_column(JSONB, default=list)
    use_knowledge: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None, comment="easy/normal/hard")
    interview_style: Mapped[str | None] = mapped_column(String(20), nullable=True, default=None, comment="strict/warm/coaching")
    report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
