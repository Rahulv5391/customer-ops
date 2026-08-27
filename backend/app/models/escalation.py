from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.ids import new_id, new_reference


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    escalation_number: Mapped[str] = mapped_column(
        String(20), unique=True, default=lambda: new_reference("ESC")
    )
    ticket_id: Mapped[str | None] = mapped_column(
        ForeignKey("tickets.id"), default=None, index=True
    )
    escalation_type: Mapped[str] = mapped_column(String(30))
    requested_action: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    policy_citation: Mapped[str | None] = mapped_column(Text, default=None)
    rejection_note: Mapped[str | None] = mapped_column(Text, default=None)
    # Set server-side from the authenticated user.
    requested_by: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)

    ticket: Mapped["Ticket | None"] = relationship(back_populates="escalations")
