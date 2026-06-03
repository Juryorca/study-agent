"""Tool: search_course_material - retrieve relevant course content from vector DB."""

from app.services.rag import retrieve_chunks
from app.tools.registry import global_registry


async def _search_course_material(course_id: str, query: str, top_k: int = 5) -> str:
    chunks = await retrieve_chunks(course_id, query, top_k)
    if not chunks:
        return f"未在课程 {course_id} 中找到与 '{query}' 相关的资料。"
    results = []
    for i, c in enumerate(chunks, 1):
        results.append(f"[{i}] 来源: {c['source']}, 相关度: {c['score']}\n{c['content']}")
    return "\n\n".join(results)


global_registry.register(
    name="search_course_material",
    description="从课程知识库中检索与查询相关的课程资料片段。传入课程ID和查询文本，返回最相关的文档片段及其来源。",
    parameters={
        "type": "object",
        "properties": {
            "course_id": {
                "type": "string",
                "description": "课程ID，例如 'database_001'",
            },
            "query": {
                "type": "string",
                "description": "检索查询文本，例如 'SQL多表连接'",
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量，默认5",
                "default": 5,
            },
        },
        "required": ["course_id", "query"],
    },
    function=_search_course_material,
)
