import asyncio
import os
from typing import Callable

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.genai import types

from app.core.circuit_breaker import CircuitBreaker
from app.core.config import settings
from app.core.exceptions import LLMTransientError
from app.core.observability import get_logger, timed


def _has_real_api_key() -> bool:
    return bool(settings.gemini_api_key) and not settings.gemini_api_key.startswith("your-")


class ToolCallingAgentRuntime:
    """Wraps a Google ADK Agent + Runner around a set of tool functions,
    with the same retry/circuit-breaker/timeout protection as the old
    per-category BaseSubAgent - but returns the model's final plain text
    instead of a validated structured-output object, since tool selection
    now does the job a separate output_schema used to do.

    ADK's Runner.run_async already handles the full tool-call round trip
    transparently (calls a requested tool, feeds its result back to the
    model, repeats) before ever emitting a final response event, so the
    event-walking loop below needs no changes to support tools - it just
    reads whatever text the model settles on."""

    def __init__(self, agent_name: str, instruction: str, tools: list[Callable], model: str | None = None):
        self.agent_name = agent_name
        self._logger = get_logger(agent_name)
        self._breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_failure_threshold,
            reset_seconds=settings.circuit_breaker_reset_seconds,
        )

        if _has_real_api_key():
            os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

        self._session_service = InMemorySessionService()
        self._agent = Agent(
            name=agent_name,
            model=model or settings.gemini_llm_model,
            instruction=instruction,
            tools=[FunctionTool(fn) for fn in tools],
        )
        self._runner = Runner(
            agent=self._agent, app_name=agent_name, session_service=self._session_service
        )

    async def run(
        self, prompt_text: str, user_id: str = "system", on_retry: Callable[[], None] | None = None
    ) -> str:
        """`on_retry`, if given, is called at the start of every attempt
        (including the first) before invoking the model - used by callers
        that capture tool-call side effects per attempt (e.g. OpsAgent's
        `outcomes` list) so a failed attempt's partial captures never leak
        into a later attempt's result."""
        if not _has_real_api_key():
            raise LLMTransientError("No Gemini API key configured")

        self._breaker.before_call()

        last_error: Exception = LLMTransientError("LLM call did not run")
        for attempt in range(1, settings.llm_max_retries + 1):
            if on_retry:
                on_retry()
            try:
                with timed(self._logger, "llm_call", agent=self.agent_name, attempt=attempt):
                    final_text = await asyncio.wait_for(
                        self._invoke(prompt_text, user_id), timeout=settings.llm_timeout_seconds
                    )
            except Exception as exc:
                last_error = LLMTransientError(f"LLM call failed: {exc}")
            else:
                self._breaker.record_success()
                return final_text

            self._breaker.record_failure()
            if attempt < settings.llm_max_retries:
                await asyncio.sleep(settings.llm_backoff_base_seconds * attempt)

        raise last_error

    async def _invoke(self, prompt_text: str, user_id: str) -> str:
        session = await self._session_service.create_session(app_name=self.agent_name, user_id=user_id)
        try:
            content = types.Content(role="user", parts=[types.Part(text=prompt_text)])
            final_text = ""
            async for event in self._runner.run_async(
                user_id=user_id, session_id=session.id, new_message=content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_text = event.content.parts[0].text or ""
            # Unlike the old structured-output path, an empty final text is
            # tolerated here - a tool call may have already produced the
            # user-facing ChatMessage (see tools/base.py), and the model's
            # own wrap-up text is only used when it's actually needed
            # (ops_agent.OpsAgent.handle_message's needs_model_text check).
            return final_text
        finally:
            try:
                await self._session_service.delete_session(
                    app_name=self.agent_name, user_id=user_id, session_id=session.id
                )
            except Exception:
                pass
