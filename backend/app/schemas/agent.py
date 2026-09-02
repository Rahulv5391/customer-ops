from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.agent_status import is_on_duty


class AgentBase(BaseModel):
    full_name: str
    email: str
    role: str = "support_agent"
    role_label: str = "Support Agent"
    team: str = "general"
    shift_start: str = "09:00"
    shift_end: str = "17:00"
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
    extension: str | None = None
    active: bool | None = None
    two_factor: bool | None = None


class AgentResponse(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    active: bool
    two_factor: bool
    created_at: datetime
    # Always recomputed from shift_start/shift_end below - never trusts
    # whatever the stored `on_duty` column happens to hold, which could
    # drift arbitrarily out of sync with the actual shift schedule.
    on_duty: bool = True

    @model_validator(mode="after")
    def _derive_on_duty(self) -> "AgentResponse":
        self.on_duty = is_on_duty(self.shift_start, self.shift_end)
        return self
