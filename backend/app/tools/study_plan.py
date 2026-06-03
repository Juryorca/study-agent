"""Tool: create_study_plan - generate personalized study plan."""

from app.services.study_planning import create_study_plan
from app.tools.registry import global_registry


async def _create_study_plan(
    course_id: str = "",
    weak_points: list = [],
    user_id: str = "default",
) -> str:
    # If weak_points not provided, fetch from DB
    if not weak_points:
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

        from collections import defaultdict
        stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "wrong": 0})
        for r in records:
            kp = r.knowledge_point or "未知"
            stats[kp]["total"] += 1
            if not r.is_correct:
                stats[kp]["wrong"] += 1

        weak_points = [
            {
                "knowledge_point": kp,
                "error_rate": s["wrong"] / s["total"] if s["total"] > 0 else 0,
            }
            for kp, s in stats.items()
            if s["total"] >= 3 and s["wrong"] / s["total"] >= 0.3
        ]
        weak_points.sort(key=lambda x: x["error_rate"], reverse=True)

    plan = await create_study_plan(weak_points)
    return f"## 个性化学习计划\n\n{plan}"


global_registry.register(
    name="create_study_plan",
    description="根据学生薄弱点生成个性化学习计划。需要传入薄弱知识点列表，或提供课程ID从答题记录自动分析。返回分步骤的可执行学习计划。",
    parameters={
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "课程ID",
                "default": "",
            },
            "user_id": {
                "type": "string",
                "description": "用户ID",
                "default": "default",
            },
            "weak_points": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "knowledge_point": {"type": "string"},
                        "error_rate": {"type": "number"},
                    },
                },
                "description": "薄弱知识点列表，留空则自动分析",
                "default": [],
            },
        },
        "required": [],
    },
    function=_create_study_plan,
)
