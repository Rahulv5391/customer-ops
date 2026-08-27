import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import kb_document as kb_crud
from app.models.agent import SupportAgent
from app.models.kb_document import KBDocument
from app.schemas.kb_document import KBDocumentResponse, KBDocumentUpdate
from app.services import rag_service
from app.services.auth_service import get_current_agent
from app.services.document_extraction import compute_content_hash, extract_pdf_sections

router = APIRouter(prefix="/kb", tags=["kb"])


class KBSearchRequest(BaseModel):
    query: str


class KBSearchHit(BaseModel):
    text: str
    similarity: float
    document_title: str
    version: str
    source_updated_at: str
    section: str


def _create_and_ingest(
    db: Session,
    *,
    title: str,
    category: str,
    version: str,
    source_updated_at: str,
    sections: list[dict],
    source_filename: str | None,
) -> KBDocument:
    """Creates a KB document and ingests it into Chroma. Commits only if
    ingestion succeeds; rolls back the DB insert otherwise."""
    content_hash = compute_content_hash(sections)
    existing = kb_crud.get_by_content_hash(db, content_hash)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This content is already ingested as document "
                f"'{existing.title}' (id={existing.id}) - update that document instead."
            ),
        )

    document = KBDocument(
        title=title,
        category=category,
        version=version,
        source_updated_at=source_updated_at,
        content_json=json.dumps({"sections": sections}),
        source_filename=source_filename,
        content_hash=content_hash,
    )
    db.add(document)
    db.flush()
    try:
        rag_service.ingest_document(document)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to ingest document into the knowledge base: {exc}"
        )
    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=list[KBDocumentResponse])
def list_documents(
    category: str | None = None,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return kb_crud.list_documents(db, category=category)


@router.get("/{document_id}", response_model=KBDocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    document = kb_crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/upload", response_model=KBDocumentResponse, status_code=201)
def upload_document(
    title: str = Form(...),
    category: str = Form("faq"),
    version: str = Form("v1"),
    source_updated_at: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    """Creates a KB document from an uploaded PDF. Duplicate detection is
    based on content hash, not filename."""
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    sections = extract_pdf_sections(file.file.read())
    if not sections:
        raise HTTPException(status_code=400, detail="No extractable text found in this PDF")

    return _create_and_ingest(
        db,
        title=title,
        category=category,
        version=version,
        source_updated_at=source_updated_at,
        sections=sections,
        source_filename=file.filename,
    )


@router.patch("/{document_id}", response_model=KBDocumentResponse)
def update_document(
    document_id: str,
    payload: KBDocumentUpdate,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    document = kb_crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    # Metadata only - content changes go through PATCH /kb/{id}/upload.
    return kb_crud.update_document(db, document, payload)


@router.patch("/{document_id}/upload", response_model=KBDocumentResponse)
def upload_document_update(
    document_id: str,
    version: str | None = Form(None),
    source_updated_at: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    """Re-ingests a new PDF into an existing document id."""
    document = kb_crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    sections = extract_pdf_sections(file.file.read())
    if not sections:
        raise HTTPException(status_code=400, detail="No extractable text found in this PDF")

    new_hash = compute_content_hash(sections)
    if new_hash == document.content_hash:
        # Same content already ingested - nothing to do.
        return document

    conflict = kb_crud.get_by_content_hash(db, new_hash)
    if conflict and conflict.id != document.id:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This content is already ingested as document "
                f"'{conflict.title}' (id={conflict.id})."
            ),
        )

    document.content_hash = new_hash
    document.content_json = json.dumps({"sections": sections})
    document.source_filename = file.filename
    if version is not None:
        document.version = version
    if source_updated_at is not None:
        document.source_updated_at = source_updated_at

    db.flush()
    try:
        rag_service.ingest_document(document)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to re-ingest document into the knowledge base: {exc}"
        )
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    document = kb_crud.get_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    rag_service.remove_document(document_id)
    kb_crud.delete_document(db, document)


@router.post("/search", response_model=list[KBSearchHit])
def search_kb(
    payload: KBSearchRequest,
    _agent: SupportAgent = Depends(get_current_agent),
):
    """Direct knowledge base search, bypassing chat."""
    return rag_service.search(payload.query)
