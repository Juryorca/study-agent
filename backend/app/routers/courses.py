from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.course import Course
from app.models.document import Document
from app.schemas.course import CourseCreate, CourseList, CourseRead

router = APIRouter()


@router.post("", response_model=CourseRead)
async def create_course(data: CourseCreate, db: AsyncSession = Depends(get_db)):
    course = Course(
        name=data.name,
        category=data.category,
        description=data.description,
        user_id="default",
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.get("", response_model=CourseList)
async def list_courses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).order_by(Course.created_at.desc()))
    courses = result.scalars().all()
    total = len(courses)
    return CourseList(courses=courses, total=total)


@router.get("/{course_id}", response_model=CourseRead)
async def get_course(course_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.delete("/{course_id}")
async def delete_course(course_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="课程不存在")
    await db.delete(course)
    await db.commit()
    return {"message": "已删除"}
