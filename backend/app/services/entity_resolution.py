from typing import Any


def resolve_entity(candidates: list[Any], target_hint: str | None, raw_query: str) -> Any | None:
    """Resolves a customer/agent/etc. from free text. Tries exact id, exact
    email, exact full name, then a token-subset name match, in that order.
    Returns None if nothing matches - never guesses."""
    for candidate_text in (target_hint, raw_query):
        if not candidate_text:
            continue
        normalized = candidate_text.strip().lower()
        if not normalized:
            continue

        for entity in candidates:
            entity_id = getattr(entity, "id", None)
            if entity_id and (entity_id.lower() == normalized or entity_id.lower() in normalized.split()):
                return entity

        for entity in candidates:
            email = getattr(entity, "email", None)
            if email and email.lower() == normalized:
                return entity

        for entity in candidates:
            name = getattr(entity, "full_name", None)
            if name and name.lower() == normalized:
                return entity

        query_tokens = set(normalized.replace(",", " ").split())
        for entity in candidates:
            name = getattr(entity, "full_name", None)
            if not name:
                continue
            name_tokens = set(name.lower().split())
            if name_tokens and name_tokens.issubset(query_tokens):
                return entity

    return None
