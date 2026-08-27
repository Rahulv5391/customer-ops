import hashlib
import io

from pypdf import PdfReader

from app.core.config import settings


def _chunk_words(words: list[str], target: int, overlap: int) -> list[list[str]]:
    """Fixed-size word-count chunking with overlap - not paragraph-boundary
    detection, since pypdf's plain text extraction doesn't reliably
    preserve blank-line paragraph breaks across different PDF generators
    (some have none at all in the raw text stream). A word-count target is
    deterministic regardless of a given PDF's internal formatting, and
    directly caps chunk size at what's actually safe for the embedding
    model (see settings.chunk_target_words for the measurement)."""
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
    """One chunk per PDF page, unless a page's text exceeds
    settings.chunk_target_words - a whole page was silently losing content
    past roughly its first 100-150 words to the embedding model's effective
    input limit (measured directly, see Architecture.md §5/6), so a page
    that's short enough stays a single citable "Page N" chunk (the common
    case for short demo-style documents), while a longer page is split into
    overlapping "Page N (part i of k)" chunks, each safely under that
    limit. Still no real heading detection - out of scope here."""
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
    """Canonical hash of a document's sections - the real identity signal
    for duplicate detection, independent of filename or title. Used
    identically for both the JSON-body and PDF-upload creation paths, so a
    document created one way and re-uploaded the other way is still
    recognized as the same content."""
    normalized = "\n".join(f"{s.get('heading', '')}\n{s.get('content', '')}" for s in sections)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
