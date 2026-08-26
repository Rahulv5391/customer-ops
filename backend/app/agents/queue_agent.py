from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseSubAgent
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger
from app.crud.agent import list_agents
from app.crud.ticket import list_tickets
from app.models.agent import SupportAgent
from app.models.ticket import Ticket
from app.prompts.loader import load_prompt
from app.schemas.chat import ChatMessage

logger = get_logger("queue_agent")

MAX_DETAIL_ROWS = 20

_UNAVAILABLE_MESSAGE = ChatMessage(
    type="error",
    content="The AI assistant is temporarily unavailable. Please try again in a moment.",
    status="final",
)

_NOT_YET_BUILT = {
    "schedule_callback": "Scheduling a callback through chat isn't available in this build yet.",
    "reassign_ticket": "Reassigning a ticket through chat isn't available in this build yet.",
}


class QueueAgentOutput(BaseModel):
    intent: Literal["availability_check", "schedule_callback", "reassign_ticket"]
    channel: str | None = None
    category: str | None = None
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

    async def handle_message(self, db: Session, message: str) -> ChatMessage:
        try:
            parsed = await self._sub_agent.run(message, user_id="queue_agent")
        except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
            logger.warning(f"Queue agent classification failed: {exc}")
            return _UNAVAILABLE_MESSAGE

        if parsed.intent != "availability_check":
            return ChatMessage(
                type="text",
                content=_NOT_YET_BUILT.get(parsed.intent, "That capability isn't available yet."),
                status="final",
            )

        return self._availability_summary(
            db, channel=parsed.channel, category=parsed.category, include_details=parsed.include_details
        )

    def _availability_summary(
        self, db: Session, channel: str | None, category: str | None, include_details: bool = False
    ) -> ChatMessage:
        agents: list[SupportAgent] = list_agents(db)
        agents_online = sum(1 for a in agents if a.on_duty)

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
