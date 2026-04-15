"""Tests for query functions."""

from __future__ import annotations

from genealogy.models import EventType
from genealogy.query import (
    ancestors_of,
    descendants_of,
    find_by_name,
    find_by_place,
    find_by_surname,
    find_by_year,
    find_by_year_range,
    find_living,
)


def test_find_by_name_case_insensitive_substring(simple_tree):
    results = find_by_name(simple_tree, "smith")
    ids = {p.id for p in results}
    # John, Robert, Tom, Sarah all have surname Smith
    assert ids == {"I1", "I3", "I5", "I6"}


def test_find_by_name_empty_query_returns_empty(simple_tree):
    assert find_by_name(simple_tree, "") == []
    assert find_by_name(simple_tree, "   ") == []


def test_find_by_name_partial_match(simple_tree):
    results = find_by_name(simple_tree, "rob")  # matches Robert
    assert len(results) == 1
    assert results[0].id == "I3"


def test_find_by_surname_exact_match(simple_tree):
    results = find_by_surname(simple_tree, "Jones")
    assert {p.id for p in results} == {"I2"}


def test_find_by_surname_does_not_partial_match(simple_tree):
    # 'Smi' should NOT match 'Smith' via exact-surname query
    assert find_by_surname(simple_tree, "Smi") == []


def test_find_by_year(simple_tree):
    # Robert born 1930
    results = find_by_year(simple_tree, 1930, EventType.BIRTH)
    assert {p.id for p in results} == {"I3"}


def test_find_by_year_any_event_type(simple_tree):
    # 1925 is Fam1 marriage — but that's a family event, not on persons
    # Use 1970 when John died
    results = find_by_year(simple_tree, 1970)
    assert {p.id for p in results} == {"I1"}


def test_find_by_year_range(simple_tree):
    # Anyone born in the 1960s
    results = find_by_year_range(simple_tree, 1960, 1969, EventType.BIRTH)
    assert {p.id for p in results} == {"I5", "I6"}


def test_find_by_place(simple_tree):
    # Alice born in Philadelphia
    results = find_by_place(simple_tree, "Philadelphia")
    assert {p.id for p in results} == {"I4"}


def test_find_by_place_case_insensitive(simple_tree):
    results = find_by_place(simple_tree, "BOSTON")
    # John born + died Boston, Mary died Boston, Robert born Boston
    ids = {p.id for p in results}
    assert {"I1", "I2", "I3"} <= ids


def test_find_living(simple_tree):
    # Tom and Sarah have no death event
    results = find_living(simple_tree)
    assert {p.id for p in results} == {"I5", "I6"}


def test_ancestors_of(simple_tree):
    # Tom's ancestors: parents + grandparents
    ancestors = ancestors_of(simple_tree, "I5")
    ids = {p.id for p in ancestors}
    assert ids == {"I3", "I4", "I1", "I2"}


def test_ancestors_respects_max_generations(simple_tree):
    ancestors = ancestors_of(simple_tree, "I5", max_generations=1)
    ids = {p.id for p in ancestors}
    # Only parents, not grandparents
    assert ids == {"I3", "I4"}


def test_descendants_of(simple_tree):
    # John's descendants: Robert, Tom, Sarah
    descendants = descendants_of(simple_tree, "I1")
    ids = {p.id for p in descendants}
    assert ids == {"I3", "I5", "I6"}
