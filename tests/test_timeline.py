"""Tests for timeline generation."""

from __future__ import annotations

from genealogy.models import EventType
from genealogy.timeline import person_timeline


def test_timeline_includes_own_events(simple_tree):
    entries = person_timeline(simple_tree, "I3", include_family=False)  # Robert
    types = [e.event_type for e in entries]
    assert EventType.BIRTH in types
    assert EventType.DEATH in types


def test_timeline_is_chronological(simple_tree):
    entries = person_timeline(simple_tree, "I3")  # Robert
    years = [e.date.year for e in entries if e.date and e.date.year is not None]
    assert years == sorted(years)


def test_timeline_includes_family_events_by_default(simple_tree):
    entries = person_timeline(simple_tree, "I3")  # Robert
    # Should include children's births (Tom 1960, Sarah 1965) and parents' deaths (John 1970, Mary 1975)
    descriptions = " ".join(e.description for e in entries)
    assert "Tom" in descriptions or "Sarah" in descriptions
    assert "John" in descriptions or "Mary" in descriptions


def test_timeline_family_events_can_be_excluded(simple_tree):
    with_family = person_timeline(simple_tree, "I3", include_family=True)
    without_family = person_timeline(simple_tree, "I3", include_family=False)
    assert len(with_family) > len(without_family)
    # Without family, all entries should be Robert's own
    assert all(e.subject_person_id == "I3" or e.is_own_event for e in without_family)


def test_timeline_marks_own_vs_contextual_events(simple_tree):
    entries = person_timeline(simple_tree, "I3")  # Robert
    own = [e for e in entries if e.is_own_event]
    contextual = [e for e in entries if not e.is_own_event]
    assert len(own) > 0
    assert len(contextual) > 0


def test_timeline_for_unknown_person_returns_empty(simple_tree):
    assert person_timeline(simple_tree, "nonexistent") == []


def test_timeline_includes_marriage(simple_tree):
    entries = person_timeline(simple_tree, "I3")  # Robert
    marriage_entries = [e for e in entries if e.event_type == EventType.MARRIAGE]
    assert len(marriage_entries) == 1
    assert marriage_entries[0].date.year == 1955
    assert "Alice" in marriage_entries[0].description
