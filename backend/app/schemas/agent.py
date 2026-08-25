from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentBase(BaseModel):
    full_name: str
    email: str
    role: str = "support_agent"
    role_label: str = "Support Agent"
    team: str = "general"
    shift_start: str = "09:00"
    shift_end: str = "17:00"
    on_duty: bool = True
    extension: str | None = None


class AgentCreate(AgentBase):
    password: str


class AgentUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    role_label: str | None = None
    team: str | None = None
    shift_start: str | None = None
    shift_end: str | None = None
    on_duty: bool | None = None
    extension: str | None = None
    active: bool | None = None
    two_factor: bool | None = None


class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    active: bool
    two_factor: bool
    created_at: datetime
