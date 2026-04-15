"""Data quality checks over a Tree.

Each check returns a list of Issue objects. Callers can aggregate, filter by
severity, or group by person. Nothing here raises — the point is to surface
problems for review, not to reject data.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from genealogy.models import EventType, Person, Tree

# Real family trees have outliers but >= 120 years is vanishingly rare.
# Used for lifespan sanity checks; tune if your tree hits false positives.
MAX_REASONABLE_AGE = 120
MIN_PARENT_AGE = 12
MAX_PARENT_AGE = 70


class Severity(Enum):
    ERROR = "error"  # Logically impossible — must be wrong
    WARNING = "warning"  # Unlikely but not impossible
    INFO = "info"  # Worth a human glance


@dataclass(frozen=True)
class Issue:
    severity: Severity
    code: str
    message: str
    person_ids: tuple[str, ...] = ()


def validate(tree: Tree) -> list[Issue]:
    """Run every check and return all issues."""
    issues: list[Issue] = []
    issues.extend(impossible_dates(tree))
    issues.extend(age_sanity(tree))
    issues.extend(missing_sources(tree))
    issues.extend(duplicate_persons(tree))
    return issues


def impossible_dates(tree: Tree) -> list[Issue]:
    """Flag logically impossible date ordering within a person's life."""
    issues: list[Issue] = []
    for person in tree.persons.values():
        birth = person.birth()
        death = person.death()
        if birth and death and birth.date and death.date:
            if birth.date.is_known() and death.date.is_known():
                if birth.date.sort_key() > death.date.sort_key():
                    issues.append(
                        Issue(
                            severity=Severity.ERROR,
                            code="BIRTH_AFTER_DEATH",
                            message=f"{_label(person)}: birth date is after death date",
                            person_ids=(person.id,),
                        )
                    )
    return issues


def age_sanity(tree: Tree) -> list[Issue]:
    """Lifespan and parent-age sanity."""
    issues: list[Issue] = []
    for person in tree.persons.values():
        birth = person.birth()
        death = person.death()
        # Lifespan > MAX_REASONABLE_AGE
        if (
            birth and death
            and birth.date and death.date
            and birth.date.year is not None
            and death.date.year is not None
        ):
            age = death.date.year - birth.date.year
            if age > MAX_REASONABLE_AGE:
                issues.append(
                    Issue(
                        severity=Severity.WARNING,
                        code="LIFESPAN_TOO_LONG",
                        message=f"{_label(person)}: lifespan of {age} years exceeds {MAX_REASONABLE_AGE}",
                        person_ids=(person.id,),
                    )
                )
        # Parent age at child's birth
        for child in tree.children_of(person.id):
            parent_birth = birth
            child_birth = child.birth()
            if (
                parent_birth and child_birth
                and parent_birth.date and child_birth.date
                and parent_birth.date.year is not None
                and child_birth.date.year is not None
            ):
                parent_age = child_birth.date.year - parent_birth.date.year
                if parent_age < MIN_PARENT_AGE:
                    issues.append(
                        Issue(
                            severity=Severity.WARNING,
                            code="PARENT_TOO_YOUNG",
                            message=(
                                f"{_label(person)} was {parent_age} at {_label(child)}'s birth "
                                f"(min sensible: {MIN_PARENT_AGE})"
                            ),
                            person_ids=(person.id, child.id),
                        )
                    )
                elif parent_age > MAX_PARENT_AGE:
                    issues.append(
                        Issue(
                            severity=Severity.WARNING,
                            code="PARENT_TOO_OLD",
                            message=(
                                f"{_label(person)} was {parent_age} at {_label(child)}'s birth "
                                f"(max sensible: {MAX_PARENT_AGE})"
                            ),
                            person_ids=(person.id, child.id),
                        )
                    )
    return issues


def missing_sources(tree: Tree) -> list[Issue]:
    """Every life event should have at least one source citation."""
    issues: list[Issue] = []
    for person in tree.persons.values():
        for event in person.events:
            if event.type in (EventType.BIRTH, EventType.DEATH, EventType.MARRIAGE) and not event.sources:
                issues.append(
                    Issue(
                        severity=Severity.INFO,
                        code="MISSING_SOURCE",
                        message=f"{_label(person)}: {event.type.name.lower()} has no source",
                        person_ids=(person.id,),
                    )
                )
    return issues


def duplicate_persons(tree: Tree) -> list[Issue]:
    """People with identical full name + birth year are very likely the same person.

    Birth year alone catches the common case (imported the same ancestor twice).
    False positives are fine — this is INFO severity, meant to prompt review.
    """
    issues: list[Issue] = []
    buckets: dict[tuple[str, int], list[Person]] = {}
    for person in tree.persons.values():
        name = person.primary_name
        birth = person.birth()
        if not name or not birth or not birth.date or birth.date.year is None:
            continue
        key = (name.full().lower(), birth.date.year)
        buckets.setdefault(key, []).append(person)

    for (full_name, year), people in buckets.items():
        if len(people) > 1:
            ids = tuple(p.id for p in people)
            issues.append(
                Issue(
                    severity=Severity.INFO,
                    code="POSSIBLE_DUPLICATE",
                    message=f"{len(people)} persons share name '{full_name}' + birth year {year}",
                    person_ids=ids,
                )
            )
    return issues


def _label(person: Person) -> str:
    """Short human-readable label for issue messages."""
    name = person.primary_name
    return f"{name.full()} [{person.id}]" if name else f"[{person.id}]"
