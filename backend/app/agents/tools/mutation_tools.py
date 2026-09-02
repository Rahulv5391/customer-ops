"""Every tool here only ever PROPOSES a change - it builds an ActionDiff and
a signed token (create_action_token) and appends that as a terminal
ToolOutcome, exactly like the old per-category sub-agents did. None of these
ever call app.services.crm_mutations directly; the real write only happens
from POST /chat/action/confirm decoding the signed token after a human
clicks Authorize. This is the one hard invariant that must never be broken
by anything built in this module."""

from typing import Callable, Literal

from sqlalchemy.orm import Session

from app.agents.tools.base import PROPOSAL_ALREADY_SHOWN, ToolOutcome, logged_tool
from app.crud.agent import list_agents
from app.crud.customer import list_customers
from app.prompts.loader import load_prompt
from app.schemas.chat import ActionDiff, ChatMessage, PendingAction
from app.services.action_token import create_action_token
from app.services.crm_mutations import CUSTOMER_FIELD_LABELS, normalize_customer_field
from app.services.entity_resolution import AmbiguousEntityError, resolve_entity
from app.services.ticket_resolution import resolve_ticket_context

_VALID_ESCALATION_TYPES_HELP = (
    "a refund approval, an SLA exception, an account credit, or a retention offer override"
)

_UPDATE_CUSTOMER_FIELD_DOC = load_prompt("tools/update_customer_field")
_REASSIGN_TICKET_DOC = load_prompt("tools/reassign_ticket")
_SCHEDULE_CALLBACK_DOC = load_prompt("tools/schedule_callback")
_CREATE_ESCALATION_DOC = load_prompt("tools/create_escalation")
_CREATE_TICKET_DOC = load_prompt("tools/create_ticket")


def _ambiguous_customer_message(exc: AmbiguousEntityError) -> str:
    names = ", ".join(f"{c.full_name} ({c.email})" for c in exc.matches[:5])
    return f"More than one customer matches that: {names}. Try their email or customer id instead."


def build_tools(db: Session, actor: str, outcomes: list[ToolOutcome]) -> list[Callable]:
    @logged_tool
    def propose_update_customer_field(
        customer_hint: str, field_name: str, field_value: str
    ) -> str:
        candidates = list_customers(db, limit=1000)
        try:
            customer = resolve_entity(candidates, customer_hint, customer_hint)
        except AmbiguousEntityError as exc:
            return _ambiguous_customer_message(exc)
        if not customer:
            return "No matching customer was found. Ask the user for their full name, email, or customer id."

        normalized_field = normalize_customer_field(field_name)
        if normalized_field is None:
            supported = ", ".join(CUSTOMER_FIELD_LABELS.values())
            return f"'{field_name}' isn't a field that can be updated through chat. Fields that can be updated: {supported}."

        before_value = getattr(customer, normalized_field)
        outcomes.append(
            ToolOutcome(
                chat_message=ChatMessage(
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
                )
            )
        )
        return PROPOSAL_ALREADY_SHOWN

    propose_update_customer_field.__doc__ = _UPDATE_CUSTOMER_FIELD_DOC

    @logged_tool
    def propose_reassign_ticket(ticket_hint: str, target_agent_hint: str) -> str:
        ticket = resolve_ticket_context(db, ticket_hint)
        if not ticket:
            return "No matching ticket was found. Ask the user for the ticket number."

        try:
            target_agent = resolve_entity(list_agents(db), target_agent_hint, target_agent_hint)
        except AmbiguousEntityError as exc:
            names = ", ".join(f"{a.full_name} ({a.team})" for a in exc.matches[:5])
            return f"More than one agent matches that: {names}. Try their email instead."
        if not target_agent:
            return f"No agent matching '{target_agent_hint}' was found. Ask the user to confirm the agent's name."

        before_agent_name = ticket.assigned_agent.full_name if ticket.assigned_agent else "Unassigned"
        outcomes.append(
            ToolOutcome(
                chat_message=ChatMessage(
                    type="action-confirmation",
                    content=(
                        f"Reassign ticket {ticket.ticket_number} from {before_agent_name} "
                        f"to {target_agent.full_name}?"
                    ),
                    status="pending_confirmation",
                    action_diff=ActionDiff(
                        before={"assigned_agent": before_agent_name},
                        after={"assigned_agent": target_agent.full_name},
                    ),
                    pending_action=PendingAction(
                        token=create_action_token(
                            action_type="reassign_ticket",
                            entity_type="ticket",
                            entity_id=ticket.id,
                            field_name="assigned_agent_id",
                            field_value=target_agent.id,
                        ),
                        action_type="reassign_ticket",
                        entity_type="ticket",
                        entity_id=ticket.id,
                        field_name="assigned_agent_id",
                        field_value=target_agent.id,
                    ),
                )
            )
        )
        return PROPOSAL_ALREADY_SHOWN

    propose_reassign_ticket.__doc__ = _REASSIGN_TICKET_DOC

    @logged_tool
    def propose_schedule_callback(ticket_hint: str, callback_time: str) -> str:
        ticket = resolve_ticket_context(db, ticket_hint)
        if not ticket:
            return "No matching ticket was found. Ask the user for the ticket number."

        outcomes.append(
            ToolOutcome(
                chat_message=ChatMessage(
                    type="action-confirmation",
                    content=f"Schedule a callback on ticket {ticket.ticket_number} for {callback_time}?",
                    status="pending_confirmation",
                    action_diff=ActionDiff(before={}, after={"callback_time": callback_time}),
                    pending_action=PendingAction(
                        token=create_action_token(
                            action_type="schedule_callback",
                            entity_type="ticket",
                            entity_id=ticket.id,
                            field_value=callback_time,
                        ),
                        action_type="schedule_callback",
                        entity_type="ticket",
                        entity_id=ticket.id,
                        field_value=callback_time,
                    ),
                )
            )
        )
        return PROPOSAL_ALREADY_SHOWN

    propose_schedule_callback.__doc__ = _SCHEDULE_CALLBACK_DOC

    @logged_tool
    def propose_create_escalation(
        escalation_type: Literal[
            "refund_approval", "sla_exception", "account_credit", "retention_offer_override"
        ],
        requested_action: str,
        ticket_hint: str | None = None,
        priority: Literal["low", "medium", "high", "urgent"] = "medium",
        policy_citation: str | None = None,
        requested_amount: float | None = None,
    ) -> str:
        ticket = resolve_ticket_context(db, ticket_hint)
        if ticket_hint and not ticket:
            return f"I couldn't find a ticket matching '{ticket_hint}'. Ask the user for the ticket number."
        # Every escalation in this app is filed against a specific ticket
        # (that's what the team lead reviews it in the context of) - if
        # nothing named one, don't propose with an empty/dangling link;
        # ask instead. This is enforced in Python regardless of what the
        # model believed, not left to instruction-following alone.
        if not ticket:
            return "This needs a ticket to file the escalation against. Ask the user for the ticket number."

        payload = {
            "escalation_type": escalation_type,
            "requested_action": requested_action,
            "priority": priority,
            "ticket_id": ticket.id,
            "policy_citation": policy_citation,
            "requested_amount": requested_amount,
        }
        diff_after: dict = {
            "escalation_type": escalation_type.replace("_", " ").title(),
            "requested_action": requested_action,
            "ticket": ticket.ticket_number,
        }
        if requested_amount is not None:
            diff_after["requested_amount"] = f"${requested_amount:,.2f}"
        diff_after["priority"] = priority
        if policy_citation:
            diff_after["policy_citation"] = policy_citation

        outcomes.append(
            ToolOutcome(
                chat_message=ChatMessage(
                    type="action-confirmation",
                    content=(
                        f"File a {escalation_type.replace('_', ' ')} escalation for ticket "
                        f"{ticket.ticket_number}: {requested_action}?"
                    ),
                    status="pending_confirmation",
                    action_diff=ActionDiff(before={}, after=diff_after),
                    pending_action=PendingAction(
                        token=create_action_token(
                            action_type="create_escalation",
                            entity_type="ticket",
                            entity_id=ticket.id,
                            mutation_payload=payload,
                        ),
                        action_type="create_escalation",
                        entity_type="ticket",
                        entity_id=ticket.id,
                        mutation_payload=payload,
                    ),
                )
            )
        )
        return PROPOSAL_ALREADY_SHOWN

    propose_create_escalation.__doc__ = _CREATE_ESCALATION_DOC

    @logged_tool
    def propose_create_ticket(
        customer_hint: str,
        subject: str,
        channel: Literal["email", "chat", "phone", "social"] = "email",
        priority: Literal["low", "medium", "high", "urgent"] = "medium",
        category: Literal["billing", "technical", "shipping", "account", "other"] = "other",
    ) -> str:
        candidates = list_customers(db, limit=1000)
        try:
            customer = resolve_entity(candidates, customer_hint, customer_hint)
        except AmbiguousEntityError as exc:
            return _ambiguous_customer_message(exc)
        if not customer:
            return "No matching customer was found. Ask the user for the customer's full name, email, or id."

        payload = {
            "customer_id": customer.id,
            "subject": subject,
            "channel": channel,
            "priority": priority,
            "category": category,
        }
        diff_after = {
            "customer": customer.full_name,
            "subject": subject,
            "channel": channel,
            "priority": priority,
            "category": category,
        }

        outcomes.append(
            ToolOutcome(
                chat_message=ChatMessage(
                    type="action-confirmation",
                    content=f"Create a new {channel} ticket for {customer.full_name}: {subject}?",
                    status="pending_confirmation",
                    action_diff=ActionDiff(before={}, after=diff_after),
                    pending_action=PendingAction(
                        token=create_action_token(
                            action_type="create_ticket",
                            entity_type="customer",
                            entity_id=customer.id,
                            mutation_payload=payload,
                        ),
                        action_type="create_ticket",
                        entity_type="customer",
                        entity_id=customer.id,
                        mutation_payload=payload,
                    ),
                )
            )
        )
        return PROPOSAL_ALREADY_SHOWN

    propose_create_ticket.__doc__ = _CREATE_TICKET_DOC

    return [
        propose_update_customer_field,
        propose_reassign_ticket,
        propose_schedule_callback,
        propose_create_escalation,
        propose_create_ticket,
    ]
