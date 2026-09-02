from datetime import datetime, timezone


def _minutes_since_midnight(value: str) -> int:
    """Parses an 'HH:MM' string into minutes since midnight."""
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def is_on_duty(shift_start: str, shift_end: str, now: datetime | None = None) -> bool:
    """Whether `now` (UTC) falls within [shift_start, shift_end).

    on_duty is derived from shift hours, not stored as an independent
    flag - it can never drift out of sync with the schedule the way a
    manually-set/seeded boolean would. Handles shifts that wrap past
    midnight (e.g. 21:00-05:00). Malformed shift strings are treated as
    off-duty rather than raising, since this feeds display logic.
    """
    now = now or datetime.now(timezone.utc)
    current = now.hour * 60 + now.minute

    try:
        start = _minutes_since_midnight(shift_start)
        end = _minutes_since_midnight(shift_end)
    except (ValueError, AttributeError, TypeError):
        return False

    if start == end:
        # Zero-length window is meaningless as a "sometime today" shift -
        # treat it as covering the full day rather than never/always by
        # accident of comparison direction.
        return True
    if start < end:
        return start <= current < end
    # Overnight shift.
    return current >= start or current < end
