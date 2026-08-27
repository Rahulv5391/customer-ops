def _create_customer(client, headers, **overrides):
    payload = {"full_name": "Ada Lovelace", "email": "ada@example.com"}
    payload.update(overrides)
    return client.post("/api/v1/customers", json=payload, headers=headers)


def test_list_customers_requires_auth(client):
    r = client.get("/api/v1/customers")
    assert r.status_code == 401


def test_create_and_get_customer(client, agent_headers):
    r = _create_customer(client, agent_headers)
    assert r.status_code == 201
    customer_id = r.json()["id"]

    r = client.get(f"/api/v1/customers/{customer_id}", headers=agent_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["full_name"] == "Ada Lovelace"
    assert body["orders"] == []
    assert body["tickets"] == []


def test_get_customer_404_for_missing_id(client, agent_headers):
    r = client.get("/api/v1/customers/does-not-exist", headers=agent_headers)
    assert r.status_code == 404


def test_list_customers_returns_created_customer(client, agent_headers):
    _create_customer(client, agent_headers)
    r = client.get("/api/v1/customers", headers=agent_headers)
    assert r.status_code == 200
    assert any(c["email"] == "ada@example.com" for c in r.json())


def test_list_customers_query_filter(client, agent_headers):
    _create_customer(client, agent_headers, email="daniel@example.com", full_name="Daniel Brooks")
    _create_customer(client, agent_headers, email="ada@example.com", full_name="Ada Lovelace")

    r = client.get("/api/v1/customers?query=Daniel", headers=agent_headers)
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["email"] == "daniel@example.com"


def test_patch_customer_updates_field(client, agent_headers):
    r = _create_customer(client, agent_headers)
    customer_id = r.json()["id"]

    r = client.patch(
        f"/api/v1/customers/{customer_id}", json={"phone": "+1-555-0100"}, headers=agent_headers
    )
    assert r.status_code == 200
    assert r.json()["phone"] == "+1-555-0100"


def test_patch_customer_404_for_missing_id(client, agent_headers):
    r = client.patch(
        "/api/v1/customers/does-not-exist", json={"phone": "+1-555-0100"}, headers=agent_headers
    )
    assert r.status_code == 404


def test_add_note_sets_author_from_authenticated_agent(client, agent_headers, support_agent):
    r = _create_customer(client, agent_headers)
    customer_id = r.json()["id"]

    r = client.post(
        f"/api/v1/customers/{customer_id}/notes",
        json={"body": "Called about a billing question."},
        headers=agent_headers,
    )
    assert r.status_code == 201
    assert r.json()["author"] == support_agent.full_name
    assert r.json()["body"] == "Called about a billing question."


def test_add_note_404_for_missing_customer(client, agent_headers):
    r = client.post(
        "/api/v1/customers/does-not-exist/notes",
        json={"body": "irrelevant"},
        headers=agent_headers,
    )
    assert r.status_code == 404
