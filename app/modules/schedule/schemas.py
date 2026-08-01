from pydantic import BaseModel
from datetime import datetime
from typing import Any


class CreateScheduleRequest(BaseModel):
    candidate_name: str
    candidate_email: str | None = None
    resume_id: str | None = None
    schedule_type: str = "technical"
    scheduled_at: str
    duration_minutes: int = 60
    notes: str | None = None


class UpdateScheduleRequest(BaseModel):
    candidate_name: str | None = None
    candidate_email: str | None = None
    schedule_type: str | None = None
    scheduled_at: str | None = None
    duration_minutes: int | None = None
    notes: str | None = None
    status: str | None = None


class ScheduleResponse(BaseModel):
    id: str
    candidate_name: str
    candidate_email: str | None = None
    resume_id: str | None = None
    schedule_type: str
    status: str
    scheduled_at: datetime
    duration_minutes: int
    notes: str | None = None
    created_at: datetime
