from app.core.security import hash_password
from app.crud import chat_session as chat_session_crud
from app.models.agent import SupportAgent
from app.models.chat_session import ChatSession


def _make_agent(db, email="chat.agent@example.com"):
    agent = SupportAgent(
        full_name="Chat Agent", email=email, password_hash=hash_password("password123")
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def test_get_or_create_session_creates_once_and_is_idempotent(db):
    agent = _make_agent(db)
    session_id = "11111111-1111-1111-1111-111111111111"

    created = chat_session_crud.get_or_create_session(db, session_id, agent.id)
    assert created.id == session_id
    assert created.agent_id == agent.id

    fetched = chat_session_crud.get_or_create_session(db, session_id, agent.id)
    assert fetched.id == created.id
    assert db.query(ChatSession).count() == 1


def test_get_or_create_session_rejects_a_different_agents_session(db):
    owner = _make_agent(db, email="owner@example.com")
    other = _make_agent(db, email="other@example.com")
    session_id = "22222222-2222-2222-2222-222222222222"
    chat_session_crud.get_or_create_session(db, session_id, owner.id)

    try:
        chat_session_crud.get_or_create_session(db, session_id, other.id)
        assert False, "expected a PermissionError"
    except PermissionError:
        pass


def test_add_message_and_get_recent_messages_preserve_order(db):
    agent = _make_agent(db)
    session = chat_session_crud.get_or_create_session(db, "session-order", agent.id)

    chat_session_crud.add_message(db, session.id, role="user", content="first")
    chat_session_crud.add_message(db, session.id, role="assistant", content="second")
    chat_session_crud.add_message(db, session.id, role="user", content="third")

    recent = chat_session_crud.get_recent_messages(db, session.id)
    assert [m.content for m in recent] == ["first", "second", "third"]
    assert [m.role for m in recent] == ["user", "assistant", "user"]


def test_get_recent_messages_returns_only_the_most_recent_up_to_limit(db):
    agent = _make_agent(db)
    session = chat_session_crud.get_or_create_session(db, "session-limit", agent.id)

    for i in range(15):
        chat_session_crud.add_message(db, session.id, role="user", content=f"turn {i}")

    recent = chat_session_crud.get_recent_messages(db, session.id, limit=10)
    assert len(recent) == 10
    assert [m.content for m in recent] == [f"turn {i}" for i in range(5, 15)]
