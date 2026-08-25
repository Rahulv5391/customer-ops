class AppError(Exception):
    """Base class for all application-specific errors.

    Subclasses are added in later build phases only when a real code path
    raises them (see Architecture.md §8) — no speculative/dead exception
    types.
    """
