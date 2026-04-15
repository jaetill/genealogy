"""Convert a GEDCOM file into our domain Tree.

Thin adapter over `ged4py`. Handles GEDCOM 5.5.1 well (what Ancestry exports);
unknown or vendor-specific tags (e.g. Ancestry's `_APID`, `_MTTAG`) are ignored
rather than erroring — genealogy software loves custom extensions.
"""

from __future__ import annotations

from pathlib import Path

from ged4py.date import (
    DateValue,
    DateValueAbout,
    DateValueAfter,
    DateValueBefore,
    DateValueCalculated,
    DateValueEstimated,
    DateValuePeriod,
    DateValueRange,
    DateValueSimple,
)
from ged4py.parser import GedcomReader

from genealogy.models import (
    Date,
    DateQualifier,
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

# GEDCOM tag → EventType. Unknown tags fall through to EventType.OTHER.
_EVENT_TAGS: dict[str, EventType] = {
    "BIRT": EventType.BIRTH,
    "DEAT": EventType.DEATH,
    "MARR": EventType.MARRIAGE,
    "DIV": EventType.DIVORCE,
    "BURI": EventType.BURIAL,
    "CHR": EventType.CHRISTENING,
    "IMMI": EventType.IMMIGRATION,
    "RESI": EventType.RESIDENCE,
    "OCCU": EventType.OCCUPATION,
    "CENS": EventType.CENSUS,
}

# Events we'll pull off an Individual record.
_INDI_EVENT_TAGS = ("BIRT", "DEAT", "BURI", "CHR", "IMMI", "RESI", "OCCU", "CENS")

# Events we'll pull off a Family record.
_FAM_EVENT_TAGS = ("MARR", "DIV")

# GEDCOM uses 3-letter English month abbreviations. ged4py surfaces these as
# raw strings on CalendarDate.month rather than parsing them to integers.
_MONTH_TOKENS: dict[str, int] = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def parse_gedcom_file(path: str | Path) -> Tree:
    """Parse a GEDCOM file and return a Tree."""
    tree = Tree()
    with GedcomReader(str(path)) as reader:
        for indi in reader.records0("INDI"):
            person = _build_person(indi)
            tree.add_person(person)
        for fam in reader.records0("FAM"):
            family = _build_family(fam)
            tree.add_family(family)

    _wire_family_links(tree)
    return tree


def parse_gedcom_string(content: str) -> Tree:
    """Parse a GEDCOM string. Convenience for tests; writes to a temp file."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ged", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        temp_path = f.name
    try:
        return parse_gedcom_file(temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _strip_xref(xref: str | None) -> str:
    """GEDCOM xrefs look like '@I1@'; we drop the @ for cleaner internal ids."""
    if not xref:
        return ""
    return xref.strip("@")


def _build_person(indi) -> Person:
    person = Person(id=_strip_xref(indi.xref_id))

    # Names — ged4py's NameRec.value is a pre-split (given, surname, suffix) tuple.
    for name_rec in indi.sub_tags("NAME"):
        given, surname = _parse_name_value(name_rec.value)
        if given or surname:
            person.names.append(Name(given=given, surname=surname))

    # Sex
    if indi.sex:
        person.sex = _parse_sex(indi.sex)

    # Events (individual-level)
    for tag in _INDI_EVENT_TAGS:
        for event_rec in indi.sub_tags(tag):
            event = _build_event(event_rec, _EVENT_TAGS[tag])
            if event:
                person.events.append(event)

    # Family links — FAMC = parent families, FAMS = spouse families
    for famc in indi.sub_tags("FAMC"):
        fam_id = _strip_xref(famc.xref_id) if famc.xref_id else None
        if fam_id:
            person.parent_family_ids.append(fam_id)
    for fams in indi.sub_tags("FAMS"):
        fam_id = _strip_xref(fams.xref_id) if fams.xref_id else None
        if fam_id:
            person.spouse_family_ids.append(fam_id)

    # Person-level sources
    person.sources = _parse_sources(indi)

    return person


def _build_family(fam) -> Family:
    family = Family(id=_strip_xref(fam.xref_id))

    husb = fam.sub_tag("HUSB")
    if husb and husb.xref_id:
        family.husband_id = _strip_xref(husb.xref_id)
    wife = fam.sub_tag("WIFE")
    if wife and wife.xref_id:
        family.wife_id = _strip_xref(wife.xref_id)

    for child_rec in fam.sub_tags("CHIL"):
        if child_rec.xref_id:
            family.child_ids.append(_strip_xref(child_rec.xref_id))

    for tag in _FAM_EVENT_TAGS:
        for event_rec in fam.sub_tags(tag):
            event = _build_event(event_rec, _EVENT_TAGS[tag])
            if event:
                family.events.append(event)

    family.sources = _parse_sources(fam)

    return family


def _build_event(event_rec, event_type: EventType) -> Event | None:
    date = None
    place = None
    description = event_rec.value if event_rec.value else None

    date_rec = event_rec.sub_tag("DATE")
    if date_rec and date_rec.value:
        date = _parse_date(date_rec.value)

    place_rec = event_rec.sub_tag("PLAC")
    if place_rec and place_rec.value:
        place = Place(name=place_rec.value)

    sources = _parse_sources(event_rec)

    # Don't invent an event record from nothing — if there's literally no info,
    # skip it. (Rare, but guards against malformed GEDCOM.)
    if not (date or place or description or sources):
        return None

    return Event(
        type=event_type,
        date=date,
        place=place,
        description=description,
        sources=sources,
    )


def _parse_date(dv: DateValue) -> Date | None:
    """Map ged4py DateValue → our Date.

    For range/period dates (e.g. BET 1900 AND 1910, FROM 1900 TO 1910), we
    take the start date. This loses precision but keeps chronological sorting
    sensible. A future version could model ranges explicitly.
    """
    qualifier = _date_qualifier(dv)
    # Most DateValue types expose .date; range/period types expose .date1/.date2.
    calendar_date = None
    if hasattr(dv, "date") and dv.date is not None:
        calendar_date = dv.date
    elif hasattr(dv, "date1") and dv.date1 is not None:
        calendar_date = dv.date1

    if calendar_date is None:
        return None

    year = getattr(calendar_date, "year", None)
    month_raw = getattr(calendar_date, "month", None)
    day = getattr(calendar_date, "day", None)

    return Date(year=year, month=_normalize_month(month_raw), day=day, qualifier=qualifier)


def _normalize_month(raw) -> int | None:
    """GEDCOM months arrive as 3-letter tokens ('MAR'). Translate to 1-12."""
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        return _MONTH_TOKENS.get(raw.strip().upper())
    return None


def _date_qualifier(dv: DateValue) -> DateQualifier:
    if isinstance(dv, DateValueAbout):
        return DateQualifier.ABOUT
    if isinstance(dv, DateValueBefore):
        return DateQualifier.BEFORE
    if isinstance(dv, DateValueAfter):
        return DateQualifier.AFTER
    if isinstance(dv, DateValueEstimated):
        return DateQualifier.ESTIMATED
    if isinstance(dv, DateValueCalculated):
        return DateQualifier.CALCULATED
    # DateValueSimple, DateValueRange, DateValuePeriod, DateValueInterpreted, etc.
    return DateQualifier.EXACT


def _parse_sources(record) -> list[Source]:
    """Pull SOUR citations off a record.

    We iterate sub_records directly (not sub_tags('SOUR')) because ged4py's
    sub_tags auto-dereferences pointers to the target SOUR record — which
    discards the citation-level sub-tags (PAGE, QUAY, NOTE) that live on the
    pointer at the parent record's level, not on the referenced SOUR itself.
    """
    sources: list[Source] = []
    for sub in record.sub_records:
        if sub.tag != "SOUR":
            continue
        title = ""
        page = None
        source_id: str | None = None
        # Pointer-style: value is a raw xref string like '@S1@'.
        if isinstance(sub.value, str) and sub.value.startswith("@") and sub.value.endswith("@"):
            source_id = _strip_xref(sub.value)
        elif sub.value and isinstance(sub.value, str):
            # Inline-style: the value IS the title.
            title = sub.value

        # Citation-level sub-tags live here regardless of pointer vs inline.
        for citation_sub in sub.sub_records:
            if citation_sub.tag == "PAGE" and citation_sub.value:
                page = citation_sub.value
            elif citation_sub.tag == "TITL" and citation_sub.value and not title:
                title = citation_sub.value

        sources.append(Source(id=source_id, title=title, page=page))
    return sources


def _parse_sex(sex_str: str) -> Sex:
    normalized = sex_str.strip().upper()
    if normalized == "M":
        return Sex.MALE
    if normalized == "F":
        return Sex.FEMALE
    return Sex.UNKNOWN


def _parse_name_value(value) -> tuple[str, str]:
    """Extract (given, surname) from a NameRec.value.

    ged4py delivers NAME values in one of two shapes:
      - Pre-split tuple (given, surname, suffix) — the common case
      - Raw string 'John /Smith/' — rare, but possible on malformed input
    """
    if isinstance(value, tuple):
        given = (value[0] or "").strip() if len(value) > 0 else ""
        surname = (value[1] or "").strip() if len(value) > 1 else ""
        return given, surname
    if isinstance(value, str):
        if "/" in value:
            parts = value.split("/")
            given = parts[0].strip()
            surname = parts[1].strip() if len(parts) > 1 else ""
            return given, surname
        return value.strip(), ""
    return "", ""


def _wire_family_links(tree: Tree) -> None:
    """Populate each Person's parent_family_ids/spouse_family_ids from Family records.

    GEDCOM redundantly encodes family links on both sides (person's FAMC/FAMS
    and family's HUSB/WIFE/CHIL). If the input only has one side populated,
    this backfills the other for consistency.
    """
    for family in tree.families.values():
        for parent_id in (family.husband_id, family.wife_id):
            if not parent_id:
                continue
            person = tree.person(parent_id)
            if person and family.id not in person.spouse_family_ids:
                person.spouse_family_ids.append(family.id)
        for child_id in family.child_ids:
            person = tree.person(child_id)
            if person and family.id not in person.parent_family_ids:
                person.parent_family_ids.append(family.id)
