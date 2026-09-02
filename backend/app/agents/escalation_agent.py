from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseSubAgent
from app.agents.messages import UNAVAILABLE_MESSAGE
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger
from app.prompts.loader import load_prompt
from app.schemas.chat import ActionDiff, ChatMessage, PendingAction
from app.services.action_token import create_action_token
from app.services.conversation import with_history
from app.services.ticket_resolution import resolve_ticket_context

logger = get_logger("escalation_agent")

_VALID_TYPES_HELP = (
    "a refund approval, an SLA exception, an account credit, or a retention offer override"
)


class EscalationAgentOutput(BaseModel):
    # Both left optional (schema can't say "I don't know") so a vague
    # message ("create an escalation", or something that doesn't fit any
    # of the four types) surfaces as a clarifying question instead of
    # forcing the model to invent a plausible-looking type/action just to
    # satisfy a required field - the exact bug this replaces.
    escalation_type: (
        Literal["refund_approval", "sla_exception", "account_credit", "retention_offer_override"]
        | None
    ) = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    requested_action: str | None = None
    ticket_hint: str | None = None
    policy_citation: str | None = None
    requested_amount: float | None = None
    summary: str = ""


class EscalationAgent:
    """Escalation-filing sub-agent. Always proposes; never files directly."""

    def __init__(self):
        instruction = load_prompt("escalation_agent")
        self._sub_agent = BaseSubAgent(
            agent_name="escalation_agent", instruction=instruction, output_schema=EscalationAgentOutput
        )

    async def handle_message(self, db: Session, message: str, history: str = "") -> ChatMessage:
        try:
            parsed = await self._sub_agent.run(
                with_history(history, message), user_id="escalation_agent"
            )
        except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
            logger.warning(f"Escalation agent classification failed: {exc}")
            return UNAVAILABLE_MESSAGE

        if not parsed.escalation_type or not parsed.requested_action:
            if parsed.escalation_type and not parsed.requested_action:
                # Progress was actually made this turn (the type is known) -
                # say so, rather than repeating the exact same generic
                # prompt verbatim. Repeating identical text after a reply
                # that clearly answered part of the question reads as "the
                # bot isn't listening", even though the type really was
                # understood; only the specifics are still missing.
                type_label = parsed.escalation_type.replace("_", " ")
                return ChatMessage(
                    type="text",
                    content=(
                        f"Got it — a {type_label}. What's the issue, and what exactly are "
                        "you asking for (an amount, a specific action, etc.)?"
                    ),
                    status="final",
                )
            return ChatMessage(
                type="text",
                content=(
                    "I can file an escalation for " + _VALID_TYPES_HELP + ". "
                    "What's the issue, and what are you asking for approval on?"
                ),
                status="final",
            )

        ticket = resolve_ticket_context(db, parsed.ticket_hint)
        if parsed.ticket_hint and not ticket:
            return ChatMessage(
                type="text",
                content=f"I couldn't find a ticket matching '{parsed.ticket_hint}'. Try its ticket number.",
                status="final",
            )
        # Every escalation in this app is filed against a specific ticket
        # (that's what the team lead reviews it in the context of) - if
        # nothing in the message or conversation history named one, ask
        # rather than proposing with an empty/dangling link. Filing "a
        # $1000 refund" with nothing to actually apply it to used to sail
        # straight through to a confirmable action.
        if not ticket:
            return ChatMessage(
                type="text",
                content="Which ticket is this escalation for? You can give me its ticket number.",
                status="final",
            )

        payload = {
            "escalation_type": parsed.escalation_type,
            "requested_action": parsed.requested_action,
            "priority": parsed.priority,
            "ticket_id": ticket.id,
            "policy_citation": parsed.policy_citation,
            "requested_amount": parsed.requested_amount,
        }

        # Shown in the review card as a labeled field list (see ChatPanel's
        # rendering: an empty `before` means "here's what's being created",
        # not "here's what changed") - human-readable values only, never
        # raw ids, so the agent can actually verify what they're approving.
        diff_after: dict = {
            "escalation_type": parsed.escalation_type.replace("_", " ").title(),
            "requested_action": parsed.requested_action,
            "ticket": ticket.ticket_number,
        }
        if parsed.requested_amount is not None:
            diff_after["requested_amount"] = f"${parsed.requested_amount:,.2f}"
        diff_after["priority"] = parsed.priority
        if parsed.policy_citation:
            diff_after["policy_citation"] = parsed.policy_citation

        content = parsed.summary or (
            f"File a {parsed.escalation_type.replace('_', ' ')} escalation for ticket "
            f"{ticket.ticket_number}: {parsed.requested_action}?"
        )

        return ChatMessage(
            type="action-confirmation",
            content=content,
            status="pending_confirmation",
            action_diff=ActionDiff(before={}, after=diff_after),
            pending_action=PendingAction(
                token=create_action_token(
                    action_type="create_escalation",
                    entity_type="ticket",
                    entity_id=ticket.id,
                    escalation_payload=payload,
                ),
                action_type="create_escalation",
                entity_type="ticket",
                entity_id=ticket.id,
                escalation_payload=payload,
            ),
        )


escalation_agent = EscalationAgent()
