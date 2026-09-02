from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketEventCreate(BaseModel):
    event_type: str
    detail: str = ""
    # actor is set server-side from the authenticated agent.


class TicketEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    event_type: str
    actor: str
    detail: str
    created_at: datetime


class TicketCustomerSummary(BaseModel):
    """Just enough to identify the customer on a ticket - a small local
    model rather than importing app.schemas.customer, since that module
    already imports TicketDetailResponse from here (would be circular)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str
    phone: str | None = None
    company: str | None = None


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
    customer: TicketCustomerSummary


class TicketBoardColumn(BaseModel):
    status: str
    tickets: list[TicketResponse]


class TicketBoardChannel(BaseModel):
    channel: str
    columns: list[TicketBoardColumn]
