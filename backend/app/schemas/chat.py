from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    active_entity_id: str | None = None
    active_entity_type: str | None = None
    # user_id/role come from the authenticated JWT, not the request body.


class ActionDiff(BaseModel):
    before: dict
    after: dict


class PendingAction(BaseModel):
    """The proposed action shown to the agent, plus a signed token proving
    it. `/chat/action/confirm` only trusts the token, not the plain fields
    below (which are for display only)."""

    token: str
    action_type: str
    entity_type: str
    entity_id: str
    field_name: str | None = None
    field_value: str | None = None
    escalation_payload: dict | None = None


class Citation(BaseModel):
    document_title: str
    version: str
    source_updated_at: str
    section: str | None = None
    # The actual retrieved passage text (not just title/section) so an
    # agent can verify the answer against real source content instead of
    # trusting an opaque "Refund Policy (v2)" chip.
    snippet: str | None = None


class ChatMessage(BaseModel):
    type: Literal["text", "action-confirmation", "citation-answer", "error"]
    content: str
    action_diff: ActionDiff | None = None
    pending_action: PendingAction | None = None
    citations: list[Citation] | None = None
    status: Literal["final", "pending_confirmation"] | None = None
    # Set when this turn's lookup resolved to exactly one entity. The
    # frontend echoes these back as active_entity_id/active_entity_type
    # on the next request.
    resolved_entity_id: str | None = None
    resolved_entity_type: str | None = None


class ChatResponse(BaseModel):
    messages: list[ChatMessage]


class ActionConfirmRequest(BaseModel):
    """The signed token from a PendingAction, echoed back to confirm it."""

    token: str


class ActionConfirmResponse(BaseModel):
    success: bool
    message: str
    entity: dict
