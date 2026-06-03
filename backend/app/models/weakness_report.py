from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, OwnerMixin, CourseMixin, gen_uuid


class WeaknessReport(Base, TimestampMixin, OwnerMixin, CourseMixin):
    __tablename__ = "weakness_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    weak_points: Mapped[dict] = mapped_column(JSON, default=list)
    report_text: Mapped[str] = mapped_column(Text, default="")
    study_plan: Mapped[str] = mapped_column(Text, default="")
