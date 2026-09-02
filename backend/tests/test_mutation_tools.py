"""Tests mutation_tools functions directly - no LLM/mocking involved at all,
since a tool function is just plain synchronous Python once the model's
argument-extraction step is out of the picture. Each test simulates "the
model called this tool with these args" and asserts on what got appended to
`outcomes` (or, when nothing should be proposed, that outcomes stayed
empty and a clarifying string came back instead)."""

from app.agents.tools import mutation_tools
from app.agents.tools.base import PROPOSAL_ALREADY_SHOWN
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


def _make_agent(db, full_name="Priya Nair", email="priya.test@example.com", team="billing"):
    agent = SupportAgent(
        full_name=full_name, email=email, password_hash=hash_password("password123"), team=team
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def _tools(db, actor="Test Agent"):
    outcomes = []
    built = {fn.__name__: fn for fn in mutation_tools.build_tools(db, actor=actor, outcomes=outcomes)}
    return built, outcomes


# --- propose_create_escalation ---


def test_fully_specified_escalation_with_no_ticket_returns_a_clarifying_string_not_a_proposal(db):
    """The exact bug reported this session: a fully-specified escalation
    with no ticket named anywhere used to sail through to a confirmable
    action with a dangling link. This is enforced in Python regardless of
    what the model supplied - the tool itself refuses to propose."""
    tools, outcomes = _tools(db)
    result = tools["propose_create_escalation"](
        escalation_type="account_credit",
        requested_action="Issue a $20 account credit for a delayed shipment.",
        requested_amount=20,
    )
    assert outcomes == []
    assert "ticket" in result.lower()


def test_escalation_with_ticket_hint_resolves_and_proposes(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    tools, outcomes = _tools(db)
    result = tools["propose_create_escalation"](
        escalation_type="refund_approval",
        requested_action="Refund the order outside the return window.",
        ticket_hint=ticket.ticket_number,
    )
    assert result == PROPOSAL_ALREADY_SHOWN
    assert len(outcomes) == 1
    msg = outcomes[0].chat_message
    assert msg.type == "action-confirmation"
    assert msg.status == "pending_confirmation"
    assert msg.pending_action.mutation_payload["ticket_id"] == ticket.id
    assert msg.pending_action.entity_type == "ticket"
    assert msg.action_diff.before == {}
    assert msg.action_diff.after["ticket"] == ticket.ticket_number
    assert msg.action_diff.after["escalation_type"] == "Refund Approval"


def test_unmatched_ticket_hint_returns_a_not_found_string_not_a_proposal(db):
    """Regression coverage for the tool-calling safety mitigation: a
    wrong-but-plausible hint must never reach a signed-token proposal."""
    tools, outcomes = _tools(db)
    result = tools["propose_create_escalation"](
        escalation_type="account_credit",
        requested_action="Issue a credit.",
        ticket_hint="TCK-DOESNOTEXIST",
    )
    assert outcomes == []
    assert "couldn't find" in result.lower()


def test_escalation_review_card_shows_human_readable_fields(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    tools, outcomes = _tools(db)
    tools["propose_create_escalation"](
        escalation_type="account_credit",
        requested_action="Issue a $45 credit for a shipping delay.",
        ticket_hint=ticket.ticket_number,
        requested_amount=45,
        priority="high",
    )
    after = outcomes[0].chat_message.action_diff.after
    assert after["requested_amount"] == "$45.00"
    assert after["priority"] == "high"
    assert after["ticket"] == ticket.ticket_number  # not the raw ticket id


# --- propose_reassign_ticket / propose_schedule_callback ---


def test_reassign_diff_shows_agent_names_not_raw_ids(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    target = _make_agent(db)
    tools, outcomes = _tools(db)

    result = tools["propose_reassign_ticket"](
        ticket_hint=ticket.ticket_number, target_agent_hint=target.full_name
    )

    assert result == PROPOSAL_ALREADY_SHOWN
    msg = outcomes[0].chat_message
    assert msg.action_diff.before == {"assigned_agent": "Unassigned"}
    assert msg.action_diff.after == {"assigned_agent": target.full_name}
    assert msg.pending_action.field_value == target.id


def test_reassign_diff_shows_previous_agents_name_when_already_assigned(db):
    customer = _make_customer(db)
    previous = _make_agent(db, full_name="Sam Rivera", email="sam.test@example.com")
    target = _make_agent(db, full_name="Priya Nair", email="priya.test2@example.com")
    ticket = _make_ticket(db, customer.id, assigned_agent_id=previous.id)
    tools, outcomes = _tools(db)

    tools["propose_reassign_ticket"](ticket_hint=ticket.ticket_number, target_agent_hint=target.full_name)

    msg = outcomes[0].chat_message
    assert msg.action_diff.before == {"assigned_agent": "Sam Rivera"}
    assert msg.action_diff.after == {"assigned_agent": "Priya Nair"}


def test_reassign_unmatched_ticket_returns_a_string_not_a_proposal(db):
    tools, outcomes = _tools(db)
    result = tools["propose_reassign_ticket"](ticket_hint="TCK-NOPE", target_agent_hint="anyone")
    assert outcomes == []
    assert "ticket" in result.lower()


def test_schedule_callback_proposes_with_the_stated_time(db):
    customer = _make_customer(db)
    ticket = _make_ticket(db, customer.id)
    tools, outcomes = _tools(db)

    result = tools["propose_schedule_callback"](
        ticket_hint=ticket.ticket_number, callback_time="tomorrow at 3pm"
    )

    assert result == PROPOSAL_ALREADY_SHOWN
    msg = outcomes[0].chat_message
    assert msg.action_diff.after == {"callback_time": "tomorrow at 3pm"}


# --- propose_update_customer_field ---


def test_update_customer_field_proposes_the_change(db):
    customer = _make_customer(db)
    tools, outcomes = _tools(db)

    result = tools["propose_update_customer_field"](
        customer_hint=customer.email, field_name="phone number", field_value="+1-555-0100"
    )

    assert result == PROPOSAL_ALREADY_SHOWN
    msg = outcomes[0].chat_message
    assert msg.pending_action.field_name == "phone"
    assert msg.pending_action.field_value == "+1-555-0100"
    assert msg.action_diff.after == {"phone": "+1-555-0100"}


def test_update_customer_field_unsupported_field_returns_a_string_not_a_proposal(db):
    customer = _make_customer(db)
    tools, outcomes = _tools(db)

    result = tools["propose_update_customer_field"](
        customer_hint=customer.email, field_name="favorite color", field_value="blue"
    )

    assert outcomes == []
    assert "isn't a field" in result


def test_update_customer_field_ambiguous_customer_returns_a_string_not_a_proposal(db):
    _make_customer(db, full_name="Carla Jensen", email="carla1@example.com")
    _make_customer(db, full_name="Carla Jensen", email="carla2@example.com")
    tools, outcomes = _tools(db)

    result = tools["propose_update_customer_field"](
        customer_hint="Carla Jensen", field_name="phone", field_value="+1-555-0100"
    )

    assert outcomes == []
    assert "more than one" in result.lower()


# --- propose_create_ticket (the previously-missing capability) ---


def test_create_ticket_proposes_with_the_stated_fields(db):
    customer = _make_customer(db)
    tools, outcomes = _tools(db)

    result = tools["propose_create_ticket"](
        customer_hint=customer.email,
        subject="Can't reset my password",
        channel="chat",
        priority="high",
        category="account",
    )

    assert result == PROPOSAL_ALREADY_SHOWN
    msg = outcomes[0].chat_message
    assert msg.type == "action-confirmation"
    assert msg.action_diff.before == {}
    assert msg.action_diff.after["subject"] == "Can't reset my password"
    assert msg.action_diff.after["customer"] == customer.full_name
    assert msg.pending_action.mutation_payload["customer_id"] == customer.id
    assert msg.pending_action.action_type == "create_ticket"


def test_create_ticket_defaults_channel_priority_category_when_unstated(db):
    customer = _make_customer(db)
    tools, outcomes = _tools(db)

    tools["propose_create_ticket"](customer_hint=customer.email, subject="General question")

    payload = outcomes[0].chat_message.pending_action.mutation_payload
    assert payload["channel"] == "email"
    assert payload["priority"] == "medium"
    assert payload["category"] == "other"


def test_create_ticket_unmatched_customer_returns_a_string_not_a_proposal(db):
    tools, outcomes = _tools(db)
    result = tools["propose_create_ticket"](customer_hint="nobody@example.com", subject="Test")
    assert outcomes == []
    assert "customer" in result.lower()
