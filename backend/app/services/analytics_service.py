from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.escalation import Escalation
from app.models.ticket import Ticket, TicketEvent

# Statuses that count as a ticket being wrapped up.
_RESOLVED_STATUSES = ("resolved", "closed")


def ticket_volume_by_day(db: Session, days: int = 7, agent_id: str | None = None) -> list[dict]:
    """One point per calendar day for the last `days` days, including
    today, zero-filled for days with no tickets. `agent_id` scopes to
    tickets assigned to that agent (used for a support_agent's own
    dashboard - team leads see the org-wide count)."""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)

    q = db.query(func.date(Ticket.created_at).label("day"), func.count(Ticket.id)).filter(
        func.date(Ticket.created_at) >= start.isoformat()
    )
    if agent_id:
        q = q.filter(Ticket.assigned_agent_id == agent_id)
    rows = q.group_by("day").all()

    counts = {day: count for day, count in rows}
    return [
        {
            "date": (start + timedelta(days=i)).isoformat(),
            "count": counts.get((start + timedelta(days=i)).isoformat(), 0),
        }
        for i in range(days)
    ]


def avg_resolution_time_hours(db: Session, agent_id: str | None = None) -> float | None:
    """Average of resolved_at - created_at, in hours, over resolved tickets."""
    q = db.query(Ticket).filter(Ticket.resolved_at.isnot(None))
    if agent_id:
        q = q.filter(Ticket.assigned_agent_id == agent_id)
    resolved = q.all()
    if not resolved:
        return None
    total_hours = sum((t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved)
    return round(total_hours / len(resolved), 2)


def csat_average(db: Session, agent_id: str | None = None) -> float | None:
    q = db.query(func.avg(Ticket.csat_score)).filter(Ticket.csat_score.isnot(None))
    if agent_id:
        q = q.filter(Ticket.assigned_agent_id == agent_id)
    result = q.scalar()
    return round(result, 2) if result is not None else None


def deflection_rate(db: Session, agent_id: str | None = None) -> float | None:
    """Proportion of AI-touched tickets that resolved without being
    escalated, out of all AI-touched tickets (optionally scoped to one
    agent's assigned tickets)."""
    ai_touched_ids = {
        row[0]
        for row in db.query(TicketEvent.ticket_id)
        .filter(TicketEvent.actor == "AI Assistant")
        .distinct()
        .all()
    }
    if not ai_touched_ids:
        return None

    escalated_ids = {
        row[0]
        for row in db.query(Escalation.ticket_id).filter(Escalation.ticket_id.isnot(None)).distinct().all()
    }

    q = db.query(Ticket).filter(Ticket.id.in_(ai_touched_ids))
    if agent_id:
        q = q.filter(Ticket.assigned_agent_id == agent_id)
    tickets = q.all()
    if not tickets:
        return None

    resolved_without_escalation = sum(
        1 for t in tickets if t.status in _RESOLVED_STATUSES and t.id not in escalated_ids
    )
    return round(resolved_without_escalation / len(tickets), 4)


def pending_escalations_count(db: Session) -> int:
    return db.query(Escalation).filter(Escalation.status == "pending").count()


def tickets_resolved_today(db: Session, agent_id: str | None = None) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    q = db.query(Ticket).filter(Ticket.resolved_at.isnot(None)).filter(
        func.date(Ticket.resolved_at) == today
    )
    if agent_id:
        q = q.filter(Ticket.assigned_agent_id == agent_id)
    return q.count()


def top_issue_category(db: Session, limit: int = 5, agent_id: str | None = None) -> list[dict]:
    q = db.query(Ticket.category, func.count(Ticket.id).label("count"))
    if agent_id:
        q = q.filter(Ticket.assigned_agent_id == agent_id)
    rows = q.group_by(Ticket.category).order_by(func.count(Ticket.id).desc()).limit(limit).all()
    return [{"category": category, "count": count} for category, count in rows]


def get_summary(db: Session, agent_id: str | None = None) -> dict:
    return {
        "ticket_volume_7d": ticket_volume_by_day(db, days=7, agent_id=agent_id),
        "avg_resolution_time_hours": avg_resolution_time_hours(db, agent_id=agent_id),
        "csat_average": csat_average(db, agent_id=agent_id),
        "deflection_rate": deflection_rate(db, agent_id=agent_id),
    }
