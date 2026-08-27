from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import EntityNotFoundError
from app.crud import agent as agent_crud
from app.crud import customer as customer_crud
from app.crud import escalation as escalation_crud
from app.crud import ticket as ticket_crud
from app.models.customer import Customer
from app.models.escalation import Escalation
from app.models.ticket import Ticket
from app.schemas.customer import CustomerUpdate
from app.schemas.escalation import EscalationCreate
from app.schemas.ticket import TicketEventCreate, TicketUpdate
from app.services import audit_service

# Customer fields that can be updated through chat.
ALLOWED_CUSTOMER_FIELDS = set(CustomerUpdate.model_fields.keys())

# Maps common field phrasing (e.g. "mobile number") to the real column name.
_FIELD_ALIASES = {
    "name": "full_name",
    "customer name": "full_name",
    "email address": "email",
    "e-mail": "email",
    "phone number": "phone",
    "mobile": "phone",
    "mobile number": "phone",
    "cell": "phone",
    "cell number": "phone",
    "cell phone": "phone",
    "telephone": "phone",
    "telephone number": "phone",
    "contact number": "phone",
    "employer": "company",
    "organization": "company",
    "organisation": "company",
    "tier": "account_tier",
    "plan": "account_tier",
    "account tier": "account_tier",
    "address": "address_line1",
    "street address": "address_line1",
    "address 1": "address_line1",
    "apartment": "address_line2",
    "suite": "address_line2",
    "address 2": "address_line2",
    "state": "region",
    "province": "region",
    "zip": "postal_code",
    "zip code": "postal_code",
    "zipcode": "postal_code",
    "account status": "status",
}

# Escalation types that can be auto-approved based on a dollar/percent amount.
_AMOUNT_BASED_ESCALATION_TYPES = {"account_credit", "refund_approval"}

# Human-readable labels for ALLOWED_CUSTOMER_FIELDS.
CUSTOMER_FIELD_LABELS = {
    "full_name": "full name",
    "email": "email",
    "phone": "phone",
    "company": "company",
    "account_tier": "account tier",
    "address_line1": "address",
    "address_line2": "address line 2",
    "city": "city",
    "region": "region/state",
    "postal_code": "postal/zip code",
    "country": "country",
    "status": "status",
}


def normalize_customer_field(field_name: str | None) -> str | None:
    """Map free-text field wording to a real Customer column name, or None
    if it doesn't match anything writable."""
    if not field_name:
        return None
    key = field_name.strip().lower()
    if key in ALLOWED_CUSTOMER_FIELDS:
        return key
    underscored = key.replace(" ", "_").replace("-", "_")
    if underscored in ALLOWED_CUSTOMER_FIELDS:
        return underscored
    return _FIELD_ALIASES.get(key)


def update_customer_field(
    db: Session, customer_id: str, field_name: str, field_value: str, actor: str
) -> Customer:
    customer = customer_crud.get_customer(db, customer_id)
    if not customer:
        raise EntityNotFoundError(f"Customer {customer_id} not found")
    normalized_field = normalize_customer_field(field_name)
    if normalized_field is None:
        raise ValueError(f"Field '{field_name}' cannot be updated through chat")
    field_name = normalized_field

    before_value = getattr(customer, field_name)
    updated = customer_crud.update_customer(db, customer, {field_name: field_value})
    audit_service.record_activity(
        db,
        actor=actor,
        action_type="update_field",
        entity_type="customer",
        entity_id=customer.id,
        summary=f"Changed {field_name} from '{before_value}' to '{field_value}'",
    )
    return updated


def reassign_ticket(db: Session, ticket_id: str, target_agent_id: str, actor: str) -> Ticket:
    ticket = ticket_crud.get_ticket(db, ticket_id)
    if not ticket:
        raise EntityNotFoundError(f"Ticket {ticket_id} not found")
    target_agent = agent_crud.get_agent(db, target_agent_id)
    if not target_agent:
        raise EntityNotFoundError(f"Agent {target_agent_id} not found")

    updated = ticket_crud.update_ticket(db, ticket, TicketUpdate(assigned_agent_id=target_agent_id))
    ticket_crud.add_ticket_event(
        db,
        ticket_id=ticket.id,
        actor=actor,
        data=TicketEventCreate(
            event_type="reassignment", detail=f"Reassigned to {target_agent.full_name}"
        ),
    )
    audit_service.record_activity(
        db,
        actor=actor,
        action_type="reassign_ticket",
        entity_type="ticket",
        entity_id=ticket.id,
        summary=f"Reassigned ticket {ticket.ticket_number} to {target_agent.full_name}",
    )
    return updated


def schedule_callback(db: Session, ticket_id: str, callback_time: str, actor: str) -> Ticket:
    ticket = ticket_crud.get_ticket(db, ticket_id)
    if not ticket:
        raise EntityNotFoundError(f"Ticket {ticket_id} not found")

    # Callbacks are recorded as a ticket event, not a separate entity.
    ticket_crud.add_ticket_event(
        db,
        ticket_id=ticket.id,
        actor=actor,
        data=TicketEventCreate(
            event_type="note", detail=f"Callback scheduled for {callback_time}"
        ),
    )
    audit_service.record_activity(
        db,
        actor=actor,
        action_type="schedule_callback",
        entity_type="ticket",
        entity_id=ticket.id,
        summary=f"Scheduled callback on ticket {ticket.ticket_number} for {callback_time}",
    )
    return ticket


def create_escalation(db: Session, payload: dict, requested_by: str) -> Escalation:
    payload = dict(payload)
    requested_amount = payload.pop("requested_amount", None)

    data = EscalationCreate(**payload)
    escalation = escalation_crud.create_escalation(db, data, requested_by)

    if (
        data.escalation_type in _AMOUNT_BASED_ESCALATION_TYPES
        and requested_amount is not None
        and requested_amount <= settings.auto_approval_threshold_pct
    ):
        escalation = escalation_crud.resolve_escalation(db, escalation, status="approved")

    audit_service.record_activity(
        db,
        actor=requested_by,
        action_type="create_escalation",
        entity_type="escalation",
        entity_id=escalation.id,
        summary=f"Filed {escalation.escalation_type} escalation ({escalation.status})",
    )
    return escalation
