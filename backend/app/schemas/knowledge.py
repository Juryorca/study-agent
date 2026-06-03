from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgePointCreate(BaseModel):
    name: str
    description: str = ""
    importance: str = "medium"
    source: str = ""
    document_id: str = ""
    chapter: str = ""


class KnowledgePointRead(BaseModel):
    id: str
    course_id: str
    chapter: str = ""
    name: str
    description: str
    importance: str
    mastery: str = "unlearned"
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MasteryUpdateRequest(BaseModel):
    mastery: str = Field(..., pattern="^(unlearned|learning|mastered)$")


class KnowledgePointList(BaseModel):
    knowledge_points: list[KnowledgePointRead]
    total: int


class ExtractRequest(BaseModel):
    document_id: str


class ReviewOutlineRequest(BaseModel):
    chapter: str = ""


class ReviewOutlineResponse(BaseModel):
    outline: str
    course_id: str
    chapter: str
