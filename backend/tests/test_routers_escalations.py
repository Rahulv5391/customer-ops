from app.crud import customer as customer_crud
from app.crud import escalation as escalation_crud
from app.crud import ticket as ticket_crud
from app.schemas.customer import CustomerCreate
from app.schemas.escalation import EscalationCreate
from app.schemas.ticket import TicketCreate


def _make_customer(db):
    return customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )


def _make_ticket(db, customer_id):
    return ticket_crud.create_ticket(
        db, TicketCreate(customer_id=customer_id, subject="Order never arrived")
    )


def _make_escalation(db, ticket_id, **overrides):
    data = {
        "escalation_type": "account_credit",
        "requested_action": "Issue a $500 credit.",
        "priority": "high",
        "ticket_id": ticket_id,
    }
    data.update(overrides)
    return escalation_crud.create_escalation(db, EscalationCreate(**data), requested_by="Sam Rivera")


def test_approving_an_escalation_adds_a_ticket_timeline_event(client, lead_headers, db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    escalation = _make_escalation(db, ticket.id)

    r = client.patch(
        f"/api/v1/escalations/{escalation.id}", json={"status": "approved"}, headers=lead_headers
    )
    assert r.status_code == 200

    fetched = ticket_crud.get_ticket(db, ticket.id)
    escalated_events = [e for e in fetched.events if e.event_type == "escalated"]
    assert len(escalated_events) == 1
    assert escalation.escalation_number in escalated_events[0].detail
    assert "approved" in escalated_events[0].detail


def test_rejecting_an_escalation_adds_a_ticket_timeline_event_with_the_reason(client, lead_headers, db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    escalation = _make_escalation(db, ticket.id)

    r = client.patch(
        f"/api/v1/escalations/{escalation.id}",
        json={"status": "rejected", "rejection_note": "Outside policy limits"},
        headers=lead_headers,
    )
    assert r.status_code == 200

    fetched = ticket_crud.get_ticket(db, ticket.id)
    escalated_events = [e for e in fetched.events if e.event_type == "escalated"]
    assert len(escalated_events) == 1
    assert "rejected" in escalated_events[0].detail
    assert "Outside policy limits" in escalated_events[0].detail


def test_resolving_an_escalation_with_no_ticket_does_not_error(client, lead_headers, db):
    escalation = escalation_crud.create_escalation(
        db,
        EscalationCreate(
            escalation_type="account_credit", requested_action="Issue a credit.", priority="low"
        ),
        requested_by="Sam Rivera",
    )

    r = client.patch(
        f"/api/v1/escalations/{escalation.id}", json={"status": "approved"}, headers=lead_headers
    )
    assert r.status_code == 200
