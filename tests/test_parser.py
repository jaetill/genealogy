"""Tests for the GEDCOM parser.

Uses inline GEDCOM strings rather than fixture files so each test case shows
its own input next to its assertions. The test at the bottom exercises the
bundled Ancestry-style sample file to catch real-world vendor quirks.
"""

from __future__ import annotations

from pathlib import Path

from genealogy.models import DateQualifier, EventType, Sex
from genealogy.parser import parse_gedcom_file, parse_gedcom_string

# Re-used minimal header; every test GEDCOM string needs a TRLR too.
_HEADER = """0 HEAD
1 GEDC
2 VERS 5.5.1
2 FORM LINEAGE-LINKED
1 CHAR UTF-8
"""


def _gedcom(body: str) -> str:
    # Strip leading/trailing blank lines from the body so triple-quoted test
    # strings don't introduce blank lines between records (ged4py rejects them).
    return _HEADER + body.strip("\n") + "\n0 TRLR\n"


def test_parses_single_individual_with_name_and_sex():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
"""))
    person = tree.person("I1")
    assert person is not None
    assert person.primary_name.given == "John"
    assert person.primary_name.surname == "Smith"
    assert person.sex == Sex.MALE


def test_parses_birth_event_with_date_and_place():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 NAME John /Smith/
1 BIRT
2 DATE 15 MAR 1900
2 PLAC Boston, MA
"""))
    person = tree.person("I1")
    birth = person.birth()
    assert birth is not None
    assert birth.date.year == 1900
    assert birth.date.month == 3
    assert birth.date.day == 15
    assert birth.place.name == "Boston, MA"


def test_parses_approximate_date_qualifier():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 NAME Jane /Doe/
1 BIRT
2 DATE ABT 1900
"""))
    birth = tree.person("I1").birth()
    assert birth.date.year == 1900
    assert birth.date.qualifier == DateQualifier.ABOUT


def test_parses_before_and_after_date_qualifiers():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 BIRT
2 DATE BEF 1910
0 @I2@ INDI
1 BIRT
2 DATE AFT 1920
"""))
    assert tree.person("I1").birth().date.qualifier == DateQualifier.BEFORE
    assert tree.person("I2").birth().date.qualifier == DateQualifier.AFTER


def test_parses_death_event():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 DEAT
2 DATE 1 JUN 1980
"""))
    death = tree.person("I1").death()
    assert death is not None
    assert death.date.year == 1980


def test_parses_family_with_husband_wife_children():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 NAME John /Smith/
1 SEX M
0 @I2@ INDI
1 NAME Mary /Jones/
1 SEX F
0 @I3@ INDI
1 NAME Robert /Smith/
1 SEX M
0 @I4@ INDI
1 NAME Susan /Smith/
1 SEX F
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
1 CHIL @I4@
"""))
    family = tree.family("F1")
    assert family.husband_id == "I1"
    assert family.wife_id == "I2"
    assert family.child_ids == ["I3", "I4"]


def test_family_marriage_is_parsed():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
0 @I2@ INDI
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 MARR
2 DATE 1 JUN 1925
2 PLAC Boston, MA
"""))
    family = tree.family("F1")
    marriage = family.marriage()
    assert marriage is not None
    assert marriage.date.year == 1925
    assert marriage.place.name == "Boston, MA"


def test_family_links_are_wired_on_persons():
    """Even when GEDCOM only encodes links from the family side (HUSB/WIFE/CHIL),
    the parser should backfill the corresponding FAMS/FAMC on each person.
    """
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
0 @I2@ INDI
0 @I3@ INDI
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
"""))
    assert tree.person("I1").spouse_family_ids == ["F1"]
    assert tree.person("I2").spouse_family_ids == ["F1"]
    assert tree.person("I3").parent_family_ids == ["F1"]


def test_parent_traversal_works_after_parse():
    """End-to-end: parsing produces a Tree that the query helpers can traverse."""
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 NAME John /Smith/
0 @I2@ INDI
1 NAME Mary /Jones/
0 @I3@ INDI
1 NAME Robert /Smith/
0 @F1@ FAM
1 HUSB @I1@
1 WIFE @I2@
1 CHIL @I3@
"""))
    parents = tree.parents_of("I3")
    names = {p.primary_name.full() for p in parents}
    assert names == {"John Smith", "Mary Jones"}


def test_unknown_sex_value_becomes_unknown_enum():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 NAME A /B/
1 SEX U
"""))
    assert tree.person("I1").sex == Sex.UNKNOWN


def test_inline_source_citation_captured():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 BIRT
2 DATE 1 JAN 1900
2 SOUR Family bible entry
"""))
    birth = tree.person("I1").birth()
    assert len(birth.sources) == 1
    assert birth.sources[0].title == "Family bible entry"


def test_pointer_source_citation_captured():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 BIRT
2 DATE 1 JAN 1900
2 SOUR @S1@
3 PAGE p.42
0 @S1@ SOUR
1 TITL County birth register
"""))
    birth = tree.person("I1").birth()
    assert len(birth.sources) == 1
    assert birth.sources[0].id == "S1"
    assert birth.sources[0].page == "p.42"


def test_ancestry_style_custom_tags_are_ignored():
    """Ancestry adds non-standard tags like _APID. Parser should ignore them
    rather than erroring out.
    """
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 NAME Test /Person/
1 _APID 1,123::456
1 BIRT
2 DATE 1 JAN 1900
2 _APID 1,123::789
"""))
    person = tree.person("I1")
    assert person is not None
    assert person.primary_name.full() == "Test Person"
    assert person.birth().date.year == 1900


def test_missing_name_produces_person_without_names():
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 SEX M
"""))
    person = tree.person("I1")
    assert person is not None
    assert person.names == []
    assert person.primary_name is None


def test_multiple_events_of_same_type():
    """A person can have multiple residences, multiple census events, etc."""
    tree = parse_gedcom_string(_gedcom("""
0 @I1@ INDI
1 RESI
2 DATE 1920
2 PLAC Boston, MA
1 RESI
2 DATE 1930
2 PLAC Richmond, VA
"""))
    person = tree.person("I1")
    residences = person.events_of(EventType.RESIDENCE)
    assert len(residences) == 2


def test_parse_from_file(tmp_path):
    """Round-trip: write a GEDCOM file to disk, parse it back."""
    gedcom_text = _gedcom("""
0 @I1@ INDI
1 NAME File /Roundtrip/
1 BIRT
2 DATE 1 JAN 2000
""")
    path = tmp_path / "test.ged"
    path.write_text(gedcom_text, encoding="utf-8")
    tree = parse_gedcom_file(path)
    assert tree.person("I1").primary_name.surname == "Roundtrip"
    assert tree.person("I1").birth().date.year == 2000


def test_sample_file_parses_end_to_end():
    """End-to-end check against the bundled Ancestry-style sample file.

    The sample mimics what a real Ancestry export looks like: 4 generations,
    custom `_APID` tags, pointer-style source citations with PAGE sub-tags,
    census records, and mixed exact/approximate dates. If this test breaks,
    something about real-world GEDCOM handling has regressed.
    """
    sample_path = Path(__file__).parent / "fixtures" / "sample_ancestry.ged"
    import pytest
    if not sample_path.exists():
        pytest.skip("sample file not present")
    tree = parse_gedcom_file(sample_path)

    # Structure
    assert len(tree.persons) == 8
    assert len(tree.families) == 3

    # Great-grandfather John Tilley
    john = tree.person("I1")
    assert john.primary_name.full() == "John Tilley"
    assert john.sex == Sex.MALE
    assert john.birth().date.year == 1871
    assert john.birth().date.month == 6
    assert john.birth().place.name == "Richmond, Virginia, USA"
    assert len(john.birth().sources) == 1
    assert john.birth().sources[0].id == "S1"
    assert john.birth().sources[0].page == "Registration District 42, Entry 117"

    # Approximate date handling — Martha's death is 'ABT 1945'
    martha = tree.person("I2")
    assert martha.death().date.year == 1945
    assert martha.death().date.qualifier == DateQualifier.ABOUT

    # Multi-event: William (I3) has two CENS events and an IMMI with BEF qualifier
    william = tree.person("I3")
    censuses = william.events_of(EventType.CENSUS)
    assert len(censuses) == 2
    assert {c.date.year for c in censuses} == {1920, 1930}
    immigrations = william.events_of(EventType.IMMIGRATION)
    assert len(immigrations) == 1
    assert immigrations[0].date.qualifier == DateQualifier.BEFORE

    # 4-generation ancestry chain still traverses after parse
    from genealogy.query import ancestors_of
    elizabeth = tree.person("I8")
    assert elizabeth.primary_name.given == "Elizabeth"
    ancestor_ids = {p.id for p in ancestors_of(tree, "I8")}
    assert {"I5", "I6", "I3", "I4", "I1", "I2"} <= ancestor_ids
