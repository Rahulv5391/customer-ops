from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate, TicketEventCreate, TicketUpdate


def _make_customer(db):
    return customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )


def _make_ticket(db, customer_id, **overrides):
    data = {"customer_id": customer_id, "subject": "Order never arrived"}
    data.update(overrides)
    return ticket_crud.create_ticket(db, TicketCreate(**data))


def test_create_ticket_gets_a_generated_ticket_number(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    assert ticket.ticket_number.startswith("TCK-")
    assert ticket.status == "unassigned"  # schema default


def test_get_ticket_eager_loads_events(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    fetched = ticket_crud.get_ticket(db, ticket.id)
    assert fetched is not None
    assert fetched.events == []


def test_get_ticket_returns_none_for_missing_id(db):
    assert ticket_crud.get_ticket(db, "does-not-exist") is None


def test_list_tickets_filters_by_channel_and_status(db):
    customer = _make_customer(db)
    _make_ticket(db, customer.id, channel="email", status="unassigned")
    _make_ticket(db, customer.id, channel="chat", status="in_progress")

    email_tickets = ticket_crud.list_tickets(db, channel="email")
    assert len(email_tickets) == 1
    assert email_tickets[0].channel == "email"

    in_progress = ticket_crud.list_tickets(db, status="in_progress")
    assert len(in_progress) == 1
    assert in_progress[0].channel == "chat"


def test_list_tickets_filters_by_customer_id(db):
    customer_a = _make_customer(db)
    customer_b = customer_crud.create_customer(
        db, CustomerCreate(full_name="Grace Hopper", email="grace@example.com")
    )
    _make_ticket(db, customer_a.id)
    _make_ticket(db, customer_b.id)

    for_a = ticket_crud.list_tickets(db, customer_id=customer_a.id)
    assert len(for_a) == 1
    assert for_a[0].customer_id == customer_a.id


def test_update_ticket_only_changes_provided_fields(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    updated = ticket_crud.update_ticket(db, ticket, TicketUpdate(status="resolved"))
    assert updated.status == "resolved"
    assert updated.subject == "Order never arrived"  # untouched


def test_add_ticket_event_sets_actor_and_persists(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    event = ticket_crud.add_ticket_event(
        db,
        ticket_id=ticket.id,
        actor="Jordan Lee",
        data=TicketEventCreate(event_type="note", detail="Called the customer back."),
    )
    assert event.actor == "Jordan Lee"
    assert event.ticket_id == ticket.id

    fetched = ticket_crud.get_ticket(db, ticket.id)
    assert len(fetched.events) == 1
    assert fetched.events[0].detail == "Called the customer back."
