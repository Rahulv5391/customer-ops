from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.ids import new_id


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(150))
    connector_type: Mapped[str] = mapped_column(String(30))
    sync_status: Mapped[str] = mapped_column(String(20), default="healthy")
    sync_health_pct: Mapped[int] = mapped_column(default=100)
    # Mock-only JSON blobs - no live connections.
    tables_schema: Mapped[str] = mapped_column(Text, default="[]")
    sync_logs: Mapped[str] = mapped_column(Text, default="[]")
    last_synced_at: Mapped[datetime | None] = mapped_column(default=None)
