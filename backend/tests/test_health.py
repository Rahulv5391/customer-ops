"""Tests the two health endpoints: `/` (trivial liveness, no DB touch) and
`/health` (server + DB readiness - meant to be pinged by an external uptime
service to keep a free-tier host/DB from idling out)."""

from unittest.mock import patch


def test_root_is_a_trivial_liveness_check(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health_reports_ok_when_the_db_is_reachable(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok"}


def test_health_reports_503_when_the_db_is_unreachable(client):
    with patch("app.main.Session.execute", side_effect=Exception("connection refused")):
        r = client.get("/health")
    assert r.status_code == 503
    assert r.json() == {"status": "degraded", "db": "unreachable"}


def test_health_requires_no_auth(client):
    """An uptime pinger has no way to authenticate - this must stay open,
    unlike every other endpoint in the app."""
    r = client.get("/health")
    assert r.status_code != 401