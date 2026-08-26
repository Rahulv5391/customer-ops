from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import escalation as escalation_crud
from app.models.agent import SupportAgent
from app.schemas.escalation import EscalationResponse
from app.services.auth_service import get_current_agent

# PATCH /escalations/{id} (approve/reject) is deliberately deferred to
# Phase 4 - it needs audit_service.py and the team_lead-only enforcement
# path that ships alongside it (Architecture.md §9, Phase 4).
router = APIRouter(prefix="/escalations", tags=["escalations"])


@router.get("", response_model=list[EscalationResponse])
def list_escalations(
    status: str | None = None,
    priority: str | None = None,
    escalation_type: str | None = None,
    ticket_id: str | None = None,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return escalation_crud.list_escalations(
        db,
        status=status,
        priority=priority,
        escalation_type=escalation_type,
        ticket_id=ticket_id,
    )


@router.get("/{escalation_id}", response_model=EscalationResponse)
def get_escalation(
    escalation_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    escalation = escalation_crud.get_escalation(db, escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return escalation
