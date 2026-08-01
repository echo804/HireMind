import uuid
from enum import StrEnum
from datetime import datetime
from sqlalchemy import String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.common.model.base import BaseModel


class ScheduleStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ScheduleType(StrEnum):
    FIRST = "first"
    TECHNICAL = "technical"
    HR = "hr"


class ScheduleEvent(BaseModel):
    __tablename__ = "schedule_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    candidate_name: Mapped[str] = mapped_column(String(100), nullable=False)
    candidate_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    schedule_type: Mapped[ScheduleType] = mapped_column(Enum(ScheduleType), default=ScheduleType.TECHNICAL)
    status: Mapped[ScheduleStatus] = mapped_column(Enum(ScheduleStatus), default=ScheduleStatus.PENDING)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(default=60)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
