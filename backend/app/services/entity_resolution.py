from typing import Any


class AmbiguousEntityError(Exception):
    """Raised when free text matches more than one candidate at the same
    tier (e.g. two customers named 'Carla Jensen') - the caller should ask
    for a more specific identifier instead of guessing which one was meant."""

    def __init__(self, matches: list[Any]):
        self.matches = matches
        super().__init__(f"{len(matches)} candidates matched ambiguously")


def _unique_or_ambiguous(matches: list[Any]) -> Any | None:
    """Returns the single match, raises if there's more than one, or
    returns None (try the next tier) if there are none."""
    if len(matches) > 1:
        raise AmbiguousEntityError(matches)
    return matches[0] if matches else None


def resolve_entity(candidates: list[Any], target_hint: str | None, raw_query: str) -> Any | None:
    """Resolves a customer/agent/etc. from free text. Tries exact id, exact
    email, exact full name, then a token-subset name match, in that order,
    within each tier considering ALL candidates before deciding.

    Returns None if nothing matches - never guesses. Raises
    AmbiguousEntityError (instead of silently returning the first hit) if
    more than one candidate matches at the same tier, e.g. two customers
    sharing a full name - the caller should ask the agent to disambiguate
    by id or email rather than risk acting on the wrong record."""
    for candidate_text in (target_hint, raw_query):
        if not candidate_text:
            continue
        normalized = candidate_text.strip().lower()
        if not normalized:
            continue

        id_matches = [
            entity
            for entity in candidates
            if (entity_id := getattr(entity, "id", None))
            and (entity_id.lower() == normalized or entity_id.lower() in normalized.split())
        ]
        result = _unique_or_ambiguous(id_matches)
        if result is not None:
            return result

        email_matches = [
            entity
            for entity in candidates
            if (email := getattr(entity, "email", None)) and email.lower() == normalized
        ]
        result = _unique_or_ambiguous(email_matches)
        if result is not None:
            return result

        name_matches = [
            entity
            for entity in candidates
            if (name := getattr(entity, "full_name", None)) and name.lower() == normalized
        ]
        result = _unique_or_ambiguous(name_matches)
        if result is not None:
            return result

        query_tokens = set(normalized.replace(",", " ").split())
        token_matches = [
            entity
            for entity in candidates
            if (name := getattr(entity, "full_name", None))
            and (name_tokens := set(name.lower().split()))
            and name_tokens.issubset(query_tokens)
        ]
        result = _unique_or_ambiguous(token_matches)
        if result is not None:
            return result

    return None
