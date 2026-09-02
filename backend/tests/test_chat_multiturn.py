"""End-to-end proof that conversation history actually reaches the LLM: the
exact motivating scenario from the bug report - "I want to raise an
escalation" followed by an elliptical follow-up that only makes sense in
light of the first message - hitting POST /chat twice with the same
session_id."""

from unittest.mock import AsyncMock

import pytest

from app.agents.escalation_agent import EscalationAgentOutput, escalation_agent
from app.agents.router_agent import RouterOutput, router_agent
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate


@pytest.fixture(autouse=True)
def _mock_router(monkeypatch):
    mock = AsyncMock(return_value=RouterOutput(category="escalation"))
    monkeypatch.setattr(router_agent._sub_agent, "run", mock)
    return mock


@pytest.fixture(autouse=True)
def _mock_escalation_llm(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(escalation_agent._sub_agent, "run", mock)
    return mock


def test_second_turn_prompt_includes_the_first_turns_exchange(
    client, agent_headers, db, _mock_escalation_llm
):
    customer = customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )
    ticket = ticket_crud.create_ticket(
        db, TicketCreate(customer_id=customer.id, subject="Order never arrived")
    )
    session_id = "33333333-3333-3333-3333-333333333333"

    # Turn 1: vague - the agent has to ask a clarifying question.
    _mock_escalation_llm.return_value = EscalationAgentOutput(
        escalation_type=None, requested_action=None
    )
    r1 = client.post(
        "/api/v1/chat",
        json={"message": "I want to raise an escalation", "session_id": session_id},
        headers=agent_headers,
    )
    assert r1.status_code == 200
    first_reply = r1.json()["messages"][0]["content"]
    assert first_reply  # a real clarifying question was returned

    # Turn 2: on its own this message names an amount and a ticket, but not
    # what the ask actually is - the whole point of history is that the LLM
    # sees turn 1 alongside it. Assert on the prompt text that reached the
    # second LLM call, not just on the final proposal.
    _mock_escalation_llm.return_value = EscalationAgentOutput(
        escalation_type="refund_approval",
        requested_action="Refund $1000 for the order.",
        ticket_hint=ticket.ticket_number,
        requested_amount=1000,
    )
    r2 = client.post(
        "/api/v1/chat",
        json={"message": f"refund of $1000 for ticket {ticket.ticket_number}", "session_id": session_id},
        headers=agent_headers,
    )
    assert r2.status_code == 200

    assert _mock_escalation_llm.call_count == 2
    second_prompt = _mock_escalation_llm.call_args_list[1].args[0]
    assert "I want to raise an escalation" in second_prompt
    assert first_reply in second_prompt
    assert f"refund of $1000 for ticket {ticket.ticket_number}" in second_prompt

    # And the actual proposal from turn 2 correctly resolved the ticket.
    second_reply = r2.json()["messages"][0]
    assert second_reply["pending_action"]["escalation_payload"]["ticket_id"] == ticket.id


def test_a_different_agent_cannot_read_another_agents_session(
    client, agent_headers, lead_headers, db, _mock_escalation_llm
):
    _mock_escalation_llm.return_value = EscalationAgentOutput(
        escalation_type=None, requested_action=None
    )
    session_id = "44444444-4444-4444-4444-444444444444"
    client.post(
        "/api/v1/chat",
        json={"message": "hello", "session_id": session_id},
        headers=agent_headers,
    )
    r = client.post(
        "/api/v1/chat",
        json={"message": "hello again", "session_id": session_id},
        headers=lead_headers,
    )
    assert r.status_code == 403
