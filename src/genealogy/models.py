"""Core domain model for a genealogical tree.

Loosely follows GEDCOM 5.5.1 structure but stays opinionated and typed.
A GEDCOM file parser (not yet built) will hydrate these objects; validation,
query, and timeline logic operate on them directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Sex(Enum):
    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"


class EventType(Enum):
    BIRTH = "BIRT"
    DEATH = "DEAT"
    MARRIAGE = "MARR"
    DIVORCE = "DIV"
    BURIAL = "BURI"
    CHRISTENING = "CHR"
    IMMIGRATION = "IMMI"
    RESIDENCE = "RESI"
    OCCUPATION = "OCCU"
    CENSUS = "CENS"
    OTHER = "OTHER"


class DateQualifier(Enum):
    """GEDCOM-flavored date qualifiers. Real data is rarely a clean yyyy-mm-dd."""

    EXACT = "exact"
    ABOUT = "about"  # ABT
    BEFORE = "before"  # BEF
    AFTER = "after"  # AFT
    ESTIMATED = "estimated"  # EST
    CALCULATED = "calculated"  # CAL


@dataclass(frozen=True)
class Date:
    """A genealogical date. Any of year/month/day may be unknown.

    We deliberately allow year=None to represent 'date is known to exist but
    year is unrecorded' — useful when a GEDCOM source says just 'March'.
    """

    year: int | None = None
    month: int | None = None
    day: int | None = None
    qualifier: DateQualifier = DateQualifier.EXACT

    def is_known(self) -> bool:
        return self.year is not None

    def sort_key(self) -> tuple[int, int, int]:
        """Key for chronological sorting. Unknown fields sort to the end."""
        return (
            self.year if self.year is not None else 9999,
            self.month if self.month is not None else 13,
            self.day if self.day is not None else 32,
        )


@dataclass(frozen=True)
class Place:
    name: str
    # Structured fields are optional; GEDCOM often has just a free-text name.
    city: str | None = None
    county: str | None = None
    state: str | None = None
    country: str | None = None


@dataclass(frozen=True)
class Name:
    given: str = ""
    surname: str = ""

    def full(self) -> str:
        parts = [p for p in (self.given, self.surname) if p]
        return " ".join(parts)


@dataclass(frozen=True)
class Source:
    """A citation. IDs are optional because some sources are inline-only."""

    id: str | None = None
    title: str = ""
    author: str | None = None
    publication: str | None = None
    page: str | None = None
    note: str | None = None


@dataclass
class Event:
    type: EventType
    date: Date | None = None
    place: Place | None = None
    description: str | None = None
    sources: list[Source] = field(default_factory=list)


@dataclass
class Person:
    id: str
    names: list[Name] = field(default_factory=list)
    sex: Sex = Sex.UNKNOWN
    events: list[Event] = field(default_factory=list)
    # Structural links — IDs into Tree.families, not object refs, to avoid cycles.
    parent_family_ids: list[str] = field(default_factory=list)
    spouse_family_ids: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)

    @property
    def primary_name(self) -> Name | None:
        return self.names[0] if self.names else None

    def events_of(self, event_type: EventType) -> list[Event]:
        return [e for e in self.events if e.type == event_type]

    def birth(self) -> Event | None:
        births = self.events_of(EventType.BIRTH)
        return births[0] if births else None

    def death(self) -> Event | None:
        deaths = self.events_of(EventType.DEATH)
        return deaths[0] if deaths else None


@dataclass
class Family:
    id: str
    husband_id: str | None = None
    wife_id: str | None = None
    child_ids: list[str] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)

    def marriage(self) -> Event | None:
        marriages = [e for e in self.events if e.type == EventType.MARRIAGE]
        return marriages[0] if marriages else None


@dataclass
class Tree:
    """A whole genealogical tree. Lookups by id are O(1)."""

    persons: dict[str, Person] = field(default_factory=dict)
    families: dict[str, Family] = field(default_factory=dict)

    def add_person(self, person: Person) -> None:
        self.persons[person.id] = person

    def add_family(self, family: Family) -> None:
        self.families[family.id] = family

    def person(self, person_id: str) -> Person | None:
        return self.persons.get(person_id)

    def family(self, family_id: str) -> Family | None:
        return self.families.get(family_id)

    def parents_of(self, person_id: str) -> list[Person]:
        person = self.person(person_id)
        if person is None:
            return []
        parents: list[Person] = []
        for fam_id in person.parent_family_ids:
            fam = self.family(fam_id)
            if fam is None:
                continue
            for parent_id in (fam.husband_id, fam.wife_id):
                if parent_id and (p := self.person(parent_id)):
                    parents.append(p)
        return parents

    def children_of(self, person_id: str) -> list[Person]:
        person = self.person(person_id)
        if person is None:
            return []
        children: list[Person] = []
        for fam_id in person.spouse_family_ids:
            fam = self.family(fam_id)
            if fam is None:
                continue
            for child_id in fam.child_ids:
                if c := self.person(child_id):
                    children.append(c)
        return children

    def spouses_of(self, person_id: str) -> list[Person]:
        person = self.person(person_id)
        if person is None:
            return []
        spouses: list[Person] = []
        for fam_id in person.spouse_family_ids:
            fam = self.family(fam_id)
            if fam is None:
                continue
            for spouse_id in (fam.husband_id, fam.wife_id):
                if spouse_id and spouse_id != person_id and (s := self.person(spouse_id)):
                    spouses.append(s)
        return spouses
