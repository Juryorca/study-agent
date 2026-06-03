async def create_study_plan(weak_points: list[dict]) -> str:
    """Generate personalized study plan based on weakness points."""
    from app.services.llm import chat_completion

    if not weak_points:
        return "当前没有薄弱知识点需要特别关注。建议你可以：\n1. 进行综合练习巩固\n2. 预习下一章节内容\n3. 复习之前学过的重点知识"

    weak_desc = "\n".join(
        f"- {w['knowledge_point']}: 错误率 {w.get('error_rate', 0):.0%}"
        for w in weak_points
    )

    messages = [
        {
            "role": "system",
            "content": (
                "你是一位学习规划师。你需要根据学生的薄弱知识点，"
                "制定一个具体的、可执行的学习计划。计划应包含步骤序号、每步的具体任务、"
                "以及完成标准。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"学生薄弱知识点：\n{weak_desc}\n\n"
                "请制定一个分步骤的学习计划，帮助学生在接下来的2-3天内克服这些薄弱点。"
                "每步要具体、可衡量。"
            ),
        },
    ]

    response = await chat_completion(messages, temperature=0.5)
    return response.choices[0].message.content or ""
