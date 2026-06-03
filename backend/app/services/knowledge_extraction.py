from pydantic import BaseModel, Field


class KnowledgePointItem(BaseModel):
    name: str = Field(description="知识点名称")
    description: str = Field(description="知识点详细描述")
    importance: str = Field(description="重要程度: high / medium / low")
    source: str = Field(default="", description="来源页码或段落")


class KnowledgeExtractionResult(BaseModel):
    chapter: str = Field(description="章节标题")
    knowledge_points: list[KnowledgePointItem] = Field(description="提取的知识点列表")


async def extract_knowledge_points(
    chunks: list[dict],
    course_name: str = "",
) -> KnowledgeExtractionResult:
    """Single-call extraction (kept for backward compat)."""
    from app.services.llm import structured_completion

    context = "\n\n".join(
        f"[来源: {c.get('source', '未知')}]\n{c['content']}" for c in chunks
    )

    messages = [
        {
            "role": "system",
            "content": (
                "你是一位专业的课程知识分析专家。你的任务是从课程资料中提取核心知识点。"
                "请仔细阅读提供的课程资料片段，提取出其中包含的知识点。"
                "每个知识点需包含名称、描述、重要程度和来源。"
            ),
        },
        {
            "role": "user",
            "content": f"课程名称：{course_name}\n\n课程资料内容：\n{context}\n\n请从以上资料中提取所有核心知识点。",
        },
    ]

    return await structured_completion(messages, KnowledgeExtractionResult, temperature=0.3)


async def extract_knowledge_points_stream(
    chunks: list[dict],
    course_name: str = "",
    batch_size: int = 8,
):
    """Extract knowledge points with SSE progress events.

    Yields dicts: {"type": "progress", "message": "..."} or {"type": "result", "knowledge_points": [...]}
    """
    from app.services.llm import structured_completion

    if not chunks:
        yield {"type": "result", "knowledge_points": []}
        return

    batches = [chunks[i : i + batch_size] for i in range(0, len(chunks), batch_size)]
    yield {"type": "progress", "message": f"已检索到 {len(chunks)} 个文本块，分 {len(batches)} 批提取知识点..."}

    all_points: list[dict] = []
    seen_names: set[str] = set()
    chapter = ""

    for batch_idx, batch in enumerate(batches):
        yield {"type": "progress", "message": f"AI 正在分析第 {batch_idx + 1}/{len(batches)} 批（{len(batch)} 个文本块）..."}

        context = "\n\n".join(
            f"[来源: {c.get('source', '未知')}]\n{c['content']}" for c in batch
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位专业的课程知识分析专家。从课程资料中提取核心知识点。"
                    "每个知识点包含名称、描述、重要程度(high/medium/low)和来源。"
                    "只提取明确出现在资料中的知识点，不要编造。"
                ),
            },
            {
                "role": "user",
                "content": f"课程名称：{course_name}\n\n课程资料内容（第{batch_idx + 1}部分）：\n{context}\n\n请从以上资料中提取所有核心知识点。",
            },
        ]

        try:
            result = await structured_completion(messages, KnowledgeExtractionResult, temperature=0.3)
            chapter = result.chapter or chapter
            for kp in result.knowledge_points:
                if kp.name.strip() and kp.name not in seen_names:
                    seen_names.add(kp.name)
                    all_points.append({"chapter": chapter, **kp.model_dump()})
        except Exception as e:
            yield {"type": "progress", "message": f"第 {batch_idx + 1} 批提取失败: {e}，继续处理下一批..."}

    yield {"type": "progress", "message": f"提取完成，共识别 {len(all_points)} 个知识点，正在保存..."}
    yield {"type": "result", "knowledge_points": all_points}
