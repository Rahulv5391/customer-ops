from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KBDocumentBase(BaseModel):
    title: str
    category: str = "faq"
    version: str = "v1"
    source_updated_at: str


class KBDocumentUpdate(BaseModel):
    """Metadata-only edits - content can only be changed via
    PATCH /kb/{id}/upload (a new PDF), never a hand-typed JSON body
    (Architecture.md §5/6 - removed after a direct call that nobody
    hand-authors KB content as JSON in practice)."""

    title: str | None = None
    category: str | None = None
    version: str | None = None
    source_updated_at: str | None = None


class KBDocumentResponse(KBDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_json: str
    source_filename: str | None = None
    content_hash: str
    created_at: datetime
