from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    body: str
    # author is set server-side from the authenticated agent.


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    author: str
    body: str
    created_at: datetime
