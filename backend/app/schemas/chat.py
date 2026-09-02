from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    # Client-generated (crypto.randomUUID()), stable for the chat panel's
    # whole mounted lifetime. Used to look up this session's persisted
    # history - see app/models/chat_session.py.
    session_id: str
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


class ChatResponse(BaseModel):
    messages: list[ChatMessage]


class ActionConfirmRequest(BaseModel):
    """The signed token from a PendingAction, echoed back to confirm it."""

    token: str


class ActionConfirmResponse(BaseModel):
    success: bool
    message: str
    entity: dict
