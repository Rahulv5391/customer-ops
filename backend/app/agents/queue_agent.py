from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseSubAgent
from app.agents.messages import UNAVAILABLE_MESSAGE
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger
from app.crud.agent import list_agents
from app.crud.ticket import list_tickets
from app.models.agent import SupportAgent
from app.models.ticket import Ticket
from app.prompts.loader import load_prompt
from app.schemas.chat import ActionDiff, ChatMessage, PendingAction
from app.services.action_token import create_action_token
from app.services.agent_status import is_on_duty
from app.services.conversation import with_history
from app.services.entity_resolution import AmbiguousEntityError, resolve_entity
from app.services.ticket_resolution import resolve_ticket_context

logger = get_logger("queue_agent")

MAX_DETAIL_ROWS = 20

_NO_TICKET_FOUND = ChatMessage(
    type="text",
    content="I couldn't find that ticket. Try its ticket number.",
    status="final",
)


class QueueAgentOutput(BaseModel):
    intent: Literal["availability_check", "schedule_callback", "reassign_ticket"]
    channel: str | None = None
    category: str | None = None
    ticket_hint: str | None = None
    target_agent_id: str | None = None
    callback_time: str | None = None
    include_details: bool = False
    summary: str = ""


class QueueAgent:
    def __init__(self):
        instruction = load_prompt("queue_agent")
        self._sub_agent = BaseSubAgent(
            agent_name="queue_agent", instruction=instruction, output_schema=QueueAgentOutput
        )

    async def handle_message(self, db: Session, message: str, history: str = "") -> ChatMessage:
        try:
            parsed = await self._sub_agent.run(with_history(history, message), user_id="queue_agent")
        except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
            logger.warning(f"Queue agent classification failed: {exc}")
            return UNAVAILABLE_MESSAGE

        if parsed.intent == "reassign_ticket":
            return self._propose_reassign(db, parsed, message)

        if parsed.intent == "schedule_callback":
            return self._propose_callback(db, parsed)

        return self._availability_summary(
            db, channel=parsed.channel, category=parsed.category, include_details=parsed.include_details
        )

    def _propose_reassign(
        self, db: Session, parsed: QueueAgentOutput, raw_message: str
    ) -> ChatMessage:
        ticket = resolve_ticket_context(db, parsed.ticket_hint)
        if not ticket:
            return _NO_TICKET_FOUND

        if not parsed.target_agent_id:
            return ChatMessage(
                type="text", content="Which agent should I reassign this to?", status="final"
            )

        try:
            target_agent = resolve_entity(list_agents(db), parsed.target_agent_id, raw_message)
        except AmbiguousEntityError as exc:
            names = ", ".join(f"{a.full_name} ({a.team})" for a in exc.matches[:5])
            return ChatMessage(
                type="text",
                content=f"More than one agent matches that: {names}. Try their email instead.",
                status="final",
            )
        if not target_agent:
            return ChatMessage(
                type="text",
                content=f"I couldn't find an agent matching '{parsed.target_agent_id}'.",
                status="final",
            )

        before_agent_name = ticket.assigned_agent.full_name if ticket.assigned_agent else "Unassigned"
        return ChatMessage(
            type="action-confirmation",
            content=(
                f"Reassign ticket {ticket.ticket_number} from {before_agent_name} "
                f"to {target_agent.full_name}?"
            ),
            status="pending_confirmation",
            action_diff=ActionDiff(
                # Human-readable names for display - the token (not this
                # diff) is what's actually trusted to carry the real ids
                # when the action gets confirmed.
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

    def _propose_callback(self, db: Session, parsed: QueueAgentOutput) -> ChatMessage:
        ticket = resolve_ticket_context(db, parsed.ticket_hint)
        if not ticket:
            return _NO_TICKET_FOUND

        if not parsed.callback_time:
            return ChatMessage(
                type="text", content="What time should the callback be scheduled for?", status="final"
            )

        return ChatMessage(
            type="action-confirmation",
            content=f"Schedule a callback on ticket {ticket.ticket_number} for {parsed.callback_time}?",
            status="pending_confirmation",
            action_diff=ActionDiff(before={}, after={"callback_time": parsed.callback_time}),
            pending_action=PendingAction(
                token=create_action_token(
                    action_type="schedule_callback",
                    entity_type="ticket",
                    entity_id=ticket.id,
                    field_value=parsed.callback_time,
                ),
                action_type="schedule_callback",
                entity_type="ticket",
                entity_id=ticket.id,
                field_value=parsed.callback_time,
            ),
        )

    def _availability_summary(
        self, db: Session, channel: str | None, category: str | None, include_details: bool = False
    ) -> ChatMessage:
        agents: list[SupportAgent] = list_agents(db)
        agents_online = sum(1 for a in agents if is_on_duty(a.shift_start, a.shift_end))

        unassigned: list[Ticket] = list_tickets(db, status="unassigned")

        lines = [
            f"Agents online: {agents_online} / {len(agents)}",
            f"Unassigned tickets: {len(unassigned)}",
        ]
        if channel:
            channel_tickets = list_tickets(db, channel=channel)
            lines.append(f"Tickets in {channel}: {len(channel_tickets)}")
        if category:
            category_tickets = [t for t in list_tickets(db) if t.category == category]
            lines.append(f"Tickets in category '{category}': {len(category_tickets)}")

        if include_details:
            detail_tickets = list_tickets(db, status="unassigned", channel=channel)
            if category:
                detail_tickets = [t for t in detail_tickets if t.category == category]

            lines.append("")
            for ticket in detail_tickets[:MAX_DETAIL_ROWS]:
                lines.append(
                    f"{ticket.ticket_number} | {ticket.subject} | {ticket.channel} | "
                    f"{ticket.priority} | {ticket.category} | {ticket.created_at}"
                )
            remaining = len(detail_tickets) - MAX_DETAIL_ROWS
            if remaining > 0:
                lines.append(f"...and {remaining} more")

        return ChatMessage(type="text", content="\n".join(lines), status="final")


queue_agent = QueueAgent()
