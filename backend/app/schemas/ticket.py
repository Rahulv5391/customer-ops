from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketEventBase(BaseModel):
    event_type: str
    actor: str
    detail: str = ""


class TicketEventCreate(TicketEventBase):
    pass


class TicketEventResponse(TicketEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    created_at: datetime


class TicketBase(BaseModel):
    channel: str = "email"
    subject: str
    status: str = "unassigned"
    priority: str = "medium"
    assigned_agent_id: str | None = None
    category: str = "other"


class TicketCreate(TicketBase):
    customer_id: str


class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    assigned_agent_id: str | None = None
    category: str | None = None


class TicketResponse(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    ticket_number: str
    csat_score: float | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None


class TicketDetailResponse(TicketResponse):
    events: list[TicketEventResponse] = []
