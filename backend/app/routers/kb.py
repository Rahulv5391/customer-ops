from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import kb_document as kb_crud
from app.models.agent import SupportAgent
from app.schemas.kb_document import KBDocumentResponse
from app.services.auth_service import get_current_agent

# POST/PATCH/DELETE and /kb/search are deliberately deferred to Phase 5 -
# writes need to re-ingest into Chroma via rag_service.py, which doesn't
# exist yet (Architecture.md §9, Phase 5).
router = APIRouter(prefix="/kb", tags=["kb"])


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
