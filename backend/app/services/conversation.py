"""Renders a chat session's recent messages into plain transcript text that
gets prepended to every sub-agent's LLM prompt, so multi-turn context is
carried as real conversation text instead of a hidden active-entity id."""

from app.models.chat_session import ChatSessionMessage

_ROLE_LABEL = {"user": "User", "assistant": "Assistant"}


def render_transcript(messages: list[ChatSessionMessage]) -> str:
    if not messages:
        return ""
    lines = [f"{_ROLE_LABEL.get(m.role, m.role)}: {m.content}" for m in messages]
    return "\n".join(lines)


def with_history(history: str, message: str) -> str:
    if not history:
        return message
    return f"Conversation so far:\n{history}\n\nLatest message: {message}"
