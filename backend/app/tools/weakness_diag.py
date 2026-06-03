"""Tool: diagnose_weaknesses - analyze student weak points from answer records."""

from app.services.weakness_diagnosis import diagnose_weaknesses
from app.tools.registry import global_registry


async def _diagnose_weaknesses(
    course_id: str,
    user_id: str = "default",
) -> str:
    # Query answer records from DB
    from app.database import async_session
    from app.models.answer_record import AnswerRecord
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(AnswerRecord)
            .where(AnswerRecord.course_id == course_id)
            .where(AnswerRecord.user_id == user_id)
            .order_by(AnswerRecord.created_at.desc())
            .limit(200)
        )
        records = result.scalars().all()

    if not records:
        return f"用户 {user_id} 在课程 {course_id} 中暂无答题记录，无法进行薄弱点分析。请先完成一些练习题。"

    records_data = [
        {
            "knowledge_point": r.knowledge_point or "未知知识点",
            "is_correct": r.is_correct,
        }
        for r in records
    ]

    diagnosis = await diagnose_weaknesses(records_data)

    if not diagnosis.weak_points:
        return f"分析完成：{diagnosis.overall_summary}"

    lines = ["## 薄弱点分析报告\n"]
    for w in diagnosis.weak_points:
        lines.append(
            f"### {w.knowledge_point}\n"
            f"- 答题次数: {w.total_attempts} 次\n"
            f"- 错误次数: {w.wrong_count} 次\n"
            f"- 错误率: {w.error_rate:.1%}\n"
            f"- 建议: {w.suggestion}\n"
        )
    lines.append(f"\n## 整体评价\n{diagnosis.overall_summary}")
    return "\n".join(lines)


global_registry.register(
    name="diagnose_weaknesses",
    description="根据学生的历史答题记录分析薄弱知识点。统计每个知识点的答题次数、正确率和错误率，给出针对性的复习建议。",
    parameters={
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "课程ID",
            },
            "user_id": {
                "type": "string",
                "description": "用户ID",
                "default": "default",
            },
        },
        "required": ["course_id"],
    },
    function=_diagnose_weaknesses,
)
