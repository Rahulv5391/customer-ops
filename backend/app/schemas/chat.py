from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    active_entity_id: str | None = None
    active_entity_type: str | None = None
    # user_id/role are deliberately NOT accepted here - they're derived
    # server-side from the authenticated JWT (Architecture.md §6).


class ActionDiff(BaseModel):
    before: dict
    after: dict


class PendingAction(BaseModel):
    """What the frontend renders, plus the signed proof it echoes back to
    `/chat/action/confirm`.

    `token` is the only thing the confirm endpoint actually trusts - it's a
    signed encoding of the fields below, produced server-side by
    action_token.create_action_token when this proposal was generated. The
    plain fields exist for the frontend to display/log, but are never
    re-read by confirm, so a client can't submit a different amount/entity
    than what was actually proposed (Architecture.md §5/§6).
    """

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


class ChatMessage(BaseModel):
    type: Literal["text", "action-confirmation", "citation-answer", "error"]
    content: str
    action_diff: ActionDiff | None = None
    pending_action: PendingAction | None = None
    citations: list[Citation] | None = None
    status: Literal["final", "pending_confirmation"] | None = None
    # Set when this turn's lookup unambiguously resolved to one entity - the
    # frontend should echo these back as active_entity_id/active_entity_type
    # on the next ChatRequest so "them"/"this customer" can resolve without
    # the agent having to restate the id (Architecture.md §6).
    resolved_entity_id: str | None = None
    resolved_entity_type: str | None = None


class ChatResponse(BaseModel):
    messages: list[ChatMessage]


class ActionConfirmRequest(BaseModel):
    """The confirm endpoint executes exactly what `token` decodes to - see
    PendingAction.token. confirmed_by is likewise derived from the
    authenticated session, never client-supplied."""

    token: str


class ActionConfirmResponse(BaseModel):
    success: bool
    message: str
    entity: dict
