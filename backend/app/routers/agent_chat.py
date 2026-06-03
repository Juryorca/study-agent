import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.agent.controller import AgentController, SYSTEM_PROMPT
from app.agent.memory import MAX_HISTORY, ConversationMemory
from app.database import async_session
from app.models.chat import ChatMessage, ChatSession
from app.schemas.agent import AgentChatRequest

router = APIRouter()


async def _save_messages(session_id: str, messages: list[dict]):
    """Persist messages to DB after streaming."""
    async with async_session() as db:
        for msg in messages:
            if msg["role"] == "system":
                continue
            db.add(ChatMessage(
                session_id=session_id,
                role=msg["role"],
                content=msg.get("content", ""),
                tool_name=msg.get("name", ""),
                tool_args=msg.get("tool_calls") or {},
            ))
        # Auto-title: use first user message truncated
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()
        if session and session.title == "新对话":
            first_user = next((m for m in messages if m["role"] == "user"), None)
            if first_user:
                text = first_user.get("content", "")
                session.title = text[:50] + ("..." if len(text) > 50 else "")
        await db.commit()


@router.post("/chat")
async def agent_chat(req: AgentChatRequest):
    # Initialize memory from DB if session_id provided
    memory = None
    if req.session_id:
        async with async_session() as db:
            result = await db.execute(select(ChatSession).where(ChatSession.id == req.session_id))
            if not result.scalar_one_or_none():
                raise HTTPException(404, "会话不存在")
            msg_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == req.session_id)
                .order_by(ChatMessage.created_at)
                .limit(MAX_HISTORY * 2)
            )
            history = msg_result.scalars().all()
            if history:
                memory = ConversationMemory()
                for m in history:
                    memory.add(m.role, m.content, name=m.tool_name or None)

    if memory is None:
        memory = ConversationMemory()
    agent = AgentController(memory, course_id=req.course_id, user_id=req.user_id)
    collected: list[dict] = []

    async def event_stream():
        async for event in agent.run_stream(req.message):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        # Collect messages from agent memory and persist
        for m in agent.memory.messages:
            collected.append(dict(m))
        if req.session_id:
            await _save_messages(req.session_id, collected)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/sync")
async def agent_chat_sync(req: AgentChatRequest):
    agent = AgentController(memory=ConversationMemory(), course_id=req.course_id, user_id=req.user_id)
    response = await agent.run(req.message)
    return {"response": response}


@router.post("/reset")
async def reset_chat(user_id: str = "default"):
    # No-op: sessions are now persisted. Delete individual sessions via sessions API.
    return {"message": "请通过会话管理删除对话"}
