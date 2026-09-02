from app.crud import data_source as data_source_crud


def test_create_data_source_requires_team_lead(client, agent_headers, lead_headers):
    payload = {"name": "Test Zendesk", "connector_type": "zendesk"}

    r = client.post("/api/v1/data-sources", headers=agent_headers, json=payload)
    assert r.status_code == 403

    r = client.post("/api/v1/data-sources", headers=lead_headers, json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Test Zendesk"
    assert body["connector_type"] == "zendesk"
    # Freshly registered - never synced yet.
    assert body["last_synced_at"] is None
    assert body["sync_status"] == "healthy"
    assert body["sync_health_pct"] == 100


def test_create_data_source_shows_up_in_list_and_is_syncable(client, db, lead_headers):
    r = client.post(
        "/api/v1/data-sources",
        headers=lead_headers,
        json={"name": "Test Shopify", "connector_type": "shopify"},
    )
    assert r.status_code == 201
    created_id = r.json()["id"]

    listed = client.get("/api/v1/data-sources", headers=lead_headers)
    assert any(s["id"] == created_id for s in listed.json())

    synced = client.post(f"/api/v1/data-sources/{created_id}/sync", headers=lead_headers)
    assert synced.status_code == 200
    assert synced.json()["last_synced_at"] is not None


def test_create_data_source_is_audited(client, db, lead_headers):
    r = client.post(
        "/api/v1/data-sources",
        headers=lead_headers,
        json={"name": "Test Slack", "connector_type": "slack"},
    )
    created_id = r.json()["id"]

    from app.crud.audit_log import list_activity

    entries = list_activity(db, entity_type="data_source", entity_id=created_id)
    assert any(e.action_type == "create_data_source" for e in entries)


def test_create_data_source_requires_auth(client):
    r = client.post("/api/v1/data-sources", json={"name": "x", "connector_type": "zendesk"})
    assert r.status_code == 401


def test_delete_data_source_actually_removes_it(client, db, lead_headers):
    r = client.post(
        "/api/v1/data-sources",
        headers=lead_headers,
        json={"name": "Throwaway", "connector_type": "kb_repo"},
    )
    created_id = r.json()["id"]

    r = client.delete(f"/api/v1/data-sources/{created_id}", headers=lead_headers)
    assert r.status_code == 204

    db.expunge_all()
    assert data_source_crud.get_data_source(db, created_id) is None
