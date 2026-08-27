import asyncio
import os
import re
from typing import Generic, TypeVar

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.core.circuit_breaker import CircuitBreaker
from app.core.config import settings
from app.core.exceptions import LLMOutputValidationError, LLMTransientError
from app.core.observability import get_logger, timed

_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)

TOutput = TypeVar("TOutput", bound=BaseModel)


def _has_real_api_key() -> bool:
    return bool(settings.gemini_api_key) and not settings.gemini_api_key.startswith("your-")


class BaseSubAgent(Generic[TOutput]):
    """Wraps a Google ADK Agent + Runner, turning a prompt into a validated
    Pydantic object, with retries and circuit-breaker protection."""

    def __init__(
        self,
        agent_name: str,
        instruction: str,
        output_schema: type[TOutput],
        model: str | None = None,
    ):
        self.agent_name = agent_name
        self.output_schema = output_schema
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
            output_schema=output_schema,
        )
        self._runner = Runner(
            agent=self._agent, app_name=agent_name, session_service=self._session_service
        )

    async def run(self, prompt_text: str, user_id: str = "system") -> TOutput:
        if not _has_real_api_key():
            raise LLMTransientError("No Gemini API key configured")

        self._breaker.before_call()

        last_error: Exception = LLMTransientError("LLM call did not run")
        for attempt in range(1, settings.llm_max_retries + 1):
            try:
                with timed(self._logger, "llm_call", agent=self.agent_name, attempt=attempt):
                    raw_text = await asyncio.wait_for(
                        self._invoke(prompt_text, user_id), timeout=settings.llm_timeout_seconds
                    )
                parsed = self._parse_output(raw_text)
            except LLMOutputValidationError as exc:
                self._logger.warning(f"Output validation failed on attempt {attempt}: {exc}")
                last_error = exc
            except Exception as exc:
                last_error = LLMTransientError(f"LLM call failed: {exc}")
            else:
                self._breaker.record_success()
                return parsed

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
            if not final_text:
                raise LLMTransientError("Empty response from Gemini model")
            return final_text
        finally:
            try:
                await self._session_service.delete_session(
                    app_name=self.agent_name, user_id=user_id, session_id=session.id
                )
            except Exception:
                pass

    def _parse_output(self, raw_text: str) -> TOutput:
        try:
            return self.output_schema.model_validate_json(raw_text)
        except ValidationError:
            pass
        stripped = _JSON_FENCE_RE.sub("", raw_text).strip()
        try:
            return self.output_schema.model_validate_json(stripped)
        except ValidationError as exc:
            raise LLMOutputValidationError(f"Could not parse LLM output: {exc}") from exc
