"""Tests resolve_entity's match tiers: exact id, exact email, exact
full name, then name token-subset. No fuzzy matching - unresolved returns
None."""

from types import SimpleNamespace

import pytest

from app.services.entity_resolution import AmbiguousEntityError, resolve_entity


def _entity(id="e1", full_name="Daniel Brooks", email="daniel@example.com"):
    return SimpleNamespace(id=id, full_name=full_name, email=email)


def test_exact_id_match_via_target_hint():
    candidates = [_entity(id="abc123"), _entity(id="other")]
    assert resolve_entity(candidates, "abc123", "irrelevant raw text") is candidates[0]


def test_exact_email_match():
    candidates = [_entity(email="ada@example.com"), _entity(email="other@example.com")]
    result = resolve_entity(candidates, "ada@example.com", "ignored")
    assert result is candidates[0]


def test_exact_full_name_match_case_insensitive():
    candidates = [_entity(full_name="Ada Lovelace"), _entity(full_name="Grace Hopper")]
    result = resolve_entity(candidates, "ada lovelace", "ignored")
    assert result is candidates[0]


def test_token_subset_match_all_name_words_present():
    candidates = [_entity(full_name="Daniel Brooks")]
    result = resolve_entity(candidates, None, "please update daniel brooks account")
    assert result is candidates[0]


def test_token_subset_requires_every_name_word_present():
    # "brooks" alone is not a full token-subset match for "Daniel Brooks" -
    # a partial name must not resolve, since that's exactly the fuzzy
    # guessing this design deliberately refuses to do.
    candidates = [_entity(full_name="Daniel Brooks")]
    assert resolve_entity(candidates, None, "find brooks please") is None


def test_target_hint_is_tried_before_raw_query():
    daniel = _entity(id="d1", full_name="Daniel Brooks", email="daniel@example.com")
    ada = _entity(id="a1", full_name="Ada Lovelace", email="ada@example.com")
    # raw_query alone would resolve to Ada; target_hint should win first.
    result = resolve_entity([daniel, ada], "daniel@example.com", "find ada lovelace")
    assert result is daniel


def test_falls_back_to_raw_query_when_target_hint_does_not_resolve():
    daniel = _entity(id="d1", full_name="Daniel Brooks", email="daniel@example.com")
    result = resolve_entity([daniel], "no match here", "please find daniel brooks")
    assert result is daniel


def test_no_match_returns_none_rather_than_guessing():
    candidates = [_entity(full_name="Daniel Brooks")]
    assert resolve_entity(candidates, "someone completely unrelated", "also unrelated") is None


def test_empty_candidates_returns_none():
    assert resolve_entity([], "anything", "anything") is None


def test_none_target_hint_and_raw_query_handled_gracefully():
    candidates = [_entity()]
    assert resolve_entity(candidates, None, "") is None


def test_duplicate_full_name_raises_ambiguous_instead_of_picking_first():
    # Two different customers named "Carla Jensen" - silently picking
    # whichever comes first in the list would risk updating the wrong
    # person's record. This must be surfaced as ambiguous, not guessed.
    carla_1 = _entity(id="c1", full_name="Carla Jensen", email="carla.jensen@yahoo.com")
    carla_2 = _entity(id="c2", full_name="Carla Jensen", email="carla.jensen@work.com")
    with pytest.raises(AmbiguousEntityError) as exc_info:
        resolve_entity([carla_1, carla_2], "carla jensen", "ignored")
    assert {m.id for m in exc_info.value.matches} == {"c1", "c2"}


def test_duplicate_token_subset_match_also_raises_ambiguous():
    carla_1 = _entity(id="c1", full_name="Carla Jensen")
    carla_2 = _entity(id="c2", full_name="Carla Smith")
    with pytest.raises(AmbiguousEntityError):
        resolve_entity([carla_1, carla_2], None, "update carla jensen smith account")


def test_unambiguous_id_match_wins_even_with_duplicate_names():
    carla_1 = _entity(id="c1", full_name="Carla Jensen")
    carla_2 = _entity(id="c2", full_name="Carla Jensen")
    # An exact id match is unambiguous on its own, even though the name
    # tier below it would have been ambiguous.
    assert resolve_entity([carla_1, carla_2], "c1", "ignored") is carla_1
