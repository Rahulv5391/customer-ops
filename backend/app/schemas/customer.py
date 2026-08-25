from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.note import NoteResponse
from app.schemas.order import OrderDetailResponse
from app.schemas.ticket import TicketDetailResponse


class CustomerBase(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    company: str | None = None
    account_tier: str = "free"
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    status: str = "active"


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    company: str | None = None
    account_tier: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country: str | None = None
    status: str | None = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class CustomerDetailResponse(CustomerResponse):
    orders: list[OrderDetailResponse] = []
    tickets: list[TicketDetailResponse] = []
    notes: list[NoteResponse] = []
