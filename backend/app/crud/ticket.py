from sqlalchemy.orm import Session, selectinload

from app.models.ticket import Ticket, TicketEvent
from app.schemas.ticket import TicketCreate, TicketEventCreate, TicketUpdate


def get_ticket(db: Session, ticket_id: str) -> Ticket | None:
    return (
        db.query(Ticket)
        .options(selectinload(Ticket.events))
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
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, ticket: Ticket, updates: TicketUpdate) -> Ticket:
    for field, value in updates.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


def add_ticket_event(db: Session, ticket_id: str, data: TicketEventCreate) -> TicketEvent:
    event = TicketEvent(ticket_id=ticket_id, **data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
