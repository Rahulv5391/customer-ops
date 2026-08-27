from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

# Short-lived - a pending action is meant to be confirmed within the same
# chat turn, not stashed and replayed later.
ACTION_TOKEN_EXPIRY_MINUTES = 5


def create_action_token(
    action_type: str,
    entity_type: str,
    entity_id: str,
    field_name: str | None = None,
    field_value: str | None = None,
    escalation_payload: dict | None = None,
) -> str:
    """Sign the exact fields of a proposed action (Architecture.md §5/§6).

    `/chat/action/confirm` executes only what's encoded in this token, never
    any client-supplied fields alongside it - otherwise a tampered or
    fabricated confirm request (different amount, different entity_id) would
    be indistinguishable from one the agent actually saw and approved,
    which would quietly defeat the whole point of propose -> confirm.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "action_type": action_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "field_name": field_name,
        "field_value": field_value,
        "escalation_payload": escalation_payload,
        "iat": now,
        "exp": now + timedelta(minutes=ACTION_TOKEN_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_action_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise ValueError(f"This confirmation has expired or is invalid: {exc}") from exc
    return {
        "action_type": payload["action_type"],
        "entity_type": payload["entity_type"],
        "entity_id": payload["entity_id"],
        "field_name": payload.get("field_name"),
        "field_value": payload.get("field_value"),
        "escalation_payload": payload.get("escalation_payload"),
    }
