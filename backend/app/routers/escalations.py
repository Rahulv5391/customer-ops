from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import escalation as escalation_crud
from app.models.agent import SupportAgent
from app.schemas.escalation import EscalationResolve, EscalationResponse
from app.services import audit_service
from app.services.auth_service import get_current_agent, require_team_lead

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


@router.patch("/{escalation_id}", response_model=EscalationResponse)
def resolve_escalation(
    escalation_id: str,
    payload: EscalationResolve,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(require_team_lead),
):
    escalation = escalation_crud.get_escalation(db, escalation_id)
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    if payload.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="status must be 'approved' or 'rejected'")

    updated = escalation_crud.resolve_escalation(db, escalation, payload.status, payload.rejection_note)
    audit_service.record_activity(
        db,
        actor=agent.full_name,
        action_type="resolve_escalation",
        entity_type="escalation",
        entity_id=updated.id,
        summary=f"{payload.status.capitalize()} escalation {updated.escalation_number}",
    )
    return updated
