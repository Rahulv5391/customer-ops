"""Shared plumbing for every ops_agent tool function.

The unified agent's tools never hand their real result back to the model to
paraphrase - each tool builds the actual ChatMessage the frontend will show
(a completed lookup, a formatted report, a refusal, or a mutation proposal)
directly in Python, appends it here as a ToolOutcome, and returns the model
only a short acknowledgement string. This makes paraphrase risk structural:
the model never sees the real data it could otherwise garble. See
ops_agent.OpsAgent.handle_message for how the last-appended outcome gets
turned into the actual API response.
"""

import functools
import inspect
from dataclasses import dataclass

from app.core.observability import get_logger
from app.schemas.chat import ChatMessage

logger = get_logger("ops_agent.tools")

# Shown to the model instead of the real data for every terminal outcome
# (a completed lookup, a mutation proposal, a refusal) - the data itself was
# already placed directly in the ChatMessage the frontend will render.
ALREADY_SHOWN = (
    "This was already shown to the user directly - do not restate it. A brief "
    "acknowledgement or a relevant follow-up question is fine, or nothing further."
)

# Shown to the model after a mutation proposal specifically - the stronger,
# more specific warning against re-asking for a "yes" the UI already collects
# via a button click, not a chat reply.
PROPOSAL_ALREADY_SHOWN = (
    "A confirmation card for this action was already shown to the user with an "
    "Authorize button - do not ask them to say yes in chat, they must click the "
    "button. Don't call this tool again for the same request unless they change "
    "what they're asking for."
)


@dataclass
class ToolOutcome:
    """One tool call's concrete result, captured for OpsAgent to assemble
    into the final API response - see module docstring."""

    chat_message: ChatMessage
    # True only for the one tool (policy search) where the model is
    # supposed to compose the user-facing text itself, grounded in what the
    # tool returned - see policy_tools.py.
    needs_model_text: bool = False


def logged_tool(func):
    """Wraps a tool function so every call and its result are logged - the
    equivalent of today's RouterOutput.reasoning field, but per actual tool
    call rather than one classification string, and the primary way to
    audit whether a mutation tool proposed something ungrounded."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = inspect.signature(func).bind(*args, **kwargs)
        bound.apply_defaults()
        # Never log db/outcomes/actor closures - just the model-supplied args.
        loggable_args = {
            k: v for k, v in bound.arguments.items() if k not in ("db", "outcomes", "actor")
        }
        logger.info(
            f"tool_call:{func.__name__}", extra={"extra_fields": {"args": loggable_args}}
        )
        result = func(*args, **kwargs)
        logger.info(
            f"tool_result:{func.__name__}", extra={"extra_fields": {"result": str(result)[:500]}}
        )
        return result

    return wrapper
