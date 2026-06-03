"""Tool: extract_knowledge_points - extract knowledge points from course documents."""

from app.services.knowledge_extraction import extract_knowledge_points
from app.services.rag import retrieve_chunks
from app.tools.registry import global_registry


async def _extract_knowledge_points(
    course_id: str,
    document_id: str = "",
    query: str = "",
) -> str:
    chunks = await retrieve_chunks(course_id, query or "全部知识点", top_k=20)
    if not chunks:
        return f"未在课程 {course_id} 中找到可提取知识点的资料。"
    result = await extract_knowledge_points(chunks)
    lines = [f"## {result.chapter}"]
    for kp in result.knowledge_points:
        lines.append(f"- [{kp.importance}] {kp.name}: {kp.description} (来源: {kp.source})")
    return "\n".join(lines)


global_registry.register(
    name="extract_knowledge_points",
    description="从课程资料中自动提取知识点。需要提供课程ID，可选指定文档ID或查询关键词以缩小范围。返回结构化的知识点列表，含重要程度和来源。",
    parameters={
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "课程ID",
            },
            "document_id": {
                "type": "string",
                "description": "指定文档ID，留空则查询全部课程资料",
                "default": "",
            },
            "query": {
                "type": "string",
                "description": "指定检索关键词，如 '第三章' 或 'SQL'",
                "default": "",
            },
        },
        "required": ["course_id"],
    },
    function=_extract_knowledge_points,
)
