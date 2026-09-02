from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate
from app.services.ticket_resolution import resolve_ticket_context


def _make_customer(db):
    return customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )


def _make_ticket(db, customer_id, **overrides):
    data = {"customer_id": customer_id, "subject": "Order never arrived"}
    data.update(overrides)
    return ticket_crud.create_ticket(db, TicketCreate(**data))


def test_falls_back_to_ticket_number_hint(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)

    result = resolve_ticket_context(db, ticket_hint=ticket.ticket_number)
    assert result.id == ticket.id


def test_hint_matches_case_insensitively(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)

    result = resolve_ticket_context(db, ticket_hint=ticket.ticket_number.lower())
    assert result.id == ticket.id


def test_hint_matches_raw_id_too(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)

    result = resolve_ticket_context(db, ticket_hint=ticket.id)
    assert result.id == ticket.id


def test_no_hint_returns_none(db):
    assert resolve_ticket_context(db, ticket_hint=None) is None


def test_unmatched_hint_returns_none(db):
    assert resolve_ticket_context(db, ticket_hint="TCK-NOPE") is None
