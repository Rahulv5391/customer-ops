"""Tests the propose -> confirm write flow directly via create_action_token,
without going through the LLM classification step."""

from app.core.security import hash_password
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.models.agent import SupportAgent
from app.models.audit_log import ActivityLog
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate
from app.services.action_token import create_action_token


def _make_customer(db):
    return customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )


def _make_ticket(db, customer_id):
    return ticket_crud.create_ticket(
        db, TicketCreate(customer_id=customer_id, subject="Order never arrived")
    )


def _make_agent(db, email="other.agent@example.com"):
    agent = SupportAgent(
        full_name="Other Agent", email=email, password_hash=hash_password("password123")
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def test_create_ticket_confirm_lands_the_ticket(client, agent_headers, db):
    customer = _make_customer(db)
    token = create_action_token(
        action_type="create_ticket",
        entity_type="customer",
        entity_id=customer.id,
        mutation_payload={
            "customer_id": customer.id,
            "subject": "Can't reset my password",
            "channel": "chat",
            "priority": "high",
            "category": "account_access",
        },
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 200
    assert r.json()["entity"]["subject"] == "Can't reset my password"
    assert r.json()["entity"]["customer_id"] == customer.id

    entries = db.query(ActivityLog).filter(ActivityLog.entity_id == r.json()["entity"]["id"]).all()
    assert any(e.action_type == "create_ticket" for e in entries)


def test_create_ticket_nonexistent_customer_returns_404(client, agent_headers):
    token = create_action_token(
        action_type="create_ticket",
        entity_type="customer",
        entity_id="does-not-exist",
        mutation_payload={"customer_id": "does-not-exist", "subject": "Test"},
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 404


def test_update_field_confirm_lands_the_change(client, agent_headers, db):
    customer = _make_customer(db)
    token = create_action_token(
        action_type="update_field",
        entity_type="customer",
        entity_id=customer.id,
        field_name="phone",
        field_value="+1-555-0100",
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 200
    assert r.json()["entity"]["phone"] == "+1-555-0100"


def test_update_field_disallowed_field_returns_400(client, agent_headers, db):
    customer = _make_customer(db)
    token = create_action_token(
        action_type="update_field",
        entity_type="customer",
        entity_id=customer.id,
        field_name="id",
        field_value="hacked",
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 400


def test_update_field_nonexistent_customer_returns_404(client, agent_headers):
    token = create_action_token(
        action_type="update_field",
        entity_type="customer",
        entity_id="does-not-exist",
        field_name="phone",
        field_value="+1-555-0100",
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 404


def test_reassign_ticket_confirm_lands_the_change(client, agent_headers, db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    target_agent = _make_agent(db)

    token = create_action_token(
        action_type="reassign_ticket",
        entity_type="ticket",
        entity_id=ticket.id,
        field_name="assigned_agent_id",
        field_value=target_agent.id,
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 200
    assert r.json()["entity"]["assigned_agent_id"] == target_agent.id

    fetched = ticket_crud.get_ticket(db, ticket.id)
    assert any("Reassigned to" in e.detail for e in fetched.events)


def test_reassign_ticket_nonexistent_agent_returns_404(client, agent_headers, db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    token = create_action_token(
        action_type="reassign_ticket",
        entity_type="ticket",
        entity_id=ticket.id,
        field_name="assigned_agent_id",
        field_value="does-not-exist",
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 404


def test_schedule_callback_confirm_writes_a_ticket_event(client, agent_headers, db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    token = create_action_token(
        action_type="schedule_callback",
        entity_type="ticket",
        entity_id=ticket.id,
        field_value="tomorrow at 3pm",
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 200

    fetched = ticket_crud.get_ticket(db, ticket.id)
    assert any("tomorrow at 3pm" in e.detail for e in fetched.events)


def test_create_escalation_under_threshold_is_auto_approved(client, agent_headers, db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    token = create_action_token(
        action_type="create_escalation",
        entity_type="ticket",
        entity_id=ticket.id,
        mutation_payload={
            "escalation_type": "account_credit",
            "requested_action": "Issue a $5 credit.",
            "priority": "low",
            "ticket_id": ticket.id,
            "policy_citation": None,
            "requested_amount": 5,
        },
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 200
    assert r.json()["entity"]["status"] == "approved"

    # Filing an escalation must show up on the ticket's own timeline, not
    # just the global audit log - otherwise there's no way to tell, from
    # the ticket itself, whether one was ever filed against it.
    fetched = ticket_crud.get_ticket(db, ticket.id)
    escalated_events = [e for e in fetched.events if e.event_type == "escalated"]
    assert len(escalated_events) == 1
    assert "auto-approved" in escalated_events[0].detail


def test_create_escalation_over_threshold_stays_pending(client, agent_headers, db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    token = create_action_token(
        action_type="create_escalation",
        entity_type="ticket",
        entity_id=ticket.id,
        mutation_payload={
            "escalation_type": "account_credit",
            "requested_action": "Issue a $500 credit.",
            "priority": "high",
            "ticket_id": ticket.id,
            "policy_citation": None,
            "requested_amount": 500,
        },
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)
    assert r.status_code == 200
    assert r.json()["entity"]["status"] == "pending"

    fetched = ticket_crud.get_ticket(db, ticket.id)
    escalated_events = [e for e in fetched.events if e.event_type == "escalated"]
    assert len(escalated_events) == 1
    assert "auto-approved" not in escalated_events[0].detail


def test_tampered_token_is_rejected(client, agent_headers, db):
    customer = _make_customer(db)
    token = create_action_token(
        action_type="update_field",
        entity_type="customer",
        entity_id=customer.id,
        field_name="phone",
        field_value="+1-555-0100",
    )
    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    r = client.post("/api/v1/chat/action/confirm", json={"token": tampered}, headers=agent_headers)
    assert r.status_code == 400


def test_garbage_token_is_rejected(client, agent_headers):
    r = client.post(
        "/api/v1/chat/action/confirm", json={"token": "not-a-real-token"}, headers=agent_headers
    )
    assert r.status_code == 400


def test_confirm_requires_auth(client, db):
    customer = _make_customer(db)
    token = create_action_token(
        action_type="update_field",
        entity_type="customer",
        entity_id=customer.id,
        field_name="phone",
        field_value="+1-555-0100",
    )
    r = client.post("/api/v1/chat/action/confirm", json={"token": token})
    assert r.status_code == 401


def test_confirmed_mutation_writes_an_activity_log_entry(client, agent_headers, db):
    customer = _make_customer(db)
    token = create_action_token(
        action_type="update_field",
        entity_type="customer",
        entity_id=customer.id,
        field_name="phone",
        field_value="+1-555-0100",
    )
    client.post("/api/v1/chat/action/confirm", json={"token": token}, headers=agent_headers)

    entries = db.query(ActivityLog).filter(ActivityLog.entity_id == customer.id).all()
    assert any(e.action_type == "update_field" for e in entries)
