from typing import Optional

from pydantic import BaseModel, Field


class WeaknessPoint(BaseModel):
    knowledge_point: str
    total_attempts: int
    wrong_count: int
    error_rate: float
    suggestion: str = ""


class WeaknessReportResponse(BaseModel):
    course_id: str
    user_id: str
    weak_points: list[WeaknessPoint]
    report_text: str
    study_plan: str


class AgentChatRequest(BaseModel):
    message: str
    course_id: str = ""
    session_id: str = ""
    user_id: str = "default"


class AgentChatEvent(BaseModel):
    type: str  # text, tool_call, tool_result, done, error
    content: str = ""
    tool_name: str = ""
    tool_args: dict | None = None
    tool_result: str = ""
