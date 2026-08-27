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

logger = get_logger("escalation_agent")


class EscalationAgentOutput(BaseModel):
    escalation_type: Literal[
        "refund_approval", "sla_exception", "account_credit", "retention_offer_override"
    ]
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    requested_action: str
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

    async def handle_message(
        self,
        db: Session,
        message: str,
        active_entity_id: str | None = None,
        active_entity_type: str | None = None,
    ) -> ChatMessage:
        try:
            parsed = await self._sub_agent.run(message, user_id="escalation_agent")
        except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
            logger.warning(f"Escalation agent classification failed: {exc}")
            return UNAVAILABLE_MESSAGE

        # Only link to a ticket if the active entity actually is one.
        ticket_id = active_entity_id if active_entity_type == "ticket" else None

        payload = {
            "escalation_type": parsed.escalation_type,
            "requested_action": parsed.requested_action,
            "priority": parsed.priority,
            "ticket_id": ticket_id,
            "policy_citation": parsed.policy_citation,
            "requested_amount": parsed.requested_amount,
        }
        entity_type = "ticket" if ticket_id else "customer"
        entity_id = ticket_id or active_entity_id or ""

        return ChatMessage(
            type="action-confirmation",
            content=parsed.summary
            or f"File a {parsed.escalation_type} escalation: {parsed.requested_action}?",
            status="pending_confirmation",
            action_diff=ActionDiff(before={}, after=payload),
            pending_action=PendingAction(
                token=create_action_token(
                    action_type="create_escalation",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    escalation_payload=payload,
                ),
                action_type="create_escalation",
                entity_type=entity_type,
                entity_id=entity_id,
                escalation_payload=payload,
            ),
        )


escalation_agent = EscalationAgent()
