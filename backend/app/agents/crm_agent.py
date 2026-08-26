from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseSubAgent
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger
from app.crud.customer import get_customer_with_history, list_customers
from app.prompts.loader import load_prompt
from app.schemas.chat import ChatMessage
from app.services.entity_resolution import resolve_entity

logger = get_logger("crm_agent")

_UNAVAILABLE_MESSAGE = ChatMessage(
    type="error",
    content="The AI assistant is temporarily unavailable. Please try again in a moment.",
    status="final",
)

_NOT_FOUND = ChatMessage(
    type="text",
    content="I couldn't find a matching customer. Try their full name, email, or account id.",
    status="final",
)


class CRMAgentOutput(BaseModel):
    intent: Literal["lookup", "update_field", "view_history"]
    entity_type: Literal["customer", "order", "ticket"] = "customer"
    target_hint: str | None = None
    field_name: str | None = None
    field_value: str | None = None
    summary: str = ""


class CRMAgent:
    """Customer lookup + write sub-agent (Architecture.md §5).

    Built and unit-tested in Phase 3 per the roadmap ("crm_agent.py
    lookup/view_history only, no writes yet"), but not yet wired into
    router_agent's dispatch table - the router's own direct-SQL path
    already covers crm_lookup for Phase 3's demoable chat flow. This agent
    becomes load-bearing in Phase 4, when `update_field` needs
    entity_resolution to safely identify a write target (raw SQL can't do
    that safely - see the propose/confirm pattern in Architecture.md §5).
    """

    def __init__(self):
        instruction = load_prompt("crm_agent")
        self._sub_agent = BaseSubAgent(
            agent_name="crm_agent", instruction=instruction, output_schema=CRMAgentOutput
        )

    async def handle_message(
        self, db: Session, message: str, active_entity_id: str | None = None
    ) -> ChatMessage:
        try:
            parsed = await self._sub_agent.run(message, user_id="crm_agent")
        except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
            logger.warning(f"CRM agent classification failed: {exc}")
            return _UNAVAILABLE_MESSAGE

        if parsed.intent == "lookup":
            return self.handle_lookup(db, parsed.target_hint or message)
        if parsed.intent == "view_history":
            return self.handle_view_history(db, active_entity_id, parsed.target_hint or message)
        return ChatMessage(
            type="text",
            content="Updating a customer record through chat isn't available in this build yet.",
            status="final",
        )

    def handle_lookup(self, db: Session, target_hint: str) -> ChatMessage:
        candidates = list_customers(db, limit=1000)
        customer = resolve_entity(candidates, target_hint, target_hint)
        if not customer:
            return _NOT_FOUND

        lines = [
            f"{customer.full_name} ({customer.email})",
            f"Company: {customer.company or '—'} | Tier: {customer.account_tier} | Status: {customer.status}",
            f"Phone: {customer.phone or '—'}",
        ]
        return ChatMessage(type="text", content="\n".join(lines), status="final")

    def handle_view_history(
        self, db: Session, active_entity_id: str | None, target_hint: str
    ) -> ChatMessage:
        customer_id = active_entity_id
        if not customer_id:
            candidates = list_customers(db, limit=1000)
            resolved = resolve_entity(candidates, target_hint, target_hint)
            customer_id = resolved.id if resolved else None

        if not customer_id:
            return _NOT_FOUND

        customer = get_customer_with_history(db, customer_id)
        if not customer:
            return _NOT_FOUND

        lines = [f"{customer.full_name} - order/ticket history:"]
        if customer.orders:
            for order in customer.orders[:3]:
                lines.append(f"  Order {order.order_number}: {order.status}, ${order.total_amount}")
        else:
            lines.append("  No orders on file.")
        if customer.tickets:
            for ticket in customer.tickets[:3]:
                lines.append(f"  Ticket {ticket.ticket_number}: {ticket.subject} ({ticket.status})")
        else:
            lines.append("  No tickets on file.")
        return ChatMessage(type="text", content="\n".join(lines), status="final")


crm_agent = CRMAgent()
