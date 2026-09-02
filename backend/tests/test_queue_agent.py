"""Tests queue_agent's reassign/callback logic directly, mocking the LLM
call - same technique as test_escalation_agent.py."""

from unittest.mock import AsyncMock

import pytest

from app.agents.queue_agent import QueueAgentOutput, queue_agent
from app.core.security import hash_password
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.models.agent import SupportAgent
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate


def _make_customer(db):
    return customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )


def _make_ticket(db, customer_id, **overrides):
    data = {"customer_id": customer_id, "subject": "Order never arrived"}
    data.update(overrides)
    return ticket_crud.create_ticket(db, TicketCreate(**data))


def _make_agent(db, full_name="Priya Nair", email="priya.test@example.com", team="billing"):
    agent = SupportAgent(
        full_name=full_name, email=email, password_hash=hash_password("password123"), team=team
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    mock = AsyncMock()
    monkeypatch.setattr(queue_agent._sub_agent, "run", mock)
    return mock


@pytest.mark.asyncio
async def test_reassign_diff_shows_agent_names_not_raw_ids(db, _mock_llm):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    target = _make_agent(db)
    _mock_llm.return_value = QueueAgentOutput(
        intent="reassign_ticket", ticket_hint=ticket.ticket_number, target_agent_id=target.id
    )

    result = await queue_agent.handle_message(db, target.full_name)

    assert result.type == "action-confirmation"
    assert result.action_diff.before == {"assigned_agent": "Unassigned"}
    assert result.action_diff.after == {"assigned_agent": target.full_name}
    # The token (not the display diff) is what's actually trusted on confirm.
    assert result.pending_action.field_value == target.id


@pytest.mark.asyncio
async def test_reassign_diff_shows_previous_agents_name_when_already_assigned(db, _mock_llm):
    customer = _make_customer(db)
    previous = _make_agent(db, full_name="Sam Rivera", email="sam.test@example.com")
    target = _make_agent(db, full_name="Priya Nair", email="priya.test2@example.com")
    ticket = _make_ticket(db, customer.id, assigned_agent_id=previous.id)
    _mock_llm.return_value = QueueAgentOutput(
        intent="reassign_ticket", ticket_hint=ticket.ticket_number, target_agent_id=target.id
    )

    result = await queue_agent.handle_message(db, target.full_name)

    assert result.action_diff.before == {"assigned_agent": "Sam Rivera"}
    assert result.action_diff.after == {"assigned_agent": "Priya Nair"}


@pytest.mark.asyncio
async def test_conversation_history_is_included_in_the_llm_prompt(db, _mock_llm):
    _mock_llm.return_value = QueueAgentOutput(intent="availability_check")
    history = "User: any billing agents free?\nAssistant: 2 of 5 are online."

    await queue_agent.handle_message(db, "and unassigned tickets?", history=history)

    prompt_sent = _mock_llm.call_args.args[0]
    assert history in prompt_sent
    assert "and unassigned tickets?" in prompt_sent
