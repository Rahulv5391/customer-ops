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


def test_update_ticket_to_resolved_stamps_resolved_at(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    assert ticket.resolved_at is None

    updated = ticket_crud.update_ticket(db, ticket, TicketUpdate(status="resolved"))
    assert updated.resolved_at is not None


def test_update_ticket_to_closed_also_stamps_resolved_at(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    updated = ticket_crud.update_ticket(db, ticket, TicketUpdate(status="closed"))
    assert updated.resolved_at is not None


def test_re_saving_the_same_resolved_status_does_not_bump_resolved_at(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    first = ticket_crud.update_ticket(db, ticket, TicketUpdate(status="resolved"))
    first_resolved_at = first.resolved_at

    # e.g. a second PATCH that also happens to include status=resolved
    # (unchanged) alongside another field - shouldn't reset the clock.
    again = ticket_crud.update_ticket(db, first, TicketUpdate(status="resolved", priority="high"))
    assert again.resolved_at == first_resolved_at


def test_reopening_a_resolved_ticket_clears_resolved_at(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    resolved = ticket_crud.update_ticket(db, ticket, TicketUpdate(status="resolved"))
    assert resolved.resolved_at is not None

    reopened = ticket_crud.update_ticket(db, resolved, TicketUpdate(status="in_progress"))
    assert reopened.resolved_at is None


def test_update_ticket_without_a_status_change_leaves_resolved_at_untouched(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    resolved = ticket_crud.update_ticket(db, ticket, TicketUpdate(status="resolved"))

    reassigned = ticket_crud.update_ticket(db, resolved, TicketUpdate(priority="urgent"))
    assert reassigned.resolved_at == resolved.resolved_at


def test_create_ticket_pre_resolved_stamps_resolved_at_immediately(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id, status="resolved")
    assert ticket.resolved_at is not None


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
