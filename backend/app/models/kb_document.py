from datetime import datetime, timezone

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.ids import new_id


class KBDocument(Base):
    __tablename__ = "kb_documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(30), default="faq")
    version: Mapped[str] = mapped_column(String(20), default="v1")
    content_json: Mapped[str] = mapped_column(Text, default="{}")
    # Human-readable date shown in citations, e.g. "March 2026".
    source_updated_at: Mapped[str] = mapped_column(String(50))
    # What the uploader named their file, if this came from a PDF upload -
    # descriptive only, never used for identity/dedup (see content_hash).
    source_filename: Mapped[str | None] = mapped_column(String(255), default=None)
    # SHA-256 of the document's normalized sections - the actual identity
    # signal for duplicate detection, deliberately independent of filename
    # or title (two docs can share a filename; that alone is never a
    # collision). Unique so the DB itself enforces the invariant, not just
    # an app-level check (services/document_extraction.py, routers/kb.py).
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
