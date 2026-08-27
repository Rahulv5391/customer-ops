import time

from app.core.exceptions import CircuitOpenError


class CircuitBreaker:
    """Opens after `failure_threshold` consecutive failures and stays open
    for `reset_seconds` before allowing another call through."""

    def __init__(self, failure_threshold: int, reset_seconds: float):
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    def before_call(self) -> None:
        if self._opened_at is not None:
            if time.monotonic() - self._opened_at < self.reset_seconds:
                raise CircuitOpenError("Circuit breaker is open")
            self._opened_at = None  # reset window elapsed - allow a half-open retry

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._opened_at = time.monotonic()
