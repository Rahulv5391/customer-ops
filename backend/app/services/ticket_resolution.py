from sqlalchemy.orm import Session

from app.crud.ticket import list_tickets
from app.models.ticket import Ticket


def resolve_ticket_context(db: Session, ticket_hint: str | None) -> Ticket | None:
    """Matches a free-text ticket number/id hint extracted from the chat
    message. Multi-turn context (e.g. a ticket named earlier in the
    conversation) reaches this the same way - the LLM re-states the hint
    from the conversation history baked into its prompt, it isn't tracked
    out-of-band."""
    if not ticket_hint:
        return None
    normalized = ticket_hint.strip().lower()
    for ticket in list_tickets(db):
        if ticket.id.lower() == normalized or ticket.ticket_number.lower() == normalized:
            return ticket
    return None
