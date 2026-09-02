"""Tests escalation_agent's post-classification logic directly, mocking
the LLM call so these run without a real Gemini key and exercise exactly
the bugs reported: fabricating escalation_type/requested_action out of a
vague message, and silently dropping an explicitly-named ticket."""

from unittest.mock import AsyncMock

import pytest

from app.agents.escalation_agent import _VALID_TYPES_HELP, EscalationAgentOutput, escalation_agent
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
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


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    """Replaces the LLM call with a canned response set per-test via
    `_mock_llm.result`, so handle_message's own logic (ticket resolution,
    the missing-field fallback, diff construction) runs for real."""
    mock = AsyncMock()
    monkeypatch.setattr(escalation_agent._sub_agent, "run", mock)
    return mock


async def _handle(db, mock, parsed: EscalationAgentOutput, message="irrelevant", **kwargs):
    mock.return_value = parsed
    return await escalation_agent.handle_message(db, message, **kwargs)


@pytest.mark.asyncio
async def test_missing_escalation_type_asks_a_clarifying_question_instead_of_proposing(db, _mock_llm):
    parsed = EscalationAgentOutput(escalation_type=None, requested_action=None)
    result = await _handle(db, _mock_llm, parsed)
    assert result.type == "text"
    assert result.pending_action is None
    assert "refund approval" in result.content.lower()


@pytest.mark.asyncio
async def test_missing_requested_action_alone_also_asks_instead_of_proposing(db, _mock_llm):
    parsed = EscalationAgentOutput(escalation_type="account_credit", requested_action=None)
    result = await _handle(db, _mock_llm, parsed)
    assert result.type == "text"
    assert result.pending_action is None


@pytest.mark.asyncio
async def test_known_type_but_missing_action_asks_a_targeted_follow_up_not_the_generic_menu(
    db, _mock_llm
):
    """Reported bug: a follow-up like "for refund" (after the generic
    clarifying question) got the exact same generic message back verbatim,
    even though the type actually was understood - reading as "the bot
    isn't listening". The type having been understood should be reflected
    back, not silently dropped."""
    parsed = EscalationAgentOutput(escalation_type="refund_approval", requested_action=None)
    result = await _handle(db, _mock_llm, parsed)
    assert result.type == "text"
    assert result.pending_action is None
    assert "refund approval" in result.content.lower()
    # Not the generic four-type menu this time - that's the exact text that
    # looked like no progress was made.
    assert _VALID_TYPES_HELP not in result.content


@pytest.mark.asyncio
async def test_fully_specified_request_asks_for_a_ticket_when_none_is_given(db, _mock_llm):
    """The exact bug reported: "refund of $1000" with no ticket named and
    no ticket page open used to sail through to a confirmable action with
    an empty entity link. Every escalation must be tied to a ticket."""
    parsed = EscalationAgentOutput(
        escalation_type="account_credit",
        requested_action="Issue a $20 account credit for a delayed shipment.",
        requested_amount=20,
    )
    result = await _handle(db, _mock_llm, parsed)
    assert result.type == "text"
    assert result.pending_action is None
    assert "ticket" in result.content.lower()


@pytest.mark.asyncio
async def test_explicit_ticket_hint_in_message_resolves_and_links_the_ticket(db, _mock_llm):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    parsed = EscalationAgentOutput(
        escalation_type="refund_approval",
        requested_action="Refund the order outside the return window.",
        ticket_hint=ticket.ticket_number,
    )
    result = await _handle(db, _mock_llm, parsed)
    assert result.type == "action-confirmation"
    # This is the exact bug reported: a ticket number stated in the
    # message text used to be silently dropped unless the agent was also
    # sitting on that ticket's own page.
    assert result.pending_action.escalation_payload["ticket_id"] == ticket.id
    assert result.pending_action.entity_type == "ticket"
    assert result.action_diff.after["ticket"] == ticket.ticket_number


@pytest.mark.asyncio
async def test_unmatched_ticket_hint_returns_a_not_found_message_not_a_proposal(db, _mock_llm):
    parsed = EscalationAgentOutput(
        escalation_type="account_credit",
        requested_action="Issue a credit.",
        ticket_hint="TCK-DOESNOTEXIST",
    )
    result = await _handle(db, _mock_llm, parsed)
    assert result.type == "text"
    assert result.pending_action is None


@pytest.mark.asyncio
async def test_review_card_shows_human_readable_fields_not_raw_ids(db, _mock_llm):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    parsed = EscalationAgentOutput(
        escalation_type="account_credit",
        requested_action="Issue a $45 credit for a shipping delay.",
        ticket_hint=ticket.ticket_number,
        requested_amount=45,
        priority="high",
    )
    result = await _handle(db, _mock_llm, parsed)
    after = result.action_diff.after
    assert result.action_diff.before == {}
    assert after["escalation_type"] == "Account Credit"  # not the raw "account_credit"
    assert after["requested_action"] == "Issue a $45 credit for a shipping delay."
    assert after["ticket"] == ticket.ticket_number  # not the raw ticket id
    assert after["requested_amount"] == "$45.00"
    assert after["priority"] == "high"


@pytest.mark.asyncio
async def test_conversation_history_is_included_in_the_llm_prompt(db, _mock_llm):
    """History (not a hidden active-entity id) is what carries multi-turn
    context now - confirm it actually reaches the classification prompt."""
    parsed = EscalationAgentOutput(escalation_type=None, requested_action=None)
    history = "User: I want to raise an escalation\nAssistant: Sure, what's the issue?"
    await _handle(db, _mock_llm, parsed, message="refund of $1000", history=history)
    prompt_sent = _mock_llm.call_args.args[0]
    assert history in prompt_sent
    assert "refund of $1000" in prompt_sent
