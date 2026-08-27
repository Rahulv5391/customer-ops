"""Builds a small, deterministic dataset directly via the ORM so every
analytics aggregation has an exact expected value."""

from datetime import datetime, timedelta, timezone

from app.models.customer import Customer
from app.models.escalation import Escalation
from app.models.ticket import Ticket, TicketEvent


def _now():
    return datetime.now(timezone.utc)


def _seed_dataset(db):
    customer = Customer(full_name="Ada Lovelace", email="ada@example.com")
    db.add(customer)
    db.commit()

    now = _now()
    tickets = [
        # Resolved today, 4 hours to resolve, CSAT 4.0, AI-touched, no escalation.
        Ticket(
            customer_id=customer.id,
            subject="Refund request",
            status="resolved",
            category="billing",
            csat_score=4.0,
            created_at=now - timedelta(hours=4),
            resolved_at=now,
        ),
        # Resolved today, 2 hours to resolve, CSAT 5.0, AI-touched, no escalation.
        Ticket(
            customer_id=customer.id,
            subject="Late delivery",
            status="closed",
            category="shipping",
            csat_score=5.0,
            created_at=now - timedelta(hours=2),
            resolved_at=now,
        ),
        # Resolved 3 days ago (not today), no CSAT recorded, AI-touched, escalated.
        Ticket(
            customer_id=customer.id,
            subject="Billing dispute",
            status="resolved",
            category="billing",
            csat_score=None,
            created_at=now - timedelta(days=3, hours=6),
            resolved_at=now - timedelta(days=3),
        ),
        # Still open - not resolved, not counted in resolution/CSAT/deflection numerator.
        Ticket(
            customer_id=customer.id,
            subject="API question",
            status="in_progress",
            category="technical",
            csat_score=None,
            created_at=now - timedelta(hours=1),
            resolved_at=None,
        ),
    ]
    db.add_all(tickets)
    db.commit()

    # Every ticket gets an AI Assistant event, matching data/seed_data.py's
    # own pattern - all 4 tickets above are "AI-touched" for deflection_rate.
    for ticket in tickets:
        db.add(TicketEvent(ticket_id=ticket.id, event_type="status_change", actor="AI Assistant"))
    db.commit()

    # The 3rd ticket (billing dispute) escalated - excludes it from the
    # deflection numerator even though it did eventually resolve.
    db.add(
        Escalation(
            ticket_id=tickets[2].id,
            escalation_type="refund_approval",
            requested_action="Refund outside policy window.",
            status="approved",
            requested_by="Test Lead",
        )
    )
    db.add(
        Escalation(
            ticket_id=None,
            escalation_type="account_credit",
            requested_action="Retention discount above limit.",
            status="pending",
            requested_by="Test Lead",
        )
    )
    db.commit()
    return tickets


def test_summary_matches_hand_computed_expected_values(client, agent_headers, db):
    _seed_dataset(db)

    r = client.get("/api/v1/analytics/summary", headers=agent_headers)
    assert r.status_code == 200
    body = r.json()

    assert len(body["ticket_volume_7d"]) == 7
    assert sum(p["count"] for p in body["ticket_volume_7d"]) == 4

    # 4h, 2h, and 6h (the 3rd ticket's 3-day offset is common to both
    # created_at and resolved_at, so only the 6h differential counts) ->
    # (4 + 2 + 6) / 3 = 4.0
    assert body["avg_resolution_time_hours"] == 4.0

    # avg of 4.0 and 5.0 (only 2 tickets have a csat_score) = 4.5
    assert body["csat_average"] == 4.5

    # 4 AI-touched tickets total; 2 resolved without escalation (the two
    # resolved-today ones) -> 2/4 = 0.5. The 3rd resolved but escalated
    # (excluded from numerator); the 4th is still open (excluded too).
    assert body["deflection_rate"] == 0.5


def test_ticket_volume_endpoint_zero_fills_empty_days(client, agent_headers, db):
    _seed_dataset(db)
    r = client.get("/api/v1/analytics/ticket-volume?days=7", headers=agent_headers)
    assert r.status_code == 200
    points = r.json()
    assert len(points) == 7
    assert any(p["count"] == 0 for p in points)  # at least one quiet day in a fresh 7-day window


def test_top_issue_categories_ordered_by_count_desc(client, agent_headers, db):
    _seed_dataset(db)
    r = client.get("/api/v1/analytics/top-issue-categories?limit=5", headers=agent_headers)
    assert r.status_code == 200
    rows = r.json()
    assert rows[0] == {"category": "billing", "count": 2}
    assert {"shipping", "technical"}.issubset({row["category"] for row in rows})


def test_escalations_pending_counts_only_pending_status(client, agent_headers, db):
    _seed_dataset(db)
    r = client.get("/api/v1/analytics/escalations-pending", headers=agent_headers)
    assert r.status_code == 200
    assert r.json()["count"] == 1  # the approved one must not be counted


def test_tickets_resolved_today_excludes_older_resolutions(client, agent_headers, db):
    _seed_dataset(db)
    r = client.get("/api/v1/analytics/tickets-resolved-today", headers=agent_headers)
    assert r.status_code == 200
    assert r.json()["count"] == 2  # not the one resolved 3 days ago


def test_analytics_endpoints_handle_empty_database(client, agent_headers):
    r = client.get("/api/v1/analytics/summary", headers=agent_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["avg_resolution_time_hours"] is None
    assert body["csat_average"] is None
    assert body["deflection_rate"] is None
    assert all(p["count"] == 0 for p in body["ticket_volume_7d"])


def test_analytics_requires_auth(client):
    assert client.get("/api/v1/analytics/summary").status_code == 401
