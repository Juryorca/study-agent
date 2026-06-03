from __future__ import annotations
from pydantic import BaseModel, Field


class WeakPointItem(BaseModel):
    knowledge_point: str = Field(description="薄弱知识点名称")
    total_attempts: int = Field(description="总答题次数")
    wrong_count: int = Field(description="错误次数")
    error_rate: float = Field(description="错误率")
    suggestion: str = Field(description="复习建议")


class DiagnosisResult(BaseModel):
    weak_points: list[WeakPointItem] = Field(description="薄弱知识点列表")
    overall_summary: str = Field(description="整体评价")


async def diagnose_weaknesses(
    answer_records: list[dict],
    all_knowledge_points: list[str] = [],
) -> DiagnosisResult:
    """Analyze student weaknesses based on answer records."""
    # First do statistical analysis
    from collections import defaultdict

    stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "wrong": 0})
    for record in answer_records:
        kp = record.get("knowledge_point", "未知知识点")
        stats[kp]["total"] += 1
        if not record.get("is_correct", False):
            stats[kp]["wrong"] += 1

    weak_points = []
    for kp, s in stats.items():
        rate = s["wrong"] / s["total"] if s["total"] > 0 else 0
        # Only flag if error rate > 30%
        if rate >= 0.3:
            weak_points.append(WeakPointItem(
                knowledge_point=kp,
                total_attempts=s["total"],
                wrong_count=s["wrong"],
                error_rate=round(rate, 2),
                suggestion="",
            ))

    # Generate suggestions via LLM
    if weak_points:
        from app.services.llm import chat_completion

        weak_desc = "\n".join(
            f"- {w.knowledge_point}: 答题{w.total_attempts}次, 错误{w.wrong_count}次, 错误率{w.error_rate:.0%}"
            for w in weak_points
        )
        messages = [
            {"role": "system", "content": "你是一位学习辅导专家。针对学生的薄弱知识点，给出简洁的复习建议。"},
            {"role": "user", "content": f"学生的薄弱知识点：\n{weak_desc}\n\n请给每个知识点一句复习建议，并给出整体评价。"},
        ]
        response = await chat_completion(messages, temperature=0.5)
        overall_summary = response.choices[0].message.content or ""

        # Heuristic suggestions by error rate
        for i, w in enumerate(weak_points):
            if w.suggestion == "":
                if w.error_rate > 0.7:
                    w.suggestion = f"建议重新学习{w.knowledge_point}基础知识，从教材和PPT开始"
                elif w.error_rate > 0.5:
                    w.suggestion = f"建议做5道{w.knowledge_point}专项练习"
                else:
                    w.suggestion = f"建议复习{w.knowledge_point}中出错的概念点"
    else:
        overall_summary = "目前答题正确率良好，继续保持！"

    return DiagnosisResult(weak_points=weak_points, overall_summary=overall_summary)
