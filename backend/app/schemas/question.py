from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class QuestionGenerateRequest(BaseModel):
    knowledge_point: str = ""
    question_type: str = "single_choice"  # single_choice, short_answer
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str = "medium"


class QuestionRead(BaseModel):
    id: str
    course_id: str
    knowledge_point_id: str
    knowledge_point: str
    question_type: str
    stem: str
    options: dict
    answer: str
    explanation: str
    difficulty: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionList(BaseModel):
    questions: list[QuestionRead]
    total: int
