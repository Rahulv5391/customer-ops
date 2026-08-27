import hashlib
import io

from pypdf import PdfReader


def extract_pdf_sections(file_bytes: bytes) -> list[dict]:
    """One section per PDF page - a deliberately simple, deterministic
    chunking strategy (no heading detection or LLM structuring). Good
    enough for demo-scope ingestion; a real production pipeline would want
    smarter section/heading detection, but that's out of scope here."""
    reader = PdfReader(io.BytesIO(file_bytes))
    sections = []
    for i, page in enumerate(reader.pages):
        text = (page.extract_text() or "").strip()
        if text:
            sections.append({"heading": f"Page {i + 1}", "content": text})
    return sections


def compute_content_hash(sections: list[dict]) -> str:
    """Canonical hash of a document's sections - the real identity signal
    for duplicate detection, independent of filename or title. Used
    identically for both the JSON-body and PDF-upload creation paths, so a
    document created one way and re-uploaded the other way is still
    recognized as the same content."""
    normalized = "\n".join(f"{s.get('heading', '')}\n{s.get('content', '')}" for s in sections)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
