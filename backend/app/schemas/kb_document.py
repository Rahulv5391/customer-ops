from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KBDocumentBase(BaseModel):
    title: str
    category: str = "faq"
    version: str = "v1"
    source_updated_at: str


class KBDocumentCreate(KBDocumentBase):
    content_json: str = "{}"


class KBDocumentUpdate(BaseModel):
    title: str | None = None
    category: str | None = None
    version: str | None = None
    source_updated_at: str | None = None
    content_json: str | None = None


class KBDocumentResponse(KBDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_json: str
    created_at: datetime
