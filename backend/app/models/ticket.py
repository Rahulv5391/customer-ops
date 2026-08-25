from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.ids import new_id, new_reference


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    ticket_number: Mapped[str] = mapped_column(
        String(20), unique=True, default=lambda: new_reference("TCK")
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    channel: Mapped[str] = mapped_column(String(20), default="email")
    subject: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="unassigned", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    assigned_agent_id: Mapped[str | None] = mapped_column(
        ForeignKey("agents.id"), default=None, index=True
    )
    category: Mapped[str] = mapped_column(String(30), default="other")
    csat_score: Mapped[float | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(default=None)

    customer: Mapped["Customer"] = relationship(back_populates="tickets")
    assigned_agent: Mapped["SupportAgent | None"] = relationship(
        back_populates="assigned_tickets"
    )
    events: Mapped[list["TicketEvent"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )
    escalations: Mapped[list["Escalation"]] = relationship(back_populates="ticket")


class TicketEvent(Base):
    __tablename__ = "ticket_events"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(30))
    actor: Mapped[str] = mapped_column(String(150))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    ticket: Mapped["Ticket"] = relationship(back_populates="events")
