"""Verifies the team-lead-only surfaces a support agent should never reach
directly via the API, even though the frontend already hides them: GET
/escalations, GET /data-sources, and DELETE /kb/{id}."""

from app.crud import kb_document as kb_crud
from app.models.kb_document import KBDocument


def _make_kb_document(db):
    doc = KBDocument(
        title="Refund Policy",
        category="policy",
        version="v1",
        source_updated_at="2026-01-01",
        content_json="{}",
        content_hash="test-hash-1",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_list_escalations_requires_team_lead(client, agent_headers, lead_headers):
    r = client.get("/api/v1/escalations", headers=agent_headers)
    assert r.status_code == 403

    r = client.get("/api/v1/escalations", headers=lead_headers)
    assert r.status_code == 200


def test_get_escalation_requires_team_lead(client, agent_headers):
    r = client.get("/api/v1/escalations/some-id", headers=agent_headers)
    assert r.status_code == 403


def test_list_data_sources_requires_team_lead(client, agent_headers, lead_headers):
    r = client.get("/api/v1/data-sources", headers=agent_headers)
    assert r.status_code == 403

    r = client.get("/api/v1/data-sources", headers=lead_headers)
    assert r.status_code == 200


def test_delete_kb_document_requires_team_lead(client, db, agent_headers, lead_headers):
    doc = _make_kb_document(db)

    r = client.delete(f"/api/v1/kb/{doc.id}", headers=agent_headers)
    assert r.status_code == 403
    assert kb_crud.get_document(db, doc.id) is not None

    r = client.delete(f"/api/v1/kb/{doc.id}", headers=lead_headers)
    assert r.status_code == 204
    # The delete happened through the app's own request-scoped session -
    # evict this session's identity map so the next query re-reads actual
    # DB state via a fresh SELECT instead of trying to refresh (and
    # ObjectDeletedError-ing on) a row that's already gone.
    db.expunge_all()
    assert kb_crud.get_document(db, doc.id) is None


def test_support_agent_can_still_upload_and_edit_kb_documents(client, db, agent_headers):
    """Only delete is team-lead-gated - authoring stays open to any agent."""
    doc = _make_kb_document(db)
    r = client.patch(
        f"/api/v1/kb/{doc.id}", headers=agent_headers, json={"title": "Refund Policy (updated)"}
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Refund Policy (updated)"
