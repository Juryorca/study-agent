from sqlalchemy import String, Text, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, OwnerMixin, gen_uuid


class AnswerRecord(Base, TimestampMixin, OwnerMixin):
    __tablename__ = "answer_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    question_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    course_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    student_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, default=1.0)
    feedback: Mapped[str] = mapped_column(Text, default="")
    knowledge_point: Mapped[str] = mapped_column(String(300), default="")
