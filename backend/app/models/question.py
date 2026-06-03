from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, CourseMixin, gen_uuid


class Question(Base, TimestampMixin, CourseMixin):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    knowledge_point_id: Mapped[str] = mapped_column(String(36), default="")
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)  # single_choice, short_answer, true_false
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    knowledge_point: Mapped[str] = mapped_column(String(300), default="")
    source: Mapped[str] = mapped_column(String(500), default="")
