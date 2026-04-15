"""Tests for tree validation checks."""

from __future__ import annotations

from genealogy.validation import (
    Severity,
    age_sanity,
    duplicate_persons,
    impossible_dates,
    missing_sources,
    validate,
)


def test_clean_tree_has_no_issues(simple_tree):
    issues = validate(simple_tree)
    assert issues == []


def test_impossible_dates_detects_birth_after_death(broken_tree):
    issues = impossible_dates(broken_tree)
    codes = {i.code for i in issues}
    assert "BIRTH_AFTER_DEATH" in codes
    time_traveler_issues = [i for i in issues if "B1" in i.person_ids]
    assert len(time_traveler_issues) == 1
    assert time_traveler_issues[0].severity == Severity.ERROR


def test_age_sanity_flags_implausible_lifespan(broken_tree):
    issues = age_sanity(broken_tree)
    codes = {i.code for i in issues}
    assert "LIFESPAN_TOO_LONG" in codes


def test_age_sanity_flags_too_young_parent(broken_tree):
    issues = age_sanity(broken_tree)
    too_young = [i for i in issues if i.code == "PARENT_TOO_YOUNG"]
    assert len(too_young) == 1
    assert "B6" in too_young[0].person_ids and "B7" in too_young[0].person_ids


def test_missing_sources_detected(broken_tree):
    issues = missing_sources(broken_tree)
    codes = {i.code for i in issues}
    assert "MISSING_SOURCE" in codes
    # B3 has both birth and death without sources → 2 issues
    b3_issues = [i for i in issues if "B3" in i.person_ids]
    assert len(b3_issues) == 2


def test_duplicate_persons_detected(broken_tree):
    issues = duplicate_persons(broken_tree)
    assert len(issues) == 1
    assert issues[0].code == "POSSIBLE_DUPLICATE"
    assert set(issues[0].person_ids) == {"B4", "B5"}


def test_validate_aggregates_all_checks(broken_tree):
    issues = validate(broken_tree)
    codes = {i.code for i in issues}
    # At least one of each expected check should fire
    assert "BIRTH_AFTER_DEATH" in codes
    assert "LIFESPAN_TOO_LONG" in codes
    assert "MISSING_SOURCE" in codes
    assert "POSSIBLE_DUPLICATE" in codes
    assert "PARENT_TOO_YOUNG" in codes
