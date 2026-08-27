from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import kb_document as kb_crud
from app.models.agent import SupportAgent
from app.schemas.kb_document import KBDocumentCreate, KBDocumentResponse, KBDocumentUpdate
from app.services import rag_service
from app.services.auth_service import get_current_agent

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


@router.post("", response_model=KBDocumentResponse, status_code=201)
def create_document(
    payload: KBDocumentCreate,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    document = kb_crud.create_document(db, payload)
    rag_service.ingest_document(document)
    return document


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
    updated = kb_crud.update_document(db, document, payload)
    rag_service.ingest_document(updated)
    return updated


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
    """Direct RAG search, bypassing chat - for admin/testing use, not the
    chat orchestration path (Architecture.md §6). Requires authentication
    like every other endpoint in this app (Architecture.md's Auth Design
    originally left this "optional" - resolved to require auth for
    consistency, since no other public surface exists yet)."""
    return rag_service.search(payload.query)
