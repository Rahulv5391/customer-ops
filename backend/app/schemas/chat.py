from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    active_entity_id: str | None = None
    active_entity_type: str | None = None
    scope: dict | None = None
    # user_id/role are deliberately NOT accepted here - they're derived
    # server-side from the authenticated JWT (Architecture.md §6).


class ActionDiff(BaseModel):
    before: dict
    after: dict


class Citation(BaseModel):
    document_title: str
    version: str
    source_updated_at: str
    section: str | None = None


class ChatMessage(BaseModel):
    type: Literal["text", "action-confirmation", "citation-answer", "error"]
    content: str
    action_diff: ActionDiff | None = None
    citations: list[Citation] | None = None
    status: Literal["final", "pending_confirmation"] | None = None


class ChatResponse(BaseModel):
    messages: list[ChatMessage]


class ActionConfirmRequest(BaseModel):
    action_type: str
    entity_type: str
    entity_id: str
    field_name: str | None = None
    field_value: str | None = None
    escalation_payload: dict | None = None
    # confirmed_by is likewise derived from the authenticated session.


class ActionConfirmResponse(BaseModel):
    success: bool
    message: str
    entity: dict
