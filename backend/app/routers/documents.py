import asyncio
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session, get_db
from sqlalchemy import delete

from app.models.chunk import Chunk
from app.models.document import Document
from app.schemas.document import DocumentList, DocumentRead, DocumentUploadResponse
from app.services.chunking import chunk_pages
from app.services.document_parser import parse_document
from app.services.embedding import index_chunks

router = APIRouter()


async def _process_document(doc_id: str, course_id: str, ext: str, save_path: str):
    """Background task: parse → chunk → ready for embedding."""
    async with async_session() as db:
        try:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one()
            doc.status = "parsing"
            await db.commit()

            loop = asyncio.get_running_loop()
            pages = await loop.run_in_executor(None, parse_document, save_path, ext)
            chunks = await loop.run_in_executor(None, chunk_pages, pages)

            doc.chunk_count = len(chunks)
            await db.commit()

            if chunks:
                for c in chunks:
                    chunk = Chunk(
                        document_id=doc_id,
                        course_id=course_id,
                        content=c["content"],
                        page_number=c["page_number"],
                        chunk_index=c["chunk_index"],
                        vector_id="",
                    )
                    db.add(chunk)
                await db.commit()

            doc.status = "chunked"
            await db.commit()

        except Exception as e:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one()
            doc.status = "failed"
            doc.error_message = str(e)
            await db.commit()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    course_id: str = Form(...),
    bg: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    supported = {"pdf", "pptx", "txt", "md"}
    if ext not in supported:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    # Save file
    file_id = str(uuid.uuid4())
    save_name = f"{file_id}.{ext}"
    save_path = os.path.join(settings.upload_dir, save_name)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = Document(
        id=file_id,
        course_id=course_id,
        filename=file.filename,
        file_type=ext,
        file_path=save_path,
        status="uploaded",
    )
    db.add(doc)
    await db.commit()

    # Offload processing to background — returns immediately
    if bg is not None:
        bg.add_task(_process_document, file_id, course_id, ext, save_path)

    return DocumentUploadResponse(
        id=file_id,
        filename=file.filename,
        status="uploaded",
        message="上传成功，后台处理中...",
    )


@router.get("", response_model=DocumentList)
async def list_documents(course_id: str = "", db: AsyncSession = Depends(get_db)):
    query = select(Document).order_by(Document.created_at.desc())
    if course_id:
        query = query.where(Document.course_id == course_id)
    result = await db.execute(query)
    docs = result.scalars().all()
    return DocumentList(documents=docs, total=len(docs))


@router.post("/{document_id}/reindex")
async def reindex_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Re-index a document's chunks into Chroma (for recovery after embedding failures)."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="资料不存在")

    result = await db.execute(
        select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index)
    )
    chunks_db = result.scalars().all()
    if not chunks_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="该文档没有可索引的文本块")

    chunks = [
        {"content": c.content, "page_number": c.page_number, "chunk_index": c.chunk_index}
        for c in chunks_db
    ]

    doc.status = "embedding"
    await db.commit()

    try:
        await index_chunks(doc.course_id, chunks, document_id)
    except Exception as e:
        doc.status = "chunked"
        doc.error_message = f"向量索引失败: {e}"
        await db.commit()
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"向量索引失败: {e}")

    doc.status = "completed"
    doc.error_message = ""
    await db.commit()

    return {"message": f"重新索引成功，{len(chunks)} 个文本块已写入向量库", "chunk_count": len(chunks)}


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="资料不存在")

    # Delete chunks from DB
    from sqlalchemy import delete
    await db.execute(delete(Chunk).where(Chunk.document_id == document_id))
    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    # Delete document record
    await db.delete(doc)
    await db.commit()
    return {"message": "已删除", "document_id": document_id}
