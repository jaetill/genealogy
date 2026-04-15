# genealogy

Personal family history research automation. Augments (rather than replaces) an
Ancestry.com workflow by processing local GEDCOM exports and cross-referencing
them against the FamilySearch API, with an MCP server that lets Claude assist
with research sessions.

## What it does

- **Parse and query GEDCOM files** exported from Ancestry or other genealogy
  software — search by name, date, or place; traverse family relationships.
- **Validate tree data quality** — flag impossible dates, missing source
  citations, suspicious parent ages, and likely duplicate entries.
- **Build chronological timelines** for any person in the tree.
- **Cross-reference against FamilySearch** records to find candidate matches
  and enrich existing entries (planned).
- **Expose all of this to Claude** via a Model Context Protocol server so
  natural-language research questions can be answered from tree and record
  data together (planned).

The human stays in the loop for every change — the tool surfaces candidates
and flags issues; it does not auto-edit the tree.

## Status

Early stage. Domain model, validation, query, and timeline modules are in
progress. The GEDCOM-file parser and FamilySearch integration are still to
come.

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12+ |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| GEDCOM parsing | `ged4py` / `python-gedcom` (TBD) |
| External API | FamilySearch (OAuth2) |
| AI integration | [Model Context Protocol](https://modelcontextprotocol.io) — stdio transport |
| Tests | pytest |

## Development

```bash
uv sync
uv run pytest
```

## Scope and limits

- **Ancestry.com is read-only from this tool's perspective.** Data flows in
  and out via manual GEDCOM export/import only — no scraping, no unofficial
  API access.
- **FamilySearch is the programmatic workhorse.** Free public API, OAuth2,
  well-documented.
- **Single-user, local install.** Nothing is hosted, republished, or shared
  outside the user's machine.

## License

Personal project; no license granted for redistribution.
