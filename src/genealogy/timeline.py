"""Chronological timeline for a person.

A person's own events plus the 'contextual' events from their immediate
family (parents' deaths, spouse marriages, children's births). Events without
dates get included but sort to the end with 'unknown date' markers.
"""

from __future__ import annotations

from dataclasses import dataclass

from genealogy.models import Date, Event, EventType, Tree


@dataclass(frozen=True)
class TimelineEntry:
    date: Date | None
    event_type: EventType
    description: str
    subject_person_id: str  # The person whose event this is (may not be the timeline subject)
    is_own_event: bool  # True if this is the subject's own event, False if a relative's


def person_timeline(
    tree: Tree,
    person_id: str,
    include_family: bool = True,
) -> list[TimelineEntry]:
    """Return a chronologically sorted list of events relevant to a person's life.

    If include_family is True (default), adds contextual events from parents,
    spouses, and children (births, deaths, marriages). These are the moments
    that shaped the person's life even though they aren't the person's own
    events.
    """
    person = tree.person(person_id)
    if person is None:
        return []

    entries: list[TimelineEntry] = []

    # Person's own events
    for event in person.events:
        entries.append(
            TimelineEntry(
                date=event.date,
                event_type=event.type,
                description=_describe_own_event(event),
                subject_person_id=person.id,
                is_own_event=True,
            )
        )

    if include_family:
        # Parents' deaths
        for parent in tree.parents_of(person_id):
            if (death := parent.death()) is not None:
                name = parent.primary_name.full() if parent.primary_name else parent.id
                entries.append(
                    TimelineEntry(
                        date=death.date,
                        event_type=EventType.DEATH,
                        description=f"Parent {name} died",
                        subject_person_id=parent.id,
                        is_own_event=False,
                    )
                )

        # Spouse marriages (from the person's own spouse families)
        for fam_id in person.spouse_family_ids:
            fam = tree.family(fam_id)
            if fam is None:
                continue
            if (marriage := fam.marriage()) is not None:
                spouse_id = fam.wife_id if fam.husband_id == person_id else fam.husband_id
                spouse = tree.person(spouse_id) if spouse_id else None
                spouse_label = (
                    spouse.primary_name.full() if spouse and spouse.primary_name
                    else "spouse"
                )
                entries.append(
                    TimelineEntry(
                        date=marriage.date,
                        event_type=EventType.MARRIAGE,
                        description=f"Married {spouse_label}",
                        subject_person_id=person.id,
                        is_own_event=True,
                    )
                )

        # Children's births
        for child in tree.children_of(person_id):
            if (birth := child.birth()) is not None:
                name = child.primary_name.full() if child.primary_name else child.id
                entries.append(
                    TimelineEntry(
                        date=birth.date,
                        event_type=EventType.BIRTH,
                        description=f"Child {name} born",
                        subject_person_id=child.id,
                        is_own_event=False,
                    )
                )

    entries.sort(key=_entry_sort_key)
    return entries


def _entry_sort_key(entry: TimelineEntry) -> tuple[int, int, int]:
    if entry.date is None:
        return (9999, 13, 32)
    return entry.date.sort_key()


def _describe_own_event(event: Event) -> str:
    """Short human-readable summary of one of the subject's own events."""
    pieces: list[str] = [event.type.name.lower().capitalize()]
    if event.place:
        pieces.append(f"at {event.place.name}")
    if event.description:
        pieces.append(f"— {event.description}")
    return " ".join(pieces)
