from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteBase(BaseModel):
    author: str
    body: str


class NoteCreate(NoteBase):
    pass


class NoteResponse(NoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    created_at: datetime
