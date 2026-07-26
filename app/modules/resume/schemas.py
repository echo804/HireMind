from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ResumeResponse(BaseModel):
    id: str
    filename: str
    file_size: int
    file_type: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    position: str | None = None
    skills: list[Any] | None = None
    experience: list[Any] | None = None
    education: list[Any] | None = None
    summary: str | None = None
    score: int | None = None
    status: str
    created_at: datetime


class ResumeListItem(BaseModel):
    id: str
    filename: str
    name: str | None = None
    position: str | None = None
    score: int | None = None
    status: str
    created_at: datetime
