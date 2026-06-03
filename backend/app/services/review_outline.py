import asyncio

from sqlalchemy import select

from app.database import async_session
from app.models.review_outline import ReviewOutline


async def generate_review_outline(
    chunks: list[dict],
    chapter: str = "",
) -> str:
    """Non-streaming outline (kept for backward compat)."""
    from app.services.llm import chat_completion

    context = "\n\n".join(
        f"[来源: {c.get('source', '未知')}]\n{c['content']}" for c in chunks
    )

    messages = _build_messages(context, chapter)
    response = await chat_completion(messages, temperature=0.5, max_tokens=4096)
    return response.choices[0].message.content or ""


async def generate_review_outline_background(outline_id: str, chunks: list[dict], chapter: str = ""):
    """Generate outline in background. Uses instructor (JSON mode) since MO AI requires it."""
    from app.services.llm import structured_completion
    from pydantic import BaseModel, Field

    class OutlineResult(BaseModel):
        outline: str = Field(description="完整的 Markdown 格式复习提纲")

    context = "\n\n".join(
        f"[来源: {c.get('source', '未知')}]\n{c['content']}" for c in chunks
    )
    messages = _build_messages(context, chapter)

    async with async_session() as db:
        try:
            result = await db.execute(select(ReviewOutline).where(ReviewOutline.id == outline_id))
            outline = result.scalar_one()
            outline.status = "generating"
            await db.commit()

            llm_result = await structured_completion(messages, OutlineResult, temperature=0.5, max_tokens=4096)
            content = llm_result.outline
            print(f"[OUTLINE] instructor result: len={len(content) if content else 0} preview={repr(content[:200]) if content else 'EMPTY'}")

            if content and content.strip():
                outline.content = content
                outline.status = "completed"
            else:
                outline.status = "failed"
                outline.error_message = "LLM 返回了空内容"
            await db.commit()

        except Exception as e:
            # Re-fetch inside a fresh query to avoid stale object issues
            result = await db.execute(select(ReviewOutline).where(ReviewOutline.id == outline_id))
            outline = result.scalar_one_or_none()
            if outline:
                outline.status = "failed"
                outline.error_message = f"{type(e).__name__}: {e}"
                await db.commit()


def _build_messages(context: str, chapter: str) -> list[dict]:
    chapter_hint = f"请针对「{chapter}」章节" if chapter else "请针对全部内容"
    return [
        {
            "role": "system",
            "content": (
                "你是一位经验丰富的大学课程辅导老师，擅长帮学生梳理复习思路。"
                "你的提纲必须基于提供的课程资料，不能凭空编造。"
                "输出严格的 Markdown 格式，结构如下：\n\n"
                "## 一、章节概览\n"
                "简要说明本章核心内容和在课程中的地位（2-3 句）\n\n"
                "## 二、知识体系图谱\n"
                "用层级列表梳理知识点之间的逻辑关系，例如：\n"
                "- 主题A\n"
                "  - 概念1：一句话定义\n"
                "  - 概念2：一句话定义\n"
                "- 主题B\n"
                "  - ...\n\n"
                "## 三、重点知识点精讲\n"
                "挑出 3-5 个最重要的知识点，每个用一段话讲清楚：是什么、为什么重要、怎么理解。\n\n"
                "## 四、易错点与混淆辨析\n"
                "列出学生容易出错或容易混淆的概念对，用对比方式讲清楚区别。\n\n"
                "## 五、考试高频考点\n"
                "根据资料内容，指出最可能出现在考试中的知识点和题型方向。\n\n"
                "## 六、复习建议\n"
                "给出具体的复习顺序和时间分配建议。\n\n"
                "要求：内容充实、具体、可操作，不要只说「帮助学生梳理知识结构」这类空话。"
            ),
        },
        {
            "role": "user",
            "content": f"{chapter_hint}\n\n课程资料内容：\n{context}\n\n请按照 Markdown 格式生成详细的复习提纲。",
        },
    ]
