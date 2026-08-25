from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.ids import new_id, new_reference


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    order_number: Mapped[str] = mapped_column(
        String(20), unique=True, default=lambda: new_reference("ORD")
    )
    status: Mapped[str] = mapped_column(String(20), default="placed")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    placed_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    sku: Mapped[str] = mapped_column(String(50))
    product_name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    order: Mapped["Order"] = relationship(back_populates="items")
