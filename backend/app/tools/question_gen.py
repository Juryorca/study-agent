"""Tool: generate_questions - generate practice questions from course material."""

from app.services.question_generation import generate_questions
from app.services.rag import retrieve_chunks
from app.tools.registry import global_registry


async def _generate_questions(
    course_id: str,
    knowledge_point: str = "",
    question_type: str = "single_choice",
    count: int = 5,
    difficulty: str = "medium",
) -> str:
    query = knowledge_point or "核心知识点"
    chunks = await retrieve_chunks(course_id, query, top_k=10)
    if not chunks:
        return f"未在课程 {course_id} 中找到相关课程资料来生成题目。"

    questions = await generate_questions(chunks, knowledge_point, question_type, count, difficulty)
    lines = [f"## 已生成 {len(questions)} 道{question_type}题\n"]
    for i, q in enumerate(questions, 1):
        lines.append(f"**第{i}题** ({q.difficulty}) [{q.knowledge_point}]")
        lines.append(f"{q.stem}")
        if q.options:
            for k, v in q.options.items():
                lines.append(f"  {k}. {v}")
        lines.append(f"正确答案: {q.answer}")
        lines.append(f"解析: {q.explanation}")
        lines.append("")
    return "\n".join(lines)


global_registry.register(
    name="generate_questions",
    description="根据课程资料自动生成练习题。支持单选题和简答题，可指定知识点、难度和数量。生成后可直接用于学生练习。",
    parameters={
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "课程ID",
            },
            "knowledge_point": {
                "type": "string",
                "description": "目标知识点，如 'SQL多表连接'，留空为综合",
                "default": "",
            },
            "question_type": {
                "type": "string",
                "description": "题型：single_choice 或 short_answer",
                "enum": ["single_choice", "short_answer"],
                "default": "single_choice",
            },
            "count": {
                "type": "integer",
                "description": "生成数量",
                "default": 5,
            },
            "difficulty": {
                "type": "string",
                "description": "难度：easy, medium, hard",
                "enum": ["easy", "medium", "hard"],
                "default": "medium",
            },
        },
        "required": ["course_id"],
    },
    function=_generate_questions,
)
