from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.escalation import Escalation
from app.schemas.escalation import EscalationCreate


def get_escalation(db: Session, escalation_id: str) -> Escalation | None:
    return db.get(Escalation, escalation_id)


def list_escalations(
    db: Session,
    status: str | None = None,
    priority: str | None = None,
    escalation_type: str | None = None,
    ticket_id: str | None = None,
) -> list[Escalation]:
    q = db.query(Escalation)
    if status:
        q = q.filter(Escalation.status == status)
    if priority:
        q = q.filter(Escalation.priority == priority)
    if escalation_type:
        q = q.filter(Escalation.escalation_type == escalation_type)
    if ticket_id:
        q = q.filter(Escalation.ticket_id == ticket_id)
    return q.order_by(Escalation.created_at.desc()).all()


def create_escalation(db: Session, data: EscalationCreate, requested_by: str) -> Escalation:
    escalation = Escalation(**data.model_dump(), requested_by=requested_by)
    db.add(escalation)
    db.commit()
    db.refresh(escalation)
    return escalation


def resolve_escalation(
    db: Session, escalation: Escalation, status: str, rejection_note: str | None = None
) -> Escalation:
    escalation.status = status
    escalation.rejection_note = rejection_note
    escalation.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(escalation)
    return escalation
