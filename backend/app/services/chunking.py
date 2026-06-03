import tiktoken

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        try:
            _tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _tokenizer = tiktoken.get_encoding("o200k_base")
    return _tokenizer


def count_tokens(text: str) -> int:
    enc = _get_tokenizer()
    return len(enc.encode(text))


def split_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Recursive text splitter using token counts."""
    enc = _get_tokenizer()
    tokens = enc.encode(text)

    if len(tokens) <= chunk_size:
        return [text] if text.strip() else []

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        if end >= len(tokens):
            break
        start = end - chunk_overlap

    return chunks


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Chunk document pages into smaller segments with metadata."""
    result = []
    for page_info in pages:
        page_num = page_info["page"]
        content = page_info["content"]
        text_chunks = split_text(content, chunk_size, chunk_overlap)
        for idx, chunk_text in enumerate(text_chunks):
            if chunk_text.strip():
                result.append({
                    "page_number": page_num,
                    "chunk_index": idx,
                    "content": chunk_text.strip(),
                })
    return result
