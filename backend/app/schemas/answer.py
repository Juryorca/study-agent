from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnswerSubmit(BaseModel):
    question_id: str
    student_answer: str


class AnswerBatchSubmit(BaseModel):
    answers: list[AnswerSubmit]


class AnswerResult(BaseModel):
    question_id: str
    is_correct: bool
    score: float
    max_score: float
    correct_answer: str
    explanation: str
    feedback: str


class AnswerBatchResult(BaseModel):
    results: list[AnswerResult]
    total_score: float
    max_total_score: float
    correct_count: int
    total_count: int


class AnswerRecordRead(BaseModel):
    id: str
    user_id: str
    question_id: str
    course_id: str
    student_answer: str
    is_correct: bool
    score: float
    max_score: float
    feedback: str
    knowledge_point: str
    created_at: datetime

    model_config = {"from_attributes": True}
