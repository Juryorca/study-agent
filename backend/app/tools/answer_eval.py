"""Tool: evaluate_answer - evaluate student's answer to a question."""

from app.services.answer_evaluation import evaluate_short_answer
from app.tools.registry import global_registry


async def _evaluate_answer(
    question_id: str = "",
    question_stem: str = "",
    correct_answer: str = "",
    student_answer: str = "",
    question_type: str = "single_choice",
    max_score: float = 10.0,
) -> str:
    # For multiple choice, direct comparison
    if question_type == "single_choice":
        is_correct = student_answer.strip().upper() == correct_answer.strip().upper()
        if is_correct:
            return f"回答正确！答案是 {correct_answer}。"
        else:
            return f"回答错误。你的答案: {student_answer}，正确答案: {correct_answer}。"

    # For short answer, use LLM evaluation
    if not question_stem or not correct_answer:
        return "简答题评估需要提供题目内容和标准答案。"
    if not student_answer.strip():
        return "学生未作答，得分 0 分。"

    evaluation = await evaluate_short_answer(
        question_stem=question_stem,
        correct_answer=correct_answer,
        student_answer=student_answer,
        max_score=max_score,
    )
    return (
        f"得分: {evaluation.score}/{evaluation.max_score}\n"
        f"答到的关键点: {', '.join(evaluation.covered_points) or '无'}\n"
        f"遗漏的关键点: {', '.join(evaluation.missing_points) or '无'}\n"
        f"评语: {evaluation.feedback}"
    )


global_registry.register(
    name="evaluate_answer",
    description="评估学生提交的答案。选择题直接判分，简答题通过AI评估语义正确度，给出分数和评语。",
    parameters={
        "type": "object",
        "properties": {
            "question_id": {
                "type": "string",
                "description": "题目ID",
                "default": "",
            },
            "question_stem": {
                "type": "string",
                "description": "题目题干（简答题必需）",
                "default": "",
            },
            "correct_answer": {
                "type": "string",
                "description": "标准答案",
                "default": "",
            },
            "student_answer": {
                "type": "string",
                "description": "学生提交的答案",
            },
            "question_type": {
                "type": "string",
                "description": "题型：single_choice 或 short_answer",
                "enum": ["single_choice", "short_answer"],
                "default": "single_choice",
            },
            "max_score": {
                "type": "number",
                "description": "简答题满分，选择题固定1分",
                "default": 10.0,
            },
        },
        "required": ["student_answer"],
    },
    function=_evaluate_answer,
)
