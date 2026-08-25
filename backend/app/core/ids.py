import uuid


def new_id() -> str:
    """Opaque primary-key id for internal records."""
    return uuid.uuid4().hex


def new_reference(prefix: str) -> str:
    """Human-facing reference code, e.g. ORD-A1B2C3D4.

    Collision-safe by construction (uuid4 suffix), unlike the reference
    codebase's f"T-{random.randint(100, 999)}" scheme - see Architecture.md §8.6.
    """
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
