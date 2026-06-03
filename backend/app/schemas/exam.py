from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExamConfig(BaseModel):
    choice_count: int = Field(default=20, ge=0, le=50)
    short_answer_count: int = Field(default=5, ge=0, le=20)
    difficulty_distribution: dict[str, float] = Field(
        default={"easy": 0.3, "medium": 0.5, "hard": 0.2}
    )


class ExamPaperCreate(BaseModel):
    title: str = "新试卷"
    config: ExamConfig = Field(default_factory=ExamConfig)


class ExamQuestionRead(BaseModel):
    id: str
    paper_id: str
    question_id: str
    question_type: str
    stem: str
    options: dict
    max_score: float
    order: int
    student_answer: str = ""
    score: float = 0.0
    is_correct: bool = False
    feedback: str = ""
    model_config = {"from_attributes": True}


class ExamPaperRead(BaseModel):
    id: str
    course_id: str
    title: str
    config: dict
    status: str
    total_score: float
    earned_score: float
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ExamPaperDetail(BaseModel):
    paper: ExamPaperRead
    questions: list[ExamQuestionRead]


class ExamPaperList(BaseModel):
    papers: list[ExamPaperRead]
    total: int


class AnswerSave(BaseModel):
    question_id: str
    student_answer: str


class BatchAnswerSave(BaseModel):
    answers: list[AnswerSave]
