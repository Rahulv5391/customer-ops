from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

# How long a pending action's confirmation token stays valid.
ACTION_TOKEN_EXPIRY_MINUTES = 5


def create_action_token(
    action_type: str,
    entity_type: str,
    entity_id: str,
    field_name: str | None = None,
    field_value: str | None = None,
    escalation_payload: dict | None = None,
) -> str:
    """Signs the fields of a proposed action into a short-lived token."""
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
