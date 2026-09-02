"""Tests is_on_duty: on_duty must be derived purely from shift_start/
shift_end vs the current time, including overnight (wrap-past-midnight)
shifts - never a stored/independent flag."""

from datetime import datetime, timezone

from app.services.agent_status import is_on_duty


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 1, hour, minute, tzinfo=timezone.utc)


def test_within_a_normal_daytime_shift():
    assert is_on_duty("09:00", "17:00", now=_at(12, 30)) is True


def test_before_a_normal_daytime_shift():
    assert is_on_duty("09:00", "17:00", now=_at(8, 59)) is False


def test_at_or_after_shift_end_is_off_duty():
    # End is exclusive - the shift has ended by exactly 17:00.
    assert is_on_duty("09:00", "17:00", now=_at(17, 0)) is False
    assert is_on_duty("09:00", "17:00", now=_at(18, 2)) is False


def test_start_boundary_is_inclusive():
    assert is_on_duty("09:00", "17:00", now=_at(9, 0)) is True


def test_overnight_shift_covers_late_night():
    # 21:00 - 05:00 shift should be "on" at 23:00 and at 02:00, "off" at noon.
    assert is_on_duty("21:00", "05:00", now=_at(23, 0)) is True
    assert is_on_duty("21:00", "05:00", now=_at(2, 0)) is True
    assert is_on_duty("21:00", "05:00", now=_at(12, 0)) is False


def test_overnight_shift_end_boundary_is_exclusive():
    assert is_on_duty("21:00", "05:00", now=_at(5, 0)) is False


def test_malformed_shift_strings_are_treated_as_off_duty_not_an_error():
    assert is_on_duty("", "", now=_at(12, 0)) is False
    assert is_on_duty("not-a-time", "17:00", now=_at(12, 0)) is False


def test_defaults_to_the_real_current_time_when_now_is_omitted():
    # Just confirms it runs without a `now` argument and returns a bool -
    # the actual value depends on when the test happens to run.
    assert isinstance(is_on_duty("00:00", "23:59"), bool)
