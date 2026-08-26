class AppError(Exception):
    """Base class for all application-specific errors.

    Subclasses are added in later build phases only when a real code path
    raises them (see Architecture.md §8) — no speculative/dead exception
    types.
    """


class LLMTransientError(AppError):
    """Network/timeout/rate-limit style LLM failure - safe to retry."""


class LLMOutputValidationError(AppError):
    """The LLM's response didn't match the expected structured-output schema."""


class CircuitOpenError(AppError):
    """This agent's circuit breaker is open - fail fast, don't call the LLM."""
