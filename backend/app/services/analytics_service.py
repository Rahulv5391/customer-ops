from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.escalation import Escalation
from app.models.ticket import Ticket, TicketEvent

# A ticket is considered wrapped up (feeds resolution-time/CSAT/deflection)
# once it reaches either of these statuses - matches data/seed_data.py's
# own seeding logic, which sets resolved_at for exactly this pair.
_RESOLVED_STATUSES = ("resolved", "closed")


def ticket_volume_by_day(db: Session, days: int = 7) -> list[dict]:
    """One point per calendar day for the last `days` days (including
    today), zero-filled for days with no tickets - a chart with silent
    gaps looks broken, not "no data" (Architecture.md §4)."""
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)

    rows = (
        db.query(func.date(Ticket.created_at).label("day"), func.count(Ticket.id))
        .filter(func.date(Ticket.created_at) >= start.isoformat())
        .group_by("day")
        .all()
    )
    counts = {day: count for day, count in rows}
    return [
        {
            "date": (start + timedelta(days=i)).isoformat(),
            "count": counts.get((start + timedelta(days=i)).isoformat(), 0),
        }
        for i in range(days)
    ]


def avg_resolution_time_hours(db: Session) -> float | None:
    """Average of resolved_at - created_at, in hours, over resolved
    tickets. Computed in Python over the (small, demo-scope) row set
    rather than in-SQL datetime arithmetic, which SQLite doesn't handle
    natively - avoids a DB-specific query for a handful of rows."""
    resolved = db.query(Ticket).filter(Ticket.resolved_at.isnot(None)).all()
    if not resolved:
        return None
    total_hours = sum((t.resolved_at - t.created_at).total_seconds() / 3600 for t in resolved)
    return round(total_hours / len(resolved), 2)


def csat_average(db: Session) -> float | None:
    result = db.query(func.avg(Ticket.csat_score)).filter(Ticket.csat_score.isnot(None)).scalar()
    return round(result, 2) if result is not None else None


def deflection_rate(db: Session) -> float | None:
    """Proportion of AI-touched tickets (a TicketEvent with
    actor == "AI Assistant") that reached a resolved status without ever
    being escalated, over all AI-touched tickets regardless of their
    current status. An approximation, not a precise session-level metric -
    there's no persisted chat-session table to derive this from directly
    (Architecture.md §10)."""
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

    tickets = db.query(Ticket).filter(Ticket.id.in_(ai_touched_ids)).all()
    resolved_without_escalation = sum(
        1 for t in tickets if t.status in _RESOLVED_STATUSES and t.id not in escalated_ids
    )
    return round(resolved_without_escalation / len(ai_touched_ids), 4)


def pending_escalations_count(db: Session) -> int:
    return db.query(Escalation).filter(Escalation.status == "pending").count()


def tickets_resolved_today(db: Session) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    return (
        db.query(Ticket)
        .filter(Ticket.resolved_at.isnot(None))
        .filter(func.date(Ticket.resolved_at) == today)
        .count()
    )


def top_issue_category(db: Session, limit: int = 5) -> list[dict]:
    rows = (
        db.query(Ticket.category, func.count(Ticket.id).label("count"))
        .group_by(Ticket.category)
        .order_by(func.count(Ticket.id).desc())
        .limit(limit)
        .all()
    )
    return [{"category": category, "count": count} for category, count in rows]


def get_summary(db: Session) -> dict:
    return {
        "ticket_volume_7d": ticket_volume_by_day(db, days=7),
        "avg_resolution_time_hours": avg_resolution_time_hours(db),
        "csat_average": csat_average(db),
        "deflection_rate": deflection_rate(db),
    }
