from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatMessageList,
    ChatSessionCreate,
    ChatSessionList,
    ChatSessionRead,
)

router = APIRouter()


@router.get("/sessions", response_model=ChatSessionList)
async def list_sessions(course_id: str = "", db: AsyncSession = Depends(get_db)):
    query = select(ChatSession).order_by(ChatSession.updated_at.desc())
    if course_id:
        query = query.where(ChatSession.course_id == course_id)
    result = await db.execute(query)
    sessions = result.scalars().all()
    return ChatSessionList(sessions=sessions, total=len(sessions))


@router.post("/sessions", response_model=ChatSessionRead)
async def create_session(req: ChatSessionCreate, db: AsyncSession = Depends(get_db)):
    session = ChatSession(course_id=req.course_id, user_id="default", title=req.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    # Delete messages first (SQLite doesn't enforce FK cascade)
    await db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    await db.delete(session)
    await db.commit()
    return {"message": "已删除"}


@router.get("/sessions/{session_id}/messages", response_model=ChatMessageList)
async def list_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return ChatMessageList(messages=messages, total=len(messages))
