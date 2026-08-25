from datetime import datetime, timezone

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.ids import new_id


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    full_name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), default=None)
    company: Mapped[str | None] = mapped_column(String(150), default=None)
    account_tier: Mapped[str] = mapped_column(String(20), default="free")
    address_line1: Mapped[str | None] = mapped_column(String(200), default=None)
    address_line2: Mapped[str | None] = mapped_column(String(200), default=None)
    city: Mapped[str | None] = mapped_column(String(100), default=None)
    region: Mapped[str | None] = mapped_column(String(100), default=None)
    postal_code: Mapped[str | None] = mapped_column(String(20), default=None)
    country: Mapped[str | None] = mapped_column(String(100), default=None)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    notes: Mapped[list["CustomerNote"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
