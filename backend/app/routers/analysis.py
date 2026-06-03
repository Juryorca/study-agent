from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.answer_record import AnswerRecord
from app.models.weakness_report import WeaknessReport
from app.schemas.agent import WeaknessPoint, WeaknessReportResponse
from app.services.weakness_diagnosis import diagnose_weaknesses
from app.services.study_planning import create_study_plan

router = APIRouter()


@router.post("/weakness/{course_id}", response_model=WeaknessReportResponse)
async def analyze_weakness(
    course_id: str,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    # Query answer records
    result = await db.execute(
        select(AnswerRecord)
        .where(AnswerRecord.course_id == course_id)
        .where(AnswerRecord.user_id == user_id)
        .order_by(AnswerRecord.created_at.desc())
        .limit(200)
    )
    records = result.scalars().all()

    if not records:
        return WeaknessReportResponse(
            course_id=course_id,
            user_id=user_id,
            weak_points=[],
            report_text="暂无答题记录，无法分析薄弱点。",
            study_plan="",
        )

    records_data = [
        {"knowledge_point": r.knowledge_point or "未知知识点", "is_correct": r.is_correct}
        for r in records
    ]
    all_kps = list(set(r.get("knowledge_point", "") for r in records_data))

    diagnosis = await diagnose_weaknesses(records_data, all_kps)

    weak_point_dicts = [
        {
            "knowledge_point": w.knowledge_point,
            "total_attempts": w.total_attempts,
            "wrong_count": w.wrong_count,
            "error_rate": w.error_rate,
            "suggestion": w.suggestion,
        }
        for w in diagnosis.weak_points
    ]

    # Generate study plan
    study_plan = await create_study_plan(weak_point_dicts)

    # Save report
    report = WeaknessReport(
        user_id=user_id,
        course_id=course_id,
        weak_points=weak_point_dicts,
        report_text=diagnosis.overall_summary,
        study_plan=study_plan,
    )
    db.add(report)
    await db.commit()

    weak_points_schema = [
        WeaknessPoint(
            knowledge_point=w["knowledge_point"],
            total_attempts=w["total_attempts"],
            wrong_count=w["wrong_count"],
            error_rate=w["error_rate"],
            suggestion=w["suggestion"],
        )
        for w in weak_point_dicts
    ]

    return WeaknessReportResponse(
        course_id=course_id,
        user_id=user_id,
        weak_points=weak_points_schema,
        report_text=diagnosis.overall_summary,
        study_plan=study_plan,
    )


@router.get("/reports")
async def list_reports(
    course_id: str = "",
    user_id: str = "default",
    db: AsyncSession = Depends(get_db),
):
    query = select(WeaknessReport).order_by(WeaknessReport.created_at.desc())
    if course_id:
        query = query.where(WeaknessReport.course_id == course_id)
    query = query.where(WeaknessReport.user_id == user_id)
    result = await db.execute(query)
    reports = result.scalars().all()
    return {"reports": reports, "total": len(reports)}
