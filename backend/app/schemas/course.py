from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─── Course ───
class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = ""
    description: str = ""


class CourseRead(BaseModel):
    id: str
    user_id: str
    name: str
    category: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CourseList(BaseModel):
    courses: list[CourseRead]
    total: int
