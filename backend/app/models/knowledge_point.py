from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, CourseMixin, gen_uuid


class KnowledgePoint(Base, TimestampMixin, CourseMixin):
    __tablename__ = "knowledge_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    chapter: Mapped[str] = mapped_column(String(200), default="")
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    importance: Mapped[str] = mapped_column(String(20), default="medium")  # high, medium, low
    mastery: Mapped[str] = mapped_column(String(20), default="unlearned")  # unlearned, learning, mastered
    source: Mapped[str] = mapped_column(String(500), default="")
    document_id: Mapped[str] = mapped_column(String(36), default="")
