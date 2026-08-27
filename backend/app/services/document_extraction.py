import hashlib
import io

from pypdf import PdfReader

from app.core.config import settings


def _chunk_words(words: list[str], target: int, overlap: int) -> list[list[str]]:
    """Splits words into fixed-size chunks with overlap between them."""
    if len(words) <= target:
        return [words]
    chunks = []
    step = target - overlap
    start = 0
    while start < len(words):
        chunks.append(words[start : start + target])
        if start + target >= len(words):
            break
        start += step
    return chunks


def extract_pdf_sections(file_bytes: bytes) -> list[dict]:
    """Extracts text from a PDF, one section per page. A page longer than
    chunk_target_words is split into multiple overlapping chunks, labeled
    "Page N (part i of k)"."""
    reader = PdfReader(io.BytesIO(file_bytes))
    sections = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        word_chunks = _chunk_words(
            text.split(), settings.chunk_target_words, settings.chunk_overlap_words
        )
        page_label = f"Page {i + 1}"
        for j, chunk_words in enumerate(word_chunks):
            heading = (
                page_label
                if len(word_chunks) == 1
                else f"{page_label} (part {j + 1} of {len(word_chunks)})"
            )
            sections.append({"heading": heading, "content": " ".join(chunk_words)})
    return sections


def compute_content_hash(sections: list[dict]) -> str:
    """Hashes a document's sections, used to detect duplicate content."""
    normalized = "\n".join(f"{s.get('heading', '')}\n{s.get('content', '')}" for s in sections)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
