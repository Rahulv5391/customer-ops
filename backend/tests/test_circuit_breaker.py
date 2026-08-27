"""Open/reset transitions for the per-agent failure tracker
(core/circuit_breaker.py) - the thing that makes a stuck/failing LLM
provider fail fast instead of hanging every subsequent chat call.
"""

import time

import pytest

from app.core.circuit_breaker import CircuitBreaker
from app.core.exceptions import CircuitOpenError


def test_before_call_is_a_noop_when_closed():
    breaker = CircuitBreaker(failure_threshold=3, reset_seconds=30)
    breaker.before_call()  # should not raise


def test_stays_closed_below_the_failure_threshold():
    breaker = CircuitBreaker(failure_threshold=3, reset_seconds=30)
    breaker.record_failure()
    breaker.record_failure()
    breaker.before_call()  # still 2 failures, threshold is 3 - should not raise


def test_opens_at_the_failure_threshold():
    breaker = CircuitBreaker(failure_threshold=3, reset_seconds=30)
    for _ in range(3):
        breaker.record_failure()
    with pytest.raises(CircuitOpenError):
        breaker.before_call()


def test_success_resets_the_failure_count():
    breaker = CircuitBreaker(failure_threshold=3, reset_seconds=30)
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_success()
    breaker.record_failure()
    breaker.record_failure()
    breaker.before_call()  # only 2 consecutive failures since the reset - still closed


def test_success_closes_an_already_open_circuit():
    breaker = CircuitBreaker(failure_threshold=1, reset_seconds=30)
    breaker.record_failure()
    with pytest.raises(CircuitOpenError):
        breaker.before_call()
    breaker.record_success()
    breaker.before_call()  # should not raise - success closed it


def test_half_open_retry_allowed_after_reset_window_elapses():
    breaker = CircuitBreaker(failure_threshold=1, reset_seconds=0.05)
    breaker.record_failure()
    with pytest.raises(CircuitOpenError):
        breaker.before_call()

    time.sleep(0.1)

    breaker.before_call()  # reset window elapsed - half-open retry allowed, no raise


def test_a_failure_during_half_open_reopens_the_circuit():
    breaker = CircuitBreaker(failure_threshold=1, reset_seconds=0.05)
    breaker.record_failure()
    time.sleep(0.1)
    breaker.before_call()  # half-open
    breaker.record_failure()  # the half-open retry failed too

    with pytest.raises(CircuitOpenError):
        breaker.before_call()
