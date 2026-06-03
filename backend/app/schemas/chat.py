from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    course_id: str = ""
    title: str = "新对话"


class ChatSessionRead(BaseModel):
    id: str
    course_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ChatSessionList(BaseModel):
    sessions: list[ChatSessionRead]
    total: int


class ChatMessageRead(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    tool_name: str
    tool_args: Any = {}
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatMessageList(BaseModel):
    messages: list[ChatMessageRead]
    total: int
