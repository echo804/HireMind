"""Knowledge base Pydantic schemas"""
from pydantic import BaseModel
from typing import Optional


class KnowledgeDocResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = 3


class KnowledgeSearchResult(BaseModel):
    content: str
    document_name: str
    score: float
    chunk_index: int