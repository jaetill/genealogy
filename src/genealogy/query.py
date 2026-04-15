"""Search and lookup functions over a Tree.

All queries are read-only and return plain lists. Names match
case-insensitively and use substring search by default — genealogy data
is messy (nicknames, misspellings, transliterations), so loose matching is
usually what you want.
"""

from __future__ import annotations

from genealogy.models import EventType, Person, Tree


def find_by_name(tree: Tree, query: str) -> list[Person]:
    """Substring match (case-insensitive) against any of a person's names.

    Matches against the full name, given name, or surname. A person with
    multiple recorded names (e.g. maiden + married) matches if any of them hit.
    """
    needle = query.strip().lower()
    if not needle:
        return []
    results: list[Person] = []
    for person in tree.persons.values():
        for name in person.names:
            full = name.full().lower()
            if needle in full or needle in name.given.lower() or needle in name.surname.lower():
                results.append(person)
                break
    return results


def find_by_surname(tree: Tree, surname: str) -> list[Person]:
    """Exact (case-insensitive) surname match — useful for family-branch queries."""
    target = surname.strip().lower()
    if not target:
        return []
    return [
        p for p in tree.persons.values()
        if any(n.surname.lower() == target for n in p.names)
    ]


def find_by_year(tree: Tree, year: int, event_type: EventType | None = None) -> list[Person]:
    """People with an event in the given year. If event_type is None, any event type."""
    results: list[Person] = []
    for person in tree.persons.values():
        for event in person.events:
            if event_type is not None and event.type != event_type:
                continue
            if event.date and event.date.year == year:
                results.append(person)
                break
    return results


def find_by_year_range(
    tree: Tree,
    start: int,
    end: int,
    event_type: EventType | None = None,
) -> list[Person]:
    """People with an event in [start, end] inclusive."""
    if start > end:
        start, end = end, start
    results: list[Person] = []
    for person in tree.persons.values():
        for event in person.events:
            if event_type is not None and event.type != event_type:
                continue
            if event.date and event.date.year is not None and start <= event.date.year <= end:
                results.append(person)
                break
    return results


def find_by_place(tree: Tree, place_query: str) -> list[Person]:
    """People with any event at a place whose name contains the query (case-insensitive)."""
    needle = place_query.strip().lower()
    if not needle:
        return []
    results: list[Person] = []
    for person in tree.persons.values():
        for event in person.events:
            if event.place and needle in event.place.name.lower():
                results.append(person)
                break
    return results


def find_living(tree: Tree) -> list[Person]:
    """People with a birth event and no death event recorded.

    Naive by design — real genealogy tools supplement this with 'probably
    deceased if birth year > 120 years ago' and similar heuristics.
    """
    return [
        p for p in tree.persons.values()
        if p.birth() is not None and p.death() is None
    ]


def ancestors_of(tree: Tree, person_id: str, max_generations: int = 10) -> list[Person]:
    """Breadth-first ancestor walk. Deduplicates — a person who appears in
    multiple lines (pedigree collapse) is returned once.
    """
    seen: set[str] = set()
    result: list[Person] = []
    frontier = [(person_id, 0)]
    while frontier:
        current_id, depth = frontier.pop(0)
        if depth >= max_generations:
            continue
        for parent in tree.parents_of(current_id):
            if parent.id in seen:
                continue
            seen.add(parent.id)
            result.append(parent)
            frontier.append((parent.id, depth + 1))
    return result


def descendants_of(tree: Tree, person_id: str, max_generations: int = 10) -> list[Person]:
    """Breadth-first descendant walk. Deduplicates."""
    seen: set[str] = set()
    result: list[Person] = []
    frontier = [(person_id, 0)]
    while frontier:
        current_id, depth = frontier.pop(0)
        if depth >= max_generations:
            continue
        for child in tree.children_of(current_id):
            if child.id in seen:
                continue
            seen.add(child.id)
            result.append(child)
            frontier.append((child.id, depth + 1))
    return result
