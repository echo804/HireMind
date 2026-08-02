from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ResumeResponse(BaseModel):
    id: str
    filename: str
    file_size: int | None = None
    file_type: str | None = None
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


class ResumeDetail(BaseModel):
    id: str
    filename: str
    file_size: int | None = None
    file_type: str | None = None
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    position: str | None = None
    skills: list[Any] | None = None
    experience: list[Any] | None = None
    education: list[Any] | None = None
    summary: str | None = None
    score: int | None = None
    progress: int = 0
    status: str
    created_at: str | None = None


class UpdateResumeRequest(BaseModel):
    """简历人工校正：支持部分字段更新"""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    position: str | None = None
    skills: list[str] | None = None
    experience: list[Any] | None = None
    education: list[Any] | None = None
    summary: str | None = None


class BatchDeleteRequest(BaseModel):
    """批量删除简历"""
    ids: list[str]


class UploadResumeResponse(ResumeResponse):
    """上传响应：含去重检测标记"""
    duplicate: bool = False
    duplicate_of: str | None = None
    duplicate_filename: str | None = None
