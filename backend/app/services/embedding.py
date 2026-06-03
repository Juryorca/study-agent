import uuid
from pathlib import Path

import numpy as np
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

_client: chromadb.PersistentClient | None = None

_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "embedding"
_ort_session = None
_tokenizer = None

EMBED_BATCH_SIZE = 16
_MODEL_MAX_LENGTH = 256  # all-MiniLM-L6-v2 was trained with 256, not 512


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_course_collection(course_id: str) -> chromadb.Collection:
    client = get_chroma_client()
    collection_name = f"course_{course_id}"
    try:
        return client.get_collection(collection_name)
    except Exception:
        return client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )


def _get_ort_session():
    global _ort_session
    if _ort_session is None:
        import onnxruntime as ort
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 0
        opts.inter_op_num_threads = 0
        _ort_session = ort.InferenceSession(
            str(_MODEL_DIR / "model.onnx"),
            sess_options=opts,
        )
    return _ort_session


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        from transformers import AutoTokenizer
        _tokenizer = AutoTokenizer.from_pretrained(str(_MODEL_DIR))
    return _tokenizer


def reset_embedding_client():
    pass  # Stateless ONNX session, nothing to reset


def _embed_onnx(texts: list[str]) -> list[list[float]]:
    tokenizer = _get_tokenizer()
    session = _get_ort_session()

    encoded = tokenizer(texts, padding=True, truncation=True, max_length=_MODEL_MAX_LENGTH, return_tensors="np")
    ort_inputs = {
        "input_ids": encoded["input_ids"],
        "attention_mask": encoded["attention_mask"],
        "token_type_ids": np.zeros_like(encoded["input_ids"], dtype=np.int64),
    }
    outputs = session.run(None, ort_inputs)
    token_embeddings = outputs[0]  # (batch, seq_len, hidden_dim)

    # Mean pooling with attention mask
    mask = np.expand_dims(encoded["attention_mask"].astype(np.float32), -1)
    embeddings = (token_embeddings * mask).sum(axis=1) / mask.sum(axis=1)

    # L2 normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms

    return embeddings.tolist()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings using local ONNX model, batched to avoid CPU overload."""
    all_embeddings = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        all_embeddings.extend(_embed_onnx(batch))
    return all_embeddings


async def index_chunks(
    course_id: str,
    chunks: list[dict],
    document_id: str,
) -> int:
    """Index chunks into Chroma with embeddings."""
    if not chunks:
        return 0

    texts = [c["content"] for c in chunks]
    embeddings = await embed_texts(texts)

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "course_id": course_id,
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    collection = get_course_collection(course_id)
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    return len(ids)
