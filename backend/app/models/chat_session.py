from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.ids import new_id


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    # Client-generated (crypto.randomUUID(), 36 chars w/ dashes) - the one
    # deliberate deviation from this codebase's normal String(32)/new_id()
    # PK convention, since the id must be stable across a browser tab's
    # whole lifetime and is minted client-side, not server-side.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    last_active_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))

    messages: Mapped[list["ChatSessionMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatSessionMessage.created_at",
    )


class ChatSessionMessage(Base):
    __tablename__ = "chat_session_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), index=True
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
