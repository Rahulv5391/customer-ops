import uuid


def new_id() -> str:
    """Opaque primary-key id for internal records."""
    return uuid.uuid4().hex


def new_reference(prefix: str) -> str:
    """Human-facing reference code, e.g. ORD-A1B2C3D4."""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
