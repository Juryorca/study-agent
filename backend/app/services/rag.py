from __future__ import annotations
from app.services.embedding import embed_texts, get_course_collection


async def retrieve_chunks(
    course_id: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Retrieve top-k relevant chunks from Chroma for the given query."""
    collection = get_course_collection(course_id)

    query_embedding = await embed_texts([query])
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k, collection.count()) if collection.count() > 0 else 1,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
        distance = results["distances"][0][i] if results["distances"] else 1.0
        chunks.append({
            "content": doc,
            "source": f"第 {metadata.get('page_number', '?')} 页",
            "document_id": metadata.get("document_id", ""),
            "score": round(1 - distance, 4),
        })
    return chunks
