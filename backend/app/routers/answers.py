from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.answer_record import AnswerRecord
from app.models.question import Question
from app.schemas.answer import (
    AnswerBatchResult,
    AnswerBatchSubmit,
    AnswerRecordRead,
    AnswerResult,
    AnswerSubmit,
)
from app.services.answer_evaluation import evaluate_short_answer

router = APIRouter()


@router.post("/submit", response_model=AnswerResult)
async def submit_answer(
    req: AnswerSubmit,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    # Find question
    result = await db.execute(select(Question).where(Question.id == req.question_id))
    question = result.scalar_one_or_none()
    if not question:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="题目不存在")

    # Evaluate
    if question.question_type == "single_choice":
        is_correct = req.student_answer.strip().upper() == question.answer.strip().upper()
        score = 1.0 if is_correct else 0.0
        feedback = "回答正确！" if is_correct else f"回答错误，正确答案是 {question.answer}。{question.explanation}"
    else:
        evaluation = await evaluate_short_answer(
            question_stem=question.stem,
            correct_answer=question.answer,
            student_answer=req.student_answer,
            max_score=10.0,
        )
        is_correct = evaluation.score >= evaluation.max_score * 0.6
        score = evaluation.score
        feedback = evaluation.feedback

    # Save record
    record = AnswerRecord(
        user_id=user_id,
        question_id=req.question_id,
        course_id=question.course_id,
        student_answer=req.student_answer,
        is_correct=is_correct,
        score=score,
        max_score=1.0 if question.question_type == "single_choice" else 10.0,
        feedback=feedback,
        knowledge_point=question.knowledge_point,
    )
    db.add(record)
    await db.commit()

    return AnswerResult(
        question_id=req.question_id,
        is_correct=is_correct,
        score=score,
        max_score=record.max_score,
        correct_answer=question.answer,
        explanation=question.explanation,
        feedback=feedback,
    )


@router.post("/submit-batch", response_model=AnswerBatchResult)
async def submit_batch(
    req: AnswerBatchSubmit,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    results = []
    total_score = 0.0
    max_total = 0.0
    correct_count = 0

    for answer in req.answers:
        # Similar to single submit but inline
        q_result = await db.execute(select(Question).where(Question.id == answer.question_id))
        question = q_result.scalar_one_or_none()
        if not question:
            continue

        if question.question_type == "single_choice":
            is_correct = answer.student_answer.strip().upper() == question.answer.strip().upper()
            score = 1.0 if is_correct else 0.0
            max_score = 1.0
            feedback = "正确" if is_correct else f"错误，正确是{question.answer}"
        else:
            evaluation = await evaluate_short_answer(
                question_stem=question.stem,
                correct_answer=question.answer,
                student_answer=answer.student_answer,
            )
            is_correct = evaluation.score >= 6.0
            score = evaluation.score
            max_score = 10.0
            feedback = evaluation.feedback

        record = AnswerRecord(
            user_id=user_id,
            question_id=answer.question_id,
            course_id=question.course_id,
            student_answer=answer.student_answer,
            is_correct=is_correct,
            score=score,
            max_score=max_score,
            feedback=feedback,
            knowledge_point=question.knowledge_point,
        )
        db.add(record)
        total_score += score
        max_total += max_score
        if is_correct:
            correct_count += 1

        results.append(AnswerResult(
            question_id=answer.question_id,
            is_correct=is_correct,
            score=score,
            max_score=max_score,
            correct_answer=question.answer,
            explanation=question.explanation,
            feedback=feedback,
        ))

    await db.commit()

    return AnswerBatchResult(
        results=results,
        total_score=total_score,
        max_total_score=max_total,
        correct_count=correct_count,
        total_count=len(results),
    )


@router.get("/records")
async def list_records(
    course_id: str = "",
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    query = select(AnswerRecord).order_by(AnswerRecord.created_at.desc())
    if course_id:
        query = query.where(AnswerRecord.course_id == course_id)
    query = query.where(AnswerRecord.user_id == user_id)
    result = await db.execute(query)
    records = result.scalars().all()
    return {"records": records, "total": len(records)}
