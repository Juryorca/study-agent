from pathlib import Path


def parse_pptx(file_path: str) -> list[dict]:
    """Parse PPTX file, returns list of {page, content}."""
    from pptx import Presentation

    prs = Presentation(file_path)
    pages = []
    for i, slide in enumerate(prs.slides, 1):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        texts.append(text)
            if shape.has_table:
                table = shape.table
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        texts.append(row_text)
        content = "\n".join(texts)
        if content.strip():
            pages.append({"page": i, "content": content})
    return pages


def parse_pdf(file_path: str) -> list[dict]:
    """Parse PDF file, returns list of {page, content}."""
    import fitz

    doc = fitz.open(file_path)
    pages = []
    for i in range(doc.page_count):
        page = doc[i]
        text = page.get_text()
        if text.strip():
            pages.append({"page": i + 1, "content": text.strip()})
    doc.close()
    return pages


def parse_txt(file_path: str) -> list[dict]:
    """Parse TXT/MD file, treat as one doc with line breaks as pagination."""
    content = Path(file_path).read_text(encoding="utf-8", errors="replace")
    if not content.strip():
        return []

    paragraphs = content.split("\n\n")
    pages = []
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if para:
            pages.append({"page": i + 1, "content": para})
    return pages


PARSERS = {
    "pptx": parse_pptx,
    "pdf": parse_pdf,
    "txt": parse_txt,
    "md": parse_txt,
}


def parse_document(file_path: str, file_type: str) -> list[dict]:
    parser = PARSERS.get(file_type.lower())
    if not parser:
        raise ValueError(f"Unsupported file type: {file_type}")
    return parser(file_path)
