from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.question import Question
from app.schemas.question import QuestionGenerateRequest, QuestionList, QuestionRead
from app.services.question_generation import generate_questions
from app.services.rag import retrieve_chunks

router = APIRouter()


@router.post("/generate", response_model=QuestionList)
async def generate_questions_api(
    req: QuestionGenerateRequest,
    course_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    query = req.knowledge_point or "核心知识点"
    chunks = await retrieve_chunks(course_id, query, top_k=10)
    if not chunks:
        return QuestionList(questions=[], total=0)

    items = await generate_questions(
        chunks,
        knowledge_point=req.knowledge_point,
        question_type=req.question_type,
        count=req.count,
        difficulty=req.difficulty,
    )

    saved = []
    for item in items:
        q = Question(
            course_id=course_id,
            knowledge_point_id="",
            knowledge_point=item.knowledge_point,
            question_type=item.question_type,
            stem=item.stem,
            options=item.options,
            answer=item.answer,
            explanation=item.explanation,
            difficulty=item.difficulty,
            source="",
        )
        db.add(q)
        await db.flush()
        saved.append(q)

    await db.commit()
    return QuestionList(questions=saved, total=len(saved))


@router.get("", response_model=QuestionList)
async def list_questions(
    course_id: str = "",
    knowledge_point: str = "",
    difficulty: str = "",
    question_type: str = "",
    db: AsyncSession = Depends(get_db),
):
    query = select(Question).order_by(Question.created_at.desc())
    if course_id:
        query = query.where(Question.course_id == course_id)
    if knowledge_point:
        query = query.where(Question.knowledge_point.contains(knowledge_point))
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if question_type:
        query = query.where(Question.question_type == question_type)
    result = await db.execute(query)
    questions = result.scalars().all()
    return QuestionList(questions=questions, total=len(questions))


@router.delete("/{question_id}")
async def delete_question(question_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="题目不存在")
    await db.delete(q)
    await db.commit()
    return {"message": "已删除"}
