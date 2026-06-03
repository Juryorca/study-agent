import json

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, get_db
from app.models.knowledge_point import KnowledgePoint
from app.schemas.knowledge import (
    ExtractRequest,
    KnowledgePointList,
    MasteryUpdateRequest,
    ReviewOutlineRequest,
)
from app.services.knowledge_extraction import extract_knowledge_points_stream
from app.services.rag import retrieve_chunks
from app.services.review_outline import generate_review_outline_background

router = APIRouter()


@router.post("/extract")
async def extract_knowledge(
    req: ExtractRequest,
    course_id: str = "",
):
    chunks = await retrieve_chunks(course_id, query="核心知识点", top_k=20)
    if not chunks:
        return KnowledgePointList(knowledge_points=[], total=0)

    async def event_stream():
        async for event in extract_knowledge_points_stream(chunks):
            if event["type"] == "progress":
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            elif event["type"] == "result":
                async with async_session() as db:
                    saved = []
                    for kp_data in event["knowledge_points"]:
                        record = KnowledgePoint(
                            course_id=course_id,
                            name=kp_data["name"],
                            description=kp_data["description"],
                            importance=kp_data["importance"],
                            source=kp_data.get("source", ""),
                            document_id=req.document_id,
                            chapter=kp_data.get("chapter", ""),
                        )
                        db.add(record)
                        await db.flush()
                        saved.append(record)
                    await db.commit()

                    result_data = {
                        "type": "done",
                        "knowledge_points": [
                            {"id": r.id, "name": r.name, "description": r.description,
                             "importance": r.importance, "source": r.source,
                             "course_id": r.course_id, "document_id": r.document_id,
                             "chapter": r.chapter, "mastery": r.mastery,
                             "created_at": r.created_at.isoformat()}
                            for r in saved
                        ],
                        "total": len(saved),
                    }
                    yield f"data: {json.dumps(result_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("", response_model=KnowledgePointList)
async def list_knowledge_points(
    course_id: str = "",
    importance: str = "",
    mastery: str = "",
    chapter: str = "",
    search: str = "",
    db: AsyncSession = Depends(get_db),
):
    query = select(KnowledgePoint).order_by(KnowledgePoint.created_at.desc())
    if course_id:
        query = query.where(KnowledgePoint.course_id == course_id)
    if importance:
        query = query.where(KnowledgePoint.importance == importance)
    if mastery:
        query = query.where(KnowledgePoint.mastery == mastery)
    if chapter:
        query = query.where(KnowledgePoint.chapter == chapter)
    if search:
        query = query.where(
            (KnowledgePoint.name.ilike(f"%{search}%"))
            | (KnowledgePoint.description.ilike(f"%{search}%"))
        )
    result = await db.execute(query)
    points = result.scalars().all()
    return KnowledgePointList(knowledge_points=points, total=len(points))


@router.patch("/{kp_id}/mastery")
async def update_mastery(
    kp_id: str,
    req: MasteryUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(KnowledgePoint).where(KnowledgePoint.id == kp_id))
    kp = result.scalar_one_or_none()
    if not kp:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="知识点不存在")
    kp.mastery = req.mastery
    await db.commit()
    return {"id": kp.id, "mastery": kp.mastery}


@router.post("/outline")
async def create_outline(
    req: ReviewOutlineRequest,
    course_id: str = "",
    bg: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """Start background outline generation. Returns immediately with outline_id."""
    from app.models.review_outline import ReviewOutline

    chunks = await retrieve_chunks(course_id, query=req.chapter or "全部内容", top_k=15)
    if not chunks:
        return {"outline_id": "", "status": "no_content", "message": "暂无课程资料，请先上传资料。"}

    outline = ReviewOutline(
        course_id=course_id,
        chapter=req.chapter,
        status="generating",
    )
    db.add(outline)
    await db.commit()
    await db.refresh(outline)

    if bg is not None:
        bg.add_task(generate_review_outline_background, outline.id, chunks, req.chapter)

    return {"outline_id": outline.id, "status": "generating", "message": "提纲生成中..."}


@router.get("/outline")
async def list_outlines(
    course_id: str = "",
    db: AsyncSession = Depends(get_db),
):
    """List all outlines for a course."""
    from app.models.review_outline import ReviewOutline

    query = select(ReviewOutline).order_by(ReviewOutline.created_at.desc())
    if course_id:
        query = query.where(ReviewOutline.course_id == course_id)
    result = await db.execute(query)
    outlines = result.scalars().all()
    return {
        "outlines": [
            {
                "id": o.id,
                "course_id": o.course_id,
                "chapter": o.chapter,
                "content": o.content,
                "status": o.status,
                "error_message": o.error_message,
                "created_at": o.created_at.isoformat(),
                "updated_at": o.updated_at.isoformat() if o.updated_at else None,
            }
            for o in outlines
        ]
    }


@router.delete("/outline/{outline_id}")
async def delete_outline(outline_id: str, db: AsyncSession = Depends(get_db)):
    from app.models.review_outline import ReviewOutline

    result = await db.execute(select(ReviewOutline).where(ReviewOutline.id == outline_id))
    outline = result.scalar_one_or_none()
    if not outline:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="提纲不存在")
    await db.delete(outline)
    await db.commit()
    return {"message": "已删除"}
