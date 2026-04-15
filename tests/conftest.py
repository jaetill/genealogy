"""Shared test fixtures.

Builds small in-memory Trees that exercise the modules without needing a real
GEDCOM file. When the parser arrives, a parallel fixture loading a real .ged
file can be added here without changing the existing tests.
"""

from __future__ import annotations

import pytest

from genealogy.models import (
    Date,
    Event,
    EventType,
    Family,
    Name,
    Person,
    Place,
    Sex,
    Source,
    Tree,
)


def _place(name: str) -> Place:
    return Place(name=name)


def _date(year: int, month: int | None = None, day: int | None = None) -> Date:
    return Date(year=year, month=month, day=day)


def _source(title: str) -> Source:
    return Source(title=title)


@pytest.fixture
def simple_tree() -> Tree:
    """Three generations of a Smith family with well-formed data.

    Generation 1: John Smith (1900-1970) + Mary Jones (1902-1975), married 1925
    Generation 2: Robert Smith (1930-2010) + Alice Brown (1932-2015), married 1955
    Generation 3: Tom Smith (1960-), Sarah Smith (1965-)
    """
    tree = Tree()

    # Grandparents
    john = Person(
        id="I1",
        names=[Name(given="John", surname="Smith")],
        sex=Sex.MALE,
        events=[
            Event(EventType.BIRTH, _date(1900, 3, 15), _place("Boston, MA"), sources=[_source("Birth cert I1")]),
            Event(EventType.DEATH, _date(1970, 11, 2), _place("Boston, MA"), sources=[_source("Death cert I1")]),
        ],
    )
    mary = Person(
        id="I2",
        names=[Name(given="Mary", surname="Jones")],
        sex=Sex.FEMALE,
        events=[
            Event(EventType.BIRTH, _date(1902, 6, 20), _place("Chicago, IL"), sources=[_source("Birth cert I2")]),
            Event(EventType.DEATH, _date(1975, 1, 8), _place("Boston, MA"), sources=[_source("Death cert I2")]),
        ],
    )

    # Parents
    robert = Person(
        id="I3",
        names=[Name(given="Robert", surname="Smith")],
        sex=Sex.MALE,
        events=[
            Event(EventType.BIRTH, _date(1930, 8, 1), _place("Boston, MA"), sources=[_source("Birth cert I3")]),
            Event(EventType.DEATH, _date(2010, 4, 12), _place("Richmond, VA"), sources=[_source("Death cert I3")]),
        ],
    )
    alice = Person(
        id="I4",
        names=[Name(given="Alice", surname="Brown")],
        sex=Sex.FEMALE,
        events=[
            Event(EventType.BIRTH, _date(1932, 2, 14), _place("Philadelphia, PA"), sources=[_source("Birth cert I4")]),
            Event(EventType.DEATH, _date(2015, 9, 3), _place("Richmond, VA"), sources=[_source("Death cert I4")]),
        ],
    )

    # Children (living — no death event)
    tom = Person(
        id="I5",
        names=[Name(given="Tom", surname="Smith")],
        sex=Sex.MALE,
        events=[
            Event(EventType.BIRTH, _date(1960, 5, 10), _place("Richmond, VA"), sources=[_source("Birth cert I5")]),
        ],
    )
    sarah = Person(
        id="I6",
        names=[Name(given="Sarah", surname="Smith")],
        sex=Sex.FEMALE,
        events=[
            Event(EventType.BIRTH, _date(1965, 12, 1), _place("Richmond, VA"), sources=[_source("Birth cert I6")]),
        ],
    )

    # Families
    fam1 = Family(
        id="F1",
        husband_id="I1",
        wife_id="I2",
        child_ids=["I3"],
        events=[Event(EventType.MARRIAGE, _date(1925, 6, 1), _place("Boston, MA"), sources=[_source("Marriage cert F1")])],
    )
    fam2 = Family(
        id="F2",
        husband_id="I3",
        wife_id="I4",
        child_ids=["I5", "I6"],
        events=[Event(EventType.MARRIAGE, _date(1955, 9, 20), _place("Philadelphia, PA"), sources=[_source("Marriage cert F2")])],
    )

    # Wire family references into persons
    john.spouse_family_ids = ["F1"]
    mary.spouse_family_ids = ["F1"]
    robert.parent_family_ids = ["F1"]
    robert.spouse_family_ids = ["F2"]
    alice.spouse_family_ids = ["F2"]
    tom.parent_family_ids = ["F2"]
    sarah.parent_family_ids = ["F2"]

    for person in (john, mary, robert, alice, tom, sarah):
        tree.add_person(person)
    for family in (fam1, fam2):
        tree.add_family(family)
    return tree


@pytest.fixture
def broken_tree() -> Tree:
    """Tree with intentional data quality issues — drives validation tests."""
    tree = Tree()

    # Impossible: birth after death
    timetraveler = Person(
        id="B1",
        names=[Name(given="Jane", surname="Doe")],
        events=[
            Event(EventType.BIRTH, _date(1950, 1, 1), sources=[_source("src")]),
            Event(EventType.DEATH, _date(1940, 1, 1), sources=[_source("src")]),
        ],
    )

    # Implausibly long lifespan
    methuselah = Person(
        id="B2",
        names=[Name(given="Old", surname="Person")],
        events=[
            Event(EventType.BIRTH, _date(1800, 1, 1), sources=[_source("src")]),
            Event(EventType.DEATH, _date(1950, 1, 1), sources=[_source("src")]),
        ],
    )

    # Missing sources
    undocumented = Person(
        id="B3",
        names=[Name(given="No", surname="Source")],
        events=[
            Event(EventType.BIRTH, _date(1900, 1, 1)),  # no sources
            Event(EventType.DEATH, _date(1980, 1, 1)),  # no sources
        ],
    )

    # Duplicates (same name + birth year)
    dupe_a = Person(
        id="B4",
        names=[Name(given="Twin", surname="Dup")],
        events=[Event(EventType.BIRTH, _date(1920), sources=[_source("src")])],
    )
    dupe_b = Person(
        id="B5",
        names=[Name(given="Twin", surname="Dup")],
        events=[Event(EventType.BIRTH, _date(1920), sources=[_source("src")])],
    )

    # Too-young parent
    young_parent = Person(
        id="B6",
        names=[Name(given="Young", surname="Parent")],
        events=[Event(EventType.BIRTH, _date(2000, 1, 1), sources=[_source("src")])],
    )
    young_child = Person(
        id="B7",
        names=[Name(given="Too", surname="Early")],
        events=[Event(EventType.BIRTH, _date(2005, 1, 1), sources=[_source("src")])],
    )
    fam = Family(id="FB1", husband_id="B6", child_ids=["B7"])
    young_parent.spouse_family_ids = ["FB1"]
    young_child.parent_family_ids = ["FB1"]

    for person in (timetraveler, methuselah, undocumented, dupe_a, dupe_b, young_parent, young_child):
        tree.add_person(person)
    tree.add_family(fam)
    return tree
