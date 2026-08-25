from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.ids import new_id


class SupportAgent(Base):
    """The support-staff directory AND login identity (table name `agents`)"""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="support_agent")
    role_label: Mapped[str] = mapped_column(String(100), default="Support Agent")
    team: Mapped[str] = mapped_column(String(30), default="general")
    shift_start: Mapped[str] = mapped_column(String(10), default="09:00")
    shift_end: Mapped[str] = mapped_column(String(10), default="17:00")
    on_duty: Mapped[bool] = mapped_column(default=True)
    extension: Mapped[str | None] = mapped_column(String(20), default=None)
    active: Mapped[bool] = mapped_column(default=True)
    two_factor: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    assigned_tickets: Mapped[list["Ticket"]] = relationship(back_populates="assigned_agent")
