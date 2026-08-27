class AppError(Exception):
    """Base class for application-specific errors."""


class LLMTransientError(AppError):
    """Network/timeout/rate-limit style LLM failure - safe to retry."""


class LLMOutputValidationError(AppError):
    """The LLM's response didn't match the expected structured-output schema."""


class CircuitOpenError(AppError):
    """This agent's circuit breaker is open - fail fast, don't call the LLM."""


class EntityNotFoundError(AppError):
    """A confirmed chat action targeted an entity id that doesn't exist."""
