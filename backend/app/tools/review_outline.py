"""Tool: generate_review_outline - generate structured review outline."""

from app.services.rag import retrieve_chunks
from app.services.review_outline import generate_review_outline
from app.tools.registry import global_registry


async def _generate_review_outline(course_id: str, chapter: str = "") -> str:
    query = chapter or "全部内容"
    chunks = await retrieve_chunks(course_id, query, top_k=15)
    if not chunks:
        return f"未在课程 {course_id} 中找到相关章节资料。"
    outline = await generate_review_outline(chunks, chapter)
    return outline


global_registry.register(
    name="generate_review_outline",
    description="根据课程资料生成结构化的复习提纲，包含章节知识点、重点、易错点和考试提示。",
    parameters={
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "课程ID",
            },
            "chapter": {
                "type": "string",
                "description": "指定章节，如 '第三章'，留空则覆盖全部内容",
                "default": "",
            },
        },
        "required": ["course_id"],
    },
    function=_generate_review_outline,
)
