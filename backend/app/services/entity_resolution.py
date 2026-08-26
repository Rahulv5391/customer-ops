from typing import Any


def resolve_entity(candidates: list[Any], target_hint: str | None, raw_query: str) -> Any | None:
    """Resolve a customer/agent/etc. from free text.

    Tiers, tried in order for each candidate text (target_hint first, then
    the raw query): exact id -> exact email -> exact full_name -> name
    token-subset (every word of the entity's name appears somewhere in the
    text). No fuzzy/Levenshtein matching - an unresolvable typo returns
    None so the caller can ask a clarifying question rather than guess
    (Architecture.md §5).
    """
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
