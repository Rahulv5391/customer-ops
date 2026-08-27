from app.schemas.chat import ChatMessage

# Shared canned ChatMessage returned by every sub-agent when its LLM call
# fails (LLMTransientError/LLMOutputValidationError/CircuitOpenError) - the
# only fallback path, no static rule-based routing exists behind it
# (Architecture.md §5).
UNAVAILABLE_MESSAGE = ChatMessage(
    type="error",
    content="The AI assistant is temporarily unavailable. Please try again in a moment.",
    status="final",
)
