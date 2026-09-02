"""Tests lookup_tools functions directly - same technique as
test_mutation_tools.py. Every one of these is a pure read, so there's no
proposal/token to check - just the terminal ChatMessage each tool builds."""

from app.agents.tools import lookup_tools
from app.agents.tools.base import ALREADY_SHOWN
from app.core.security import hash_password
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.models.agent import SupportAgent
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate


def _make_customer(db, **overrides):
    data = {"full_name": "Ada Lovelace", "email": "ada@example.com"}
    data.update(overrides)
    return customer_crud.create_customer(db, CustomerCreate(**data))


def _make_ticket(db, customer_id, **overrides):
    data = {"customer_id": customer_id, "subject": "Order never arrived"}
    data.update(overrides)
    return ticket_crud.create_ticket(db, TicketCreate(**data))


def _make_agent(db, full_name="Priya Nair", email="priya.test@example.com"):
    agent = SupportAgent(full_name=full_name, email=email, password_hash=hash_password("password123"))
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def _tools(db):
    outcomes = []
    built = {fn.__name__: fn for fn in lookup_tools.build_tools(db, outcomes)}
    return built, outcomes


# --- query_records ---


def test_query_records_formats_a_single_row_as_labeled_fields(db):
    customer = _make_customer(db)
    tools, outcomes = _tools(db)

    result = tools["query_records"](
        sql_query=f"SELECT id, full_name, email FROM customers WHERE id = '{customer.id}'"
    )

    assert result == ALREADY_SHOWN
    msg = outcomes[0].chat_message
    assert msg.type == "text"
    assert "Ada Lovelace" in msg.content
    assert customer.id not in msg.content  # the raw id column is dropped from display


def test_query_records_rejects_a_write_statement(db):
    tools, outcomes = _tools(db)
    tools["query_records"](sql_query="DELETE FROM customers")
    assert outcomes[0].chat_message.type == "error"


def test_query_records_no_rows_says_so(db):
    tools, outcomes = _tools(db)
    tools["query_records"](sql_query="SELECT id FROM customers WHERE id = 'nope'")
    assert "no matching records" in outcomes[0].chat_message.content.lower()


# --- find_customer ---


def test_find_customer_returns_a_profile(db):
    customer = _make_customer(db, company="Acme Co")
    tools, outcomes = _tools(db)

    tools["find_customer"](customer_hint=customer.email)

    msg = outcomes[0].chat_message
    assert "Ada Lovelace" in msg.content
    assert "Acme Co" in msg.content


def test_find_customer_not_found(db):
    tools, outcomes = _tools(db)
    tools["find_customer"](customer_hint="nobody@example.com")
    assert "couldn't find" in outcomes[0].chat_message.content.lower()


def test_find_customer_ambiguous_name(db):
    _make_customer(db, full_name="Carla Jensen", email="carla1@example.com")
    _make_customer(db, full_name="Carla Jensen", email="carla2@example.com")
    tools, outcomes = _tools(db)

    tools["find_customer"](customer_hint="Carla Jensen")

    assert "more than one" in outcomes[0].chat_message.content.lower()


def test_find_customer_with_history_lists_orders_and_tickets(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    tools, outcomes = _tools(db)

    tools["find_customer"](customer_hint=customer.email, include_history=True)

    content = outcomes[0].chat_message.content
    assert "order/ticket history" in content
    assert ticket.ticket_number in content


# --- check_queue_availability ---


def test_check_queue_availability_reports_counts(db):
    customer = _make_customer(db)
    _make_ticket(db, customer.id, status="unassigned")
    tools, outcomes = _tools(db)

    tools["check_queue_availability"]()

    content = outcomes[0].chat_message.content
    assert "Agents online" in content
    assert "Unassigned tickets: 1" in content


def test_check_queue_availability_with_details_lists_tickets(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id, status="unassigned")
    tools, outcomes = _tools(db)

    tools["check_queue_availability"](include_details=True)

    assert ticket.ticket_number in outcomes[0].chat_message.content


# --- get_reporting_metric ---


def test_get_reporting_metric_tickets_resolved_today(db):
    tools, outcomes = _tools(db)
    tools["get_reporting_metric"](metric="tickets_resolved_today")
    assert "Tickets resolved today" in outcomes[0].chat_message.content


def test_get_reporting_metric_defaults_to_summary(db):
    tools, outcomes = _tools(db)
    tools["get_reporting_metric"]()
    assert "Ticket volume" in outcomes[0].chat_message.content
