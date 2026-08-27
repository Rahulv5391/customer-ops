from app.schemas.chat import ChatMessage

# Returned by any sub-agent when its LLM call fails.
UNAVAILABLE_MESSAGE = ChatMessage(
    type="error",
    content="The AI assistant is temporarily unavailable. Please try again in a moment.",
    status="final",
)
