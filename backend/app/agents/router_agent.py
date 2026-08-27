from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.base_agent import BaseSubAgent
from app.agents.crm_agent import crm_agent
from app.agents.escalation_agent import escalation_agent
from app.agents.messages import UNAVAILABLE_MESSAGE
from app.agents.queue_agent import queue_agent
from app.agents.rag_agent import rag_agent
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger, new_trace
from app.core.sql_security import SQLSecurityViolation, execute_safe_read_query
from app.prompts.loader import load_prompt
from app.schemas.chat import ChatMessage

logger = get_logger("router_agent")

_NOT_YET_BUILT = {
    "analytics_query": "Reporting/analytics questions aren't available in this build yet.",
}


class RouterOutput(BaseModel):
    category: Literal[
        "crm_lookup",
        "crm_write",
        "queue_availability",
        "policy_qa",
        "escalation",
        "analytics_query",
        "greeting",
    ]
    sql_query: str | None = None
    action_type: str | None = None
    target_entity: str | None = None
    target_value: str | None = None
    reasoning: str = ""


class RouterAgent:
    def __init__(self):
        instruction = load_prompt("router")
        self._sub_agent = BaseSubAgent(
            agent_name="router_agent", instruction=instruction, output_schema=RouterOutput
        )

    async def route_message(
        self,
        db: Session,
        message: str,
        agent_name: str,
        role: str,
        active_entity_id: str | None = None,
        active_entity_type: str | None = None,
        trace_id: str | None = None,
    ) -> ChatMessage:
        with new_trace(trace_id):
            prompt_context = self._build_prompt(
                message, agent_name, role, active_entity_id, active_entity_type
            )
            try:
                parsed = await self._sub_agent.run(prompt_context, user_id=agent_name)
            except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
                logger.warning(f"Router classification failed: {exc}")
                return UNAVAILABLE_MESSAGE

            if parsed.category == "crm_lookup":
                return self._execute_read_path(db, parsed.sql_query)

            if parsed.category == "crm_write":
                return await crm_agent.handle_message(db, message, active_entity_id)

            if parsed.category == "queue_availability":
                return await queue_agent.handle_message(
                    db, message, active_entity_id, active_entity_type
                )

            if parsed.category == "policy_qa":
                return await rag_agent.handle_message(message)

            if parsed.category == "escalation":
                return await escalation_agent.handle_message(
                    db, message, active_entity_id, active_entity_type
                )

            if parsed.category == "greeting":
                return ChatMessage(
                    type="text",
                    content=(
                        "Hi! I can help you look up customers, check queue "
                        "availability, answer policy questions, and propose "
                        "account changes or escalations. What do you need?"
                    ),
                    status="final",
                )

            return ChatMessage(
                type="text",
                content=_NOT_YET_BUILT.get(parsed.category, "That capability isn't available yet."),
                status="final",
            )

    def _build_prompt(
        self,
        message: str,
        agent_name: str,
        role: str,
        active_entity_id: str | None,
        active_entity_type: str | None,
    ) -> str:
        if active_entity_id:
            active_entity_doc = (
                f"Active entity in context: type={active_entity_type}, id={active_entity_id}. "
                "Use this exact id if the message refers to 'this customer'/'them'/'they'."
            )
        else:
            active_entity_doc = "No active entity is currently in context."
        return (
            f"Agent: {agent_name} (role: {role}).\n"
            f"{active_entity_doc}\n"
            f"Message: {message}"
        )

    def _execute_read_path(self, db: Session, sql_query: str | None) -> ChatMessage:
        query = sql_query or "SELECT id, full_name, email, account_tier, status FROM customers LIMIT 20"
        try:
            columns, rows, table = execute_safe_read_query(db, query)
        except SQLSecurityViolation as exc:
            return ChatMessage(type="error", content=f"Security policy restriction: {exc}", status="final")
        except Exception as exc:
            return ChatMessage(type="error", content=f"Could not execute that lookup: {exc}", status="final")

        if not rows:
            return ChatMessage(type="text", content="No matching records found.", status="final")

        lines = [", ".join(f"{col}={val}" for col, val in zip(columns, row)) for row in rows[:20]]

        resolved_entity_id = None
        resolved_entity_type = None
        if len(rows) == 1 and table and "id" in columns:
            resolved_entity_id = str(rows[0][columns.index("id")])
            resolved_entity_type = table.rstrip("s")  # customers -> customer, escalations -> escalation

        return ChatMessage(
            type="text",
            content="\n".join(lines),
            status="final",
            resolved_entity_id=resolved_entity_id,
            resolved_entity_type=resolved_entity_type,
        )


router_agent = RouterAgent()
