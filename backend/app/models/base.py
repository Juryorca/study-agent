import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def gen_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class OwnerMixin:
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)


class CourseMixin:
    course_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
