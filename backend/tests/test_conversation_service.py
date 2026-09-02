from app.models.chat_session import ChatSessionMessage
from app.services.conversation import render_transcript, with_history


def _msg(role, content):
    return ChatSessionMessage(role=role, content=content)


def test_render_transcript_is_empty_for_no_messages():
    assert render_transcript([]) == ""


def test_render_transcript_labels_each_role():
    transcript = render_transcript(
        [_msg("user", "I want to raise an escalation"), _msg("assistant", "Sure, what for?")]
    )
    assert transcript == (
        "User: I want to raise an escalation\nAssistant: Sure, what for?"
    )


def test_with_history_returns_message_unchanged_when_history_is_empty():
    assert with_history("", "refund of $1000") == "refund of $1000"


def test_with_history_wraps_message_with_transcript():
    result = with_history("User: hi\nAssistant: hello", "refund of $1000")
    assert "User: hi\nAssistant: hello" in result
    assert "refund of $1000" in result
