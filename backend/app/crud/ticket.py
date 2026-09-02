from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.models.ticket import Ticket, TicketEvent
from app.schemas.ticket import TicketCreate, TicketEventCreate, TicketUpdate

# Mirrors analytics_service._RESOLVED_STATUSES - kept as a local constant
# (not imported) to avoid crud depending on the services layer.
_RESOLVED_STATUSES = {"resolved", "closed"}


def get_ticket(db: Session, ticket_id: str) -> Ticket | None:
    return (
        db.query(Ticket)
        .options(selectinload(Ticket.events), selectinload(Ticket.customer))
        .filter(Ticket.id == ticket_id)
        .first()
    )


def list_tickets(
    db: Session,
    channel: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    assigned_agent_id: str | None = None,
    customer_id: str | None = None,
) -> list[Ticket]:
    q = db.query(Ticket)
    if channel:
        q = q.filter(Ticket.channel == channel)
    if status:
        q = q.filter(Ticket.status == status)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if assigned_agent_id:
        q = q.filter(Ticket.assigned_agent_id == assigned_agent_id)
    if customer_id:
        q = q.filter(Ticket.customer_id == customer_id)
    return q.order_by(Ticket.created_at.desc()).all()


def create_ticket(db: Session, data: TicketCreate) -> Ticket:
    ticket = Ticket(**data.model_dump())
    if ticket.status in _RESOLVED_STATUSES:
        ticket.resolved_at = datetime.now(timezone.utc)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, ticket: Ticket, updates: TicketUpdate) -> Ticket:
    changes = updates.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is not None:
            setattr(ticket, field, value)

    # analytics (tickets_resolved_today, avg_resolution_time_hours) reads
    # resolved_at directly - nothing else in the app ever stamped it, so a
    # ticket marked resolved through the UI/API never showed up there.
    # Stamp it on the transition into resolved/closed (never overwrite an
    # existing resolution time on a redundant re-save), and clear it if the
    # ticket gets reopened.
    new_status = changes.get("status")
    if new_status is not None:
        if new_status in _RESOLVED_STATUSES and ticket.resolved_at is None:
            ticket.resolved_at = datetime.now(timezone.utc)
        elif new_status not in _RESOLVED_STATUSES:
            ticket.resolved_at = None

    db.commit()
    db.refresh(ticket)
    return ticket


def add_ticket_event(db: Session, ticket_id: str, actor: str, data: TicketEventCreate) -> TicketEvent:
    event = TicketEvent(ticket_id=ticket_id, actor=actor, **data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
