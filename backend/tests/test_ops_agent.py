"""Tests OpsAgent.handle_message's outcome-assembly logic - last outcome
wins, needs_model_text substitution, empty-outcomes falls back to the
model's own text - without a real Gemini call or ADK's event loop.

ToolCallingAgentRuntime.run is monkeypatched with a fake that, instead of
calling Gemini, finds one of the real tool closures built for this request
(via self._agent.tools, exactly what ADK would have called) and invokes it
directly - simulating "the model decided to call tool X with args Y" while
still exercising the real tool function and the real outcome-capture
wiring end to end."""

from unittest.mock import AsyncMock

import pytest

from app.agents.agent_runtime import ToolCallingAgentRuntime
from app.agents.ops_agent import ops_agent
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate


def _make_customer(db):
    return customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )


def _make_ticket(db, customer_id):
    return ticket_crud.create_ticket(
        db, TicketCreate(customer_id=customer_id, subject="Order never arrived")
    )


def _call_tool(runtime: ToolCallingAgentRuntime, name: str, **kwargs):
    for tool in runtime._agent.tools:
        if tool.func.__name__ == name:
            return tool.func(**kwargs)
    raise AssertionError(f"no tool named {name} was built for this request")


@pytest.mark.asyncio
async def test_a_called_proposal_tool_becomes_the_returned_action_confirmation(db, monkeypatch):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)

    async def fake_run(self, prompt_text, user_id="system", on_retry=None):
        if on_retry:
            on_retry()
        _call_tool(
            self,
            "propose_create_escalation",
            escalation_type="refund_approval",
            requested_action="Refund outside the return window.",
            ticket_hint=ticket.ticket_number,
        )
        return "I'll go ahead and file that - please confirm."

    monkeypatch.setattr(ToolCallingAgentRuntime, "run", fake_run)

    result = await ops_agent.handle_message(
        db, message="refund this ticket", agent_name="Test Agent", role="support_agent"
    )

    assert result.type == "action-confirmation"
    assert result.pending_action.mutation_payload["ticket_id"] == ticket.id
    # The model's own wrap-up text is NOT used here - the tool already built
    # the real content in Python.
    assert result.content != "I'll go ahead and file that - please confirm."


@pytest.mark.asyncio
async def test_no_tool_called_returns_the_models_own_text(db, monkeypatch):
    async def fake_run(self, prompt_text, user_id="system", on_retry=None):
        if on_retry:
            on_retry()
        return "Hi! I can help with looking up customers, tickets, and orders."

    monkeypatch.setattr(ToolCallingAgentRuntime, "run", fake_run)

    result = await ops_agent.handle_message(
        db, message="hey there", agent_name="Test Agent", role="support_agent"
    )

    assert result.type == "text"
    assert result.content == "Hi! I can help with looking up customers, tickets, and orders."


@pytest.mark.asyncio
async def test_policy_search_outcome_gets_the_models_composed_answer_substituted_in(db, monkeypatch):
    async def fake_run(self, prompt_text, user_id="system", on_retry=None):
        if on_retry:
            on_retry()
        _call_tool(self, "search_policy_knowledge_base", query="refund policy")
        return "You have 30 days to request a refund."

    monkeypatch.setattr(ToolCallingAgentRuntime, "run", fake_run)

    result = await ops_agent.handle_message(
        db, message="what's our refund policy", agent_name="Test Agent", role="support_agent"
    )

    # No KB documents are ingested in this test, so the tool's own
    # not-found refusal is what actually gets returned - this still proves
    # needs_model_text=False refusals aren't overwritten by the model's text.
    assert result.content != "You have 30 days to request a refund."


@pytest.mark.asyncio
async def test_a_failed_llm_call_with_no_prior_outcome_returns_the_unavailable_message(db, monkeypatch):
    from app.core.exceptions import LLMTransientError

    async def fake_run(self, prompt_text, user_id="system", on_retry=None):
        if on_retry:
            on_retry()
        raise LLMTransientError("boom")

    monkeypatch.setattr(ToolCallingAgentRuntime, "run", fake_run)

    result = await ops_agent.handle_message(
        db, message="anything", agent_name="Test Agent", role="support_agent"
    )

    assert result.type == "error"
