from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.ids import new_id


class CustomerNote(Base):
    __tablename__ = "customer_notes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id"), index=True
    )
    author: Mapped[str] = mapped_column(String(150))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    customer: Mapped["Customer"] = relationship(back_populates="notes")
