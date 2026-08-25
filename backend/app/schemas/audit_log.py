from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogCreate(BaseModel):
    action_type: str
    actor: str
    entity_type: str
    entity_id: str
    summary: str


class ActivityLogResponse(ActivityLogCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
