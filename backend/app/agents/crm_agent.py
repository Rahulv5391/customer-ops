from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseSubAgent
from app.agents.messages import UNAVAILABLE_MESSAGE
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger
from app.crud.customer import get_customer, get_customer_with_history, list_customers
from app.prompts.loader import load_prompt
from app.schemas.chat import ActionDiff, ChatMessage, PendingAction
from app.services.action_token import create_action_token
from app.services.crm_mutations import CUSTOMER_FIELD_LABELS, normalize_customer_field
from app.services.entity_resolution import AmbiguousEntityError, resolve_entity

logger = get_logger("crm_agent")

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
    """Customer lookup and field-update sub-agent. Lookups execute
    directly; field updates are always proposed for confirmation first."""

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
            return UNAVAILABLE_MESSAGE

        if parsed.intent == "lookup":
            return self.handle_lookup(db, parsed.target_hint, message)
        if parsed.intent == "view_history":
            return self.handle_view_history(db, active_entity_id, parsed.target_hint, message)
        return self.handle_update_field(
            db, active_entity_id, parsed.target_hint, message, parsed.field_name, parsed.field_value
        )

    def _resolve_customer(
        self, candidates: list, target_hint: str | None, raw_message: str
    ) -> tuple[object | None, ChatMessage | None]:
        """Wraps resolve_entity, turning an ambiguous match into a
        clarifying ChatMessage instead of letting it propagate as an error.
        Returns (customer, None) on a clean result, or (None, message) when
        the caller should return `message` as-is."""
        try:
            return resolve_entity(candidates, target_hint, raw_message), None
        except AmbiguousEntityError as exc:
            names = ", ".join(f"{c.full_name} ({c.email})" for c in exc.matches[:5])
            return None, ChatMessage(
                type="text",
                content=f"More than one customer matches that: {names}. Try their email or customer id instead.",
                status="final",
            )

    def handle_lookup(self, db: Session, target_hint: str | None, raw_message: str) -> ChatMessage:
        candidates = list_customers(db, limit=1000)
        customer, ambiguous = self._resolve_customer(candidates, target_hint, raw_message)
        if ambiguous:
            return ambiguous
        if not customer:
            return _NOT_FOUND

        lines = [
            f"{customer.full_name} ({customer.email})",
            f"Company: {customer.company or '—'} | Tier: {customer.account_tier} | Status: {customer.status}",
            f"Phone: {customer.phone or '—'}",
        ]
        return ChatMessage(type="text", content="\n".join(lines), status="final")

    def handle_view_history(
        self, db: Session, active_entity_id: str | None, target_hint: str | None, raw_message: str
    ) -> ChatMessage:
        customer_id = active_entity_id
        if not customer_id:
            candidates = list_customers(db, limit=1000)
            resolved, ambiguous = self._resolve_customer(candidates, target_hint, raw_message)
            if ambiguous:
                return ambiguous
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

    def handle_update_field(
        self,
        db: Session,
        active_entity_id: str | None,
        target_hint: str | None,
        raw_message: str,
        field_name: str | None,
        field_value: str | None,
    ) -> ChatMessage:
        if not field_name or field_value is None:
            return ChatMessage(
                type="text",
                content="I didn't catch what field to change or what to set it to.",
                status="final",
            )

        customer = get_customer(db, active_entity_id) if active_entity_id else None
        if not customer:
            candidates = list_customers(db, limit=1000)
            customer, ambiguous = self._resolve_customer(candidates, target_hint, raw_message)
            if ambiguous:
                return ambiguous
        if not customer:
            return _NOT_FOUND

        normalized_field = normalize_customer_field(field_name)
        if normalized_field is None:
            supported = ", ".join(CUSTOMER_FIELD_LABELS.values())
            return ChatMessage(
                type="text",
                content=f"'{field_name}' isn't a field I can update. I can update: {supported}.",
                status="final",
            )

        before_value = getattr(customer, normalized_field)
        return ChatMessage(
            type="action-confirmation",
            content=(
                f"Change {customer.full_name}'s {normalized_field} from "
                f"'{before_value}' to '{field_value}'?"
            ),
            status="pending_confirmation",
            action_diff=ActionDiff(
                before={normalized_field: before_value}, after={normalized_field: field_value}
            ),
            pending_action=PendingAction(
                token=create_action_token(
                    action_type="update_field",
                    entity_type="customer",
                    entity_id=customer.id,
                    field_name=normalized_field,
                    field_value=field_value,
                ),
                action_type="update_field",
                entity_type="customer",
                entity_id=customer.id,
                field_name=normalized_field,
                field_value=field_value,
            ),
            resolved_entity_id=customer.id,
            resolved_entity_type="customer",
        )


crm_agent = CRMAgent()
