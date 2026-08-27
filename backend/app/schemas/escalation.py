from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EscalationBase(BaseModel):
    escalation_type: str
    requested_action: str
    priority: str = "medium"
    ticket_id: str | None = None
    policy_citation: str | None = None


class EscalationCreate(EscalationBase):
    # requested_by is set server-side from the authenticated user.
    pass


class EscalationResolve(BaseModel):
    status: str  # "approved" | "rejected"
    rejection_note: str | None = None


class EscalationResponse(EscalationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    escalation_number: str
    status: str
    rejection_note: str | None = None
    requested_by: str
    created_at: datetime
    resolved_at: datetime | None = None
