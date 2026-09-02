"""Every tool here is a pure read - it builds the exact, final ChatMessage
the user will see directly in Python (deterministic formatting, never LLM
paraphrase) and captures it as a terminal ToolOutcome. See tools/base.py's
module docstring for why the model never sees the real data."""

from typing import Callable, Literal

from sqlalchemy.orm import Session

from app.agents.tools.base import ALREADY_SHOWN, ToolOutcome, logged_tool
from app.core.sql_security import SQLSecurityViolation, execute_safe_read_query
from app.crud.agent import list_agents
from app.crud.customer import get_customer_with_history, list_customers
from app.crud.ticket import list_tickets
from app.prompts.loader import load_prompt
from app.schemas.chat import ChatMessage
from app.services import analytics_service
from app.services.agent_status import is_on_duty
from app.services.entity_resolution import AmbiguousEntityError, resolve_entity

MAX_DETAIL_ROWS = 20

_NOT_FOUND = ChatMessage(
    type="text",
    content="I couldn't find a matching customer. Try their full name, email, or account id.",
    status="final",
)

_QUERY_RECORDS_DOC = load_prompt("tools/query_records")
_FIND_CUSTOMER_DOC = load_prompt("tools/find_customer")
_QUEUE_AVAILABILITY_DOC = load_prompt("tools/queue_availability")
_REPORTING_METRIC_DOC = load_prompt("tools/reporting_metric")


def _format_rows_markdown(columns: list[str], rows: list[tuple]) -> str:
    """Bolded field labels, a bullet per row once there's more than one.
    The `id` column (always requested so a result can be referenced by a
    follow-up in conversation history) is dropped from display - it's
    meaningless to a human reading the chat. A foreign key explicitly asked
    for (e.g. `assigned_agent_id`) is a real answer and is kept."""

    def label(col: str) -> str:
        return col.replace("_", " ").title()

    def display_pairs(row: tuple) -> list[tuple[str, object]]:
        pairs = [(col, val) for col, val in zip(columns, row) if col != "id"]
        return pairs or list(zip(columns, row))

    if len(rows) == 1:
        return "\n".join(f"**{label(col)}:** {val}" for col, val in display_pairs(rows[0]))

    bullets = []
    for row in rows:
        fields = " · ".join(f"**{label(col)}:** {val}" for col, val in display_pairs(row))
        bullets.append(f"- {fields}")
    return "\n".join(bullets)


def build_tools(db: Session, outcomes: list[ToolOutcome]) -> list[Callable]:
    @logged_tool
    def query_records(sql_query: str) -> str:
        try:
            columns, rows, _table = execute_safe_read_query(db, sql_query)
        except SQLSecurityViolation as exc:
            outcomes.append(
                ToolOutcome(
                    chat_message=ChatMessage(
                        type="error", content=f"Security policy restriction: {exc}", status="final"
                    )
                )
            )
            return ALREADY_SHOWN
        except Exception as exc:
            outcomes.append(
                ToolOutcome(
                    chat_message=ChatMessage(
                        type="error", content=f"Could not execute that lookup: {exc}", status="final"
                    )
                )
            )
            return ALREADY_SHOWN

        if not rows:
            outcomes.append(
                ToolOutcome(
                    chat_message=ChatMessage(type="text", content="No matching records found.", status="final")
                )
            )
            return ALREADY_SHOWN

        outcomes.append(
            ToolOutcome(
                chat_message=ChatMessage(
                    type="text", content=_format_rows_markdown(columns, rows[:20]), status="final"
                )
            )
        )
        return ALREADY_SHOWN

    query_records.__doc__ = _QUERY_RECORDS_DOC

    @logged_tool
    def find_customer(customer_hint: str, include_history: bool = False) -> str:
        candidates = list_customers(db, limit=1000)
        try:
            customer = resolve_entity(candidates, customer_hint, customer_hint)
        except AmbiguousEntityError as exc:
            names = ", ".join(f"{c.full_name} ({c.email})" for c in exc.matches[:5])
            outcomes.append(
                ToolOutcome(
                    chat_message=ChatMessage(
                        type="text",
                        content=f"More than one customer matches that: {names}. Try their email or customer id instead.",
                        status="final",
                    )
                )
            )
            return ALREADY_SHOWN
        if not customer:
            outcomes.append(ToolOutcome(chat_message=_NOT_FOUND))
            return ALREADY_SHOWN

        if not include_history:
            lines = [
                f"{customer.full_name} ({customer.email})",
                f"Company: {customer.company or '—'} | Tier: {customer.account_tier} | Status: {customer.status}",
                f"Phone: {customer.phone or '—'}",
            ]
            outcomes.append(
                ToolOutcome(chat_message=ChatMessage(type="text", content="\n".join(lines), status="final"))
            )
            return ALREADY_SHOWN

        with_history_data = get_customer_with_history(db, customer.id)
        if not with_history_data:
            outcomes.append(ToolOutcome(chat_message=_NOT_FOUND))
            return ALREADY_SHOWN

        lines = [f"{with_history_data.full_name} - order/ticket history:"]
        if with_history_data.orders:
            for order in with_history_data.orders[:3]:
                lines.append(f"  Order {order.order_number}: {order.status}, ${order.total_amount}")
        else:
            lines.append("  No orders on file.")
        if with_history_data.tickets:
            for ticket in with_history_data.tickets[:3]:
                lines.append(f"  Ticket {ticket.ticket_number}: {ticket.subject} ({ticket.status})")
        else:
            lines.append("  No tickets on file.")
        outcomes.append(
            ToolOutcome(chat_message=ChatMessage(type="text", content="\n".join(lines), status="final"))
        )
        return ALREADY_SHOWN

    find_customer.__doc__ = _FIND_CUSTOMER_DOC

    @logged_tool
    def check_queue_availability(
        channel: str | None = None, category: str | None = None, include_details: bool = False
    ) -> str:
        agents = list_agents(db)
        agents_online = sum(1 for a in agents if is_on_duty(a.shift_start, a.shift_end))
        unassigned = list_tickets(db, status="unassigned")

        lines = [
            f"Agents online: {agents_online} / {len(agents)}",
            f"Unassigned tickets: {len(unassigned)}",
        ]
        if channel:
            lines.append(f"Tickets in {channel}: {len(list_tickets(db, channel=channel))}")
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

        outcomes.append(
            ToolOutcome(chat_message=ChatMessage(type="text", content="\n".join(lines), status="final"))
        )
        return ALREADY_SHOWN

    check_queue_availability.__doc__ = _QUEUE_AVAILABILITY_DOC

    @logged_tool
    def get_reporting_metric(
        metric: Literal[
            "summary", "ticket_volume", "top_categories", "escalations_pending", "tickets_resolved_today"
        ] = "summary",
    ) -> str:
        if metric == "ticket_volume":
            points = analytics_service.ticket_volume_by_day(db, days=7)
            lines = [f"{p['date']}: {p['count']} tickets" for p in points]
            content = "Ticket volume, last 7 days:\n" + "\n".join(lines)

        elif metric == "top_categories":
            rows = analytics_service.top_issue_category(db, limit=5)
            if not rows:
                content = "No ticket category data yet."
            else:
                lines = [f"{r['category']}: {r['count']} tickets" for r in rows]
                content = "Top issue categories:\n" + "\n".join(lines)

        elif metric == "escalations_pending":
            content = f"Pending escalations: {analytics_service.pending_escalations_count(db)}"

        elif metric == "tickets_resolved_today":
            content = f"Tickets resolved today: {analytics_service.tickets_resolved_today(db)}"

        else:  # "summary"
            data = analytics_service.get_summary(db)
            total_volume = sum(p["count"] for p in data["ticket_volume_7d"])
            lines = [f"Ticket volume (last 7 days): {total_volume} total"]
            if data["avg_resolution_time_hours"] is not None:
                lines.append(f"Avg resolution time: {data['avg_resolution_time_hours']} hours")
            if data["csat_average"] is not None:
                lines.append(f"CSAT average: {data['csat_average']} / 5")
            if data["deflection_rate"] is not None:
                lines.append(f"Deflection rate: {data['deflection_rate'] * 100:.1f}%")
            content = "\n".join(lines)

        outcomes.append(ToolOutcome(chat_message=ChatMessage(type="text", content=content, status="final")))
        return ALREADY_SHOWN

    get_reporting_metric.__doc__ = _REPORTING_METRIC_DOC

    return [query_records, find_customer, check_queue_availability, get_reporting_metric]
