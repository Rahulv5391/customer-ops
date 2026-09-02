from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.chat_session import ChatSession, ChatSessionMessage


def get_or_create_session(db: Session, session_id: str, agent_id: str) -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is not None:
        if session.agent_id != agent_id:
            # One agent must never read another's chat history.
            raise PermissionError("This chat session belongs to a different agent.")
        return session

    session = ChatSession(id=session_id, agent_id=agent_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def add_message(db: Session, session_id: str, role: str, content: str) -> ChatSessionMessage:
    message = ChatSessionMessage(session_id=session_id, role=role, content=content)
    db.add(message)

    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is not None:
        session.last_active_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(message)
    return message


def get_recent_messages(db: Session, session_id: str, limit: int = 10) -> list[ChatSessionMessage]:
    rows = (
        db.query(ChatSessionMessage)
        .filter(ChatSessionMessage.session_id == session_id)
        .order_by(ChatSessionMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))
