from pydantic import BaseModel
from datetime import datetime
from typing import Any


class CreateInterviewRequest(BaseModel):
    resume_id: str | None = None
    direction: str = "frontend"
    interview_type: str = "text"
    total_questions: int = 5
    use_knowledge: bool = False


class AnswerRequest(BaseModel):
    answer: str


class InterviewSessionResponse(BaseModel):
    id: str
    direction: str
    interview_type: str
    status: str
    current_question: int
    total_questions: int
    questions_asked: list[Any]
    answers_given: list[Any]
    report: Any = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class InterviewListItem(BaseModel):
    id: str
    direction: str
    interview_type: str
    status: str
    question_count: int
    created_at: datetime


class NextQuestionResponse(BaseModel):
    question_index: int
    total: int
    question: str
    session_id: str
    is_completed: bool = False


class ReportResponse(BaseModel):
    session_id: str
    direction: str
    total_questions: int
    score: int
    feedback: str
    dimensions: dict[str, int] = {}
    per_question: list[dict] = []
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    created_at: datetime
