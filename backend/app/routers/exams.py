from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.answer_record import AnswerRecord
from app.models.exam import ExamPaper, ExamQuestion
from app.models.question import Question
from app.schemas.exam import (
    AnswerSave,
    ExamPaperCreate,
    ExamPaperDetail,
    ExamPaperList,
    ExamPaperRead,
    ExamQuestionRead,
)

router = APIRouter()


def _build_paper_and_questions(paper: ExamPaper, eqs: list[ExamQuestion]) -> ExamPaperDetail:
    return ExamPaperDetail(
        paper=ExamPaperRead.model_validate(paper),
        questions=[ExamQuestionRead.model_validate(eq) for eq in eqs],
    )


@router.post("/generate", response_model=ExamPaperDetail)
async def generate_exam(
    req: ExamPaperCreate,
    course_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    cfg = req.config

    # Gather knowledge points for this course
    from app.services.question_generation import generate_exam_questions
    from app.models.knowledge_point import KnowledgePoint

    kp_result = await db.execute(
        select(KnowledgePoint.name).where(KnowledgePoint.course_id == course_id)
    )
    knowledge_point_names = list(set(kp_result.scalars().all()))

    # Always generate fresh questions via LLM
    gen = await generate_exam_questions(
        knowledge_points=knowledge_point_names,
        choice_count=cfg.choice_count,
        short_answer_count=cfg.short_answer_count,
        difficulty_distribution=cfg.difficulty_distribution,
    )

    # Collect all generated questions
    all_items: list[tuple] = []  # (QuestionItem, max_score)
    for qi in gen.choice_questions:
        all_items.append((qi, 2.0))  # 2 points per choice
    for qi in gen.short_answer_questions:
        all_items.append((qi, 10.0))  # 10 points per short answer
    for qi in gen.true_false_questions:
        all_items.append((qi, 2.0))

    if not all_items:
        raise HTTPException(500, "题目生成失败，请重试")

    # Create paper
    paper = ExamPaper(
        course_id=course_id,
        title=req.title,
        config=req.config.model_dump(),
        status="in_progress",
    )
    db.add(paper)
    await db.flush()

    # Save to questions bank + create exam questions
    for i, (qi, max_score) in enumerate(all_items):
        q = Question(
            course_id=course_id,
            question_type=qi.question_type,
            stem=qi.stem,
            options=qi.options or {},
            answer=qi.answer,
            explanation=qi.explanation,
            difficulty=qi.difficulty,
            knowledge_point=qi.knowledge_point,
        )
        db.add(q)
        await db.flush()

        eq = ExamQuestion(
            paper_id=paper.id,
            question_id=q.id,
            question_type=qi.question_type,
            stem=qi.stem,
            options=qi.options or {},
            correct_answer=qi.answer,
            explanation=qi.explanation,
            max_score=max_score,
            order=i,
        )
        db.add(eq)

    await db.commit()

    # Re-fetch after commit to avoid greenlet expiration issues
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == paper.id))
    paper = paper_result.scalar_one()
    eq_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.paper_id == paper.id).order_by(ExamQuestion.order)
    )
    return _build_paper_and_questions(paper, eq_result.scalars().all())


@router.get("", response_model=ExamPaperList)
async def list_exams(
    course_id: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
):
    query = select(ExamPaper).order_by(ExamPaper.updated_at.desc())
    if course_id:
        query = query.where(ExamPaper.course_id == course_id)
    if status:
        query = query.where(ExamPaper.status == status)
    result = await db.execute(query)
    papers = result.scalars().all()
    return ExamPaperList(papers=papers, total=len(papers))


@router.get("/{exam_id}", response_model=ExamPaperDetail)
async def get_exam(exam_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(404, "试卷不存在")
    eq_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.paper_id == exam_id).order_by(ExamQuestion.order)
    )
    return _build_paper_and_questions(paper, eq_result.scalars().all())


@router.put("/{exam_id}/answer")
async def save_answer(exam_id: str, req: AnswerSave, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.paper_id == exam_id, ExamQuestion.id == req.question_id)
    )
    eq = result.scalar_one_or_none()
    if not eq:
        raise HTTPException(404, "题目不存在")
    eq.student_answer = req.student_answer
    # If submitting, set to in_progress if was draft
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    paper = paper_result.scalar_one_or_none()
    if paper and paper.status == "draft":
        paper.status = "in_progress"
    await db.commit()
    return {"message": "已保存"}


@router.post("/{exam_id}/save")
async def save_draft(exam_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(404, "试卷不存在")
    paper.status = "draft"
    await db.commit()
    return {"message": "草稿已保存"}


@router.post("/{exam_id}/submit", response_model=ExamPaperDetail)
async def submit_exam(exam_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(404, "试卷不存在")

    eq_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.paper_id == exam_id).order_by(ExamQuestion.order)
    )
    eqs = eq_result.scalars().all()

    from app.services.answer_evaluation import evaluate_short_answer

    total_earned = 0.0
    for eq in eqs:
        if not eq.student_answer:
            continue
        if eq.question_type == "single_choice":
            eq.is_correct = eq.student_answer.strip().upper() == eq.correct_answer.strip().upper()
            eq.score = eq.max_score if eq.is_correct else 0.0
            eq.feedback = "正确" if eq.is_correct else f"错误，正确答案是 {eq.correct_answer}"
        elif eq.question_type == "true_false":
            eq.is_correct = eq.student_answer.strip().upper() == eq.correct_answer.strip().upper()
            eq.score = eq.max_score if eq.is_correct else 0.0
            eq.feedback = "正确" if eq.is_correct else f"错误，正确答案是 {eq.correct_answer}。{eq.explanation}"
        else:
            evaluation = await evaluate_short_answer(eq.stem, eq.correct_answer, eq.student_answer, eq.max_score)
            eq.score = evaluation.score
            eq.is_correct = evaluation.score >= eq.max_score * 0.6
            eq.feedback = evaluation.feedback

        total_earned += eq.score

        # Record in answer_records
        db.add(AnswerRecord(
            user_id="default",
            question_id=eq.question_id,
            course_id=paper.course_id,
            student_answer=eq.student_answer,
            is_correct=eq.is_correct,
            score=eq.score,
            max_score=eq.max_score,
            feedback=eq.feedback,
        ))

    paper.earned_score = total_earned
    paper.total_score = sum(eq.max_score for eq in eqs)
    paper.status = "graded"
    await db.commit()

    # Re-fetch after commit to avoid greenlet expiration issues
    paper_result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    paper = paper_result.scalar_one()
    eq_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.paper_id == exam_id).order_by(ExamQuestion.order)
    )
    eqs = eq_result.scalars().all()
    return _build_paper_and_questions(paper, eqs)


@router.delete("/{exam_id}")
async def delete_exam(exam_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(ExamQuestion).where(ExamQuestion.paper_id == exam_id))
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == exam_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(404, "试卷不存在")
    await db.delete(paper)
    await db.commit()
    return {"message": "已删除"}
