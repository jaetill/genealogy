"""Tests for the domain model — traversal, lookups, property accessors."""

from __future__ import annotations

from genealogy.models import Date, DateQualifier, EventType, Name, Tree


def test_date_sort_key_with_full_date():
    d = Date(year=1950, month=6, day=15)
    assert d.sort_key() == (1950, 6, 15)


def test_date_sort_key_with_unknown_fields():
    # Unknown fields sort after everything else in that position
    assert Date(year=1950).sort_key() == (1950, 13, 32)
    assert Date().sort_key() == (9999, 13, 32)


def test_date_is_known():
    assert Date(year=1950).is_known()
    assert not Date().is_known()


def test_date_qualifier_defaults_to_exact():
    assert Date(year=1950).qualifier == DateQualifier.EXACT


def test_name_full():
    assert Name(given="John", surname="Smith").full() == "John Smith"
    assert Name(given="John").full() == "John"
    assert Name(surname="Smith").full() == "Smith"
    assert Name().full() == ""


def test_person_primary_name_with_multiple_names(simple_tree):
    john = simple_tree.person("I1")
    assert john.primary_name.given == "John"
    assert john.primary_name.surname == "Smith"


def test_person_events_of(simple_tree):
    john = simple_tree.person("I1")
    births = john.events_of(EventType.BIRTH)
    assert len(births) == 1
    assert births[0].date.year == 1900


def test_person_birth_and_death_helpers(simple_tree):
    john = simple_tree.person("I1")
    assert john.birth().date.year == 1900
    assert john.death().date.year == 1970


def test_person_birth_death_return_none_when_missing(simple_tree):
    tom = simple_tree.person("I5")  # no death recorded
    assert tom.birth() is not None
    assert tom.death() is None


def test_tree_parents_of(simple_tree):
    parents = simple_tree.parents_of("I3")  # Robert
    parent_ids = {p.id for p in parents}
    assert parent_ids == {"I1", "I2"}


def test_tree_children_of(simple_tree):
    children = simple_tree.children_of("I3")  # Robert + Alice
    child_ids = {c.id for c in children}
    assert child_ids == {"I5", "I6"}


def test_tree_spouses_of(simple_tree):
    spouses = simple_tree.spouses_of("I3")  # Robert
    assert len(spouses) == 1
    assert spouses[0].id == "I4"


def test_tree_parents_of_returns_empty_for_unknown_person():
    tree = Tree()
    assert tree.parents_of("nonexistent") == []


def test_family_marriage_helper(simple_tree):
    fam = simple_tree.family("F1")
    marriage = fam.marriage()
    assert marriage is not None
    assert marriage.date.year == 1925
