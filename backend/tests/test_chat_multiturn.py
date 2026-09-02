"""End-to-end proof that conversation history actually reaches the LLM: the
exact motivating scenario from the bug report - "I want to raise an
escalation" followed by an elliptical follow-up that only makes sense in
light of the first message - hitting POST /chat twice with the same
session_id.

ToolCallingAgentRuntime.run is monkeypatched at the class level (the same
seam test_ops_agent.py uses) with a fake that inspects which turn it's on
and either replies in plain text (turn 1, nothing to call yet) or calls the
real propose_create_escalation tool closure (turn 2) - this exercises the
real router->ops_agent->history->tool pipeline end to end without a real
Gemini key."""

from app.agents.agent_runtime import ToolCallingAgentRuntime
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate

_TURN_1_REPLY = (
    "I can file an escalation for a refund approval, an SLA exception, an account "
    "credit, or a retention offer override. What's the issue, and what are you asking "
    "for approval on?"
)


def _call_tool(runtime: ToolCallingAgentRuntime, name: str, **kwargs):
    for tool in runtime._agent.tools:
        if tool.func.__name__ == name:
            return tool.func(**kwargs)
    raise AssertionError(f"no tool named {name} was built for this request")


def test_second_turn_prompt_includes_the_first_turns_exchange(client, agent_headers, db, monkeypatch):
    customer = customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )
    ticket = ticket_crud.create_ticket(
        db, TicketCreate(customer_id=customer.id, subject="Order never arrived")
    )
    session_id = "33333333-3333-3333-3333-333333333333"
    prompts_seen = []

    async def fake_run(self, prompt_text, user_id="system", on_retry=None):
        if on_retry:
            on_retry()
        prompts_seen.append(prompt_text)
        if len(prompts_seen) == 1:
            # Turn 1: nothing concrete stated yet - no tool call.
            return _TURN_1_REPLY
        # Turn 2: on its own this message names an amount and a ticket, but
        # not what the ask actually is - the whole point of history is that
        # the model sees turn 1 alongside it before deciding to call this.
        _call_tool(
            self,
            "propose_create_escalation",
            escalation_type="refund_approval",
            requested_action="Refund $1000 for the order.",
            ticket_hint=ticket.ticket_number,
            requested_amount=1000,
        )
        return "Filing that now - please confirm."

    monkeypatch.setattr(ToolCallingAgentRuntime, "run", fake_run)

    r1 = client.post(
        "/api/v1/chat",
        json={"message": "I want to raise an escalation", "session_id": session_id},
        headers=agent_headers,
    )
    assert r1.status_code == 200
    first_reply = r1.json()["messages"][0]["content"]
    assert first_reply == _TURN_1_REPLY

    r2 = client.post(
        "/api/v1/chat",
        json={"message": f"refund of $1000 for ticket {ticket.ticket_number}", "session_id": session_id},
        headers=agent_headers,
    )
    assert r2.status_code == 200

    assert len(prompts_seen) == 2
    second_prompt = prompts_seen[1]
    assert "I want to raise an escalation" in second_prompt
    assert first_reply in second_prompt
    assert f"refund of $1000 for ticket {ticket.ticket_number}" in second_prompt

    # And the actual proposal from turn 2 correctly resolved the ticket.
    second_reply = r2.json()["messages"][0]
    assert second_reply["pending_action"]["mutation_payload"]["ticket_id"] == ticket.id


def test_a_different_agent_cannot_read_another_agents_session(
    client, agent_headers, lead_headers, db, monkeypatch
):
    async def fake_run(self, prompt_text, user_id="system", on_retry=None):
        if on_retry:
            on_retry()
        return "Hi there."

    monkeypatch.setattr(ToolCallingAgentRuntime, "run", fake_run)

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
