from app.core.security import hash_password
from app.crud import customer as customer_crud
from app.crud import ticket as ticket_crud
from app.models.agent import SupportAgent
from app.schemas.customer import CustomerCreate
from app.schemas.ticket import TicketCreate


def _make_customer(db):
    return customer_crud.create_customer(
        db, CustomerCreate(full_name="Ada Lovelace", email="ada@example.com")
    )


def _make_ticket(db, customer_id, **overrides):
    data = {"customer_id": customer_id, "subject": "Order never arrived"}
    data.update(overrides)
    return ticket_crud.create_ticket(db, TicketCreate(**data))


def _flatten(board_json):
    return [t for channel in board_json for col in channel["columns"] for t in col["tickets"]]


def _other_agent(db):
    other = SupportAgent(
        full_name="Other Agent",
        email="other.agent@example.com",
        password_hash=hash_password("password123"),
        role="support_agent",
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    return other


def test_board_requires_auth(client):
    r = client.get("/api/v1/tickets/board")
    assert r.status_code == 401


def test_board_scopes_support_agent_to_own_and_unassigned_tickets(client, db, agent_headers, support_agent):
    customer = _make_customer(db)
    mine = _make_ticket(db, customer.id, subject="Mine", assigned_agent_id=support_agent.id)
    unassigned = _make_ticket(db, customer.id, subject="Unassigned", assigned_agent_id=None)
    other = _other_agent(db)
    someone_elses = _make_ticket(db, customer.id, subject="Someone else's", assigned_agent_id=other.id)

    r = client.get("/api/v1/tickets/board", headers=agent_headers)
    assert r.status_code == 200
    ids = {t["id"] for t in _flatten(r.json())}

    assert mine.id in ids
    assert unassigned.id in ids
    assert someone_elses.id not in ids


def test_board_shows_every_ticket_to_team_lead(client, db, lead_headers, support_agent):
    customer = _make_customer(db)
    mine = _make_ticket(db, customer.id, subject="Agent's", assigned_agent_id=support_agent.id)
    unassigned = _make_ticket(db, customer.id, subject="Unassigned", assigned_agent_id=None)
    other = _other_agent(db)
    someone_elses = _make_ticket(db, customer.id, subject="Someone else's", assigned_agent_id=other.id)

    r = client.get("/api/v1/tickets/board", headers=lead_headers)
    assert r.status_code == 200
    ids = {t["id"] for t in _flatten(r.json())}

    assert {mine.id, unassigned.id, someone_elses.id}.issubset(ids)
