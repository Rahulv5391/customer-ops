from sqlalchemy.orm import Session

from app.agents.agent_runtime import ToolCallingAgentRuntime
from app.agents.messages import UNAVAILABLE_MESSAGE
from app.agents.tools import lookup_tools, mutation_tools, policy_tools
from app.agents.tools.base import ToolOutcome
from app.core.exceptions import CircuitOpenError, LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger, new_trace
from app.prompts.loader import load_prompt
from app.schemas.chat import ChatMessage
from app.services.conversation import with_history

logger = get_logger("ops_agent")


class OpsAgent:
    """The unified chat agent - one Agent, many tools, the model decides
    which (if any) to call, replacing router_agent's classify-then-dispatch
    step and the four per-category sub-agents it used to dispatch to.

    A fresh Agent + Runner + tool set is built per call (see
    ToolCallingAgentRuntime and tools/*.build_tools) since tools need this
    request's db session and a place to capture their real result - see
    tools/base.py for why the model never sees that data directly."""

    def __init__(self):
        self._instruction = load_prompt("ops_agent")

    async def handle_message(
        self,
        db: Session,
        message: str,
        agent_name: str,
        role: str,
        history: str = "",
        trace_id: str | None = None,
    ) -> ChatMessage:
        with new_trace(trace_id):
            outcomes: list[ToolOutcome] = []
            tools = [
                *lookup_tools.build_tools(db, outcomes),
                *policy_tools.build_tools(outcomes),
                *mutation_tools.build_tools(db, actor=agent_name, outcomes=outcomes),
            ]
            runtime = ToolCallingAgentRuntime(
                agent_name="ops_agent", instruction=self._instruction, tools=tools
            )

            prompt = with_history(history, f"Agent: {agent_name} (role: {role}).\nMessage: {message}")
            try:
                final_text = await runtime.run(prompt, user_id=agent_name, on_retry=outcomes.clear)
            except (LLMTransientError, LLMOutputValidationError, CircuitOpenError) as exc:
                logger.warning(f"ops_agent call failed: {exc}")
                # A tool may have already produced a usable outcome (e.g. a
                # signed proposal) even if a later wrap-up turn failed -
                # don't discard an already-valid result.
                if outcomes:
                    return self._assemble(outcomes, final_text="")
                return UNAVAILABLE_MESSAGE

            return self._assemble(outcomes, final_text)

    def _assemble(self, outcomes: list[ToolOutcome], final_text: str) -> ChatMessage:
        if not outcomes:
            # No tool was called this turn - greeting/small talk, or the
            # model asked a clarifying question in its own words instead of
            # calling an under-specified tool. Use its text verbatim.
            return ChatMessage(type="text", content=final_text, status="final")

        # The last thing this turn concretely produced wins. Only the one
        # tool that sets needs_model_text (policy search) has the model's
        # own text substituted in - every other outcome's ChatMessage was
        # already fully built in Python by the tool itself.
        outcome = outcomes[-1]
        if outcome.needs_model_text:
            outcome.chat_message.content = final_text or outcome.chat_message.content
        return outcome.chat_message


ops_agent = OpsAgent()
