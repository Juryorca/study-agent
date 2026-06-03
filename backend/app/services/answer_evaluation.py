from pydantic import BaseModel, Field


class ShortAnswerEvaluation(BaseModel):
    score: float = Field(description="得分")
    max_score: float = Field(default=10.0, description="满分")
    covered_points: list[str] = Field(description="学生答到的关键点")
    missing_points: list[str] = Field(description="学生遗漏的关键点")
    feedback: str = Field(description="评语和建议")


async def evaluate_short_answer(
    question_stem: str,
    correct_answer: str,
    student_answer: str,
    max_score: float = 10.0,
) -> ShortAnswerEvaluation:
    from app.services.llm import structured_completion

    messages = [
        {
            "role": "system",
            "content": (
                "你是一位公正的课程评卷老师。你需要根据标准答案评估学生的简答题回答。"
                "评估时请关注：1) 是否覆盖了关键知识点 2) 表述是否准确 3) 是否有遗漏。"
                "给出合理的分数和建设性的反馈。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"题目：{question_stem}\n\n"
                f"标准答案：{correct_answer}\n\n"
                f"学生答案：{student_answer}\n\n"
                f"满分：{max_score} 分\n\n"
                f"请评估学生的回答并给出分数。"
            ),
        },
    ]

    return await structured_completion(messages, ShortAnswerEvaluation, temperature=0.3)
