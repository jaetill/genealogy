# Genealogy — CLAUDE.md

## What it does
Genealogy research automation tool that augments (not replaces) Jason and his mom's Ancestry.com workflow. Combines FamilySearch's public API for record search and cross-referencing with local GEDCOM processing to automate the tedious parts of genealogy — source validation, data quality checks, branch-building suggestions, and record discovery. Includes an MCP server for Claude-assisted research sessions.

## Status: Early Stage
No code written yet. Project scaffolded with research and planning docs. Jason is completing CCA-F Phase 2 (MCP Fundamentals, Week 4) before building — this project is a candidate for the Week 4 hands-on exercise.

## Tech stack & hosting
| Layer | Technology | Notes |
|---|---|---|
| Language | Python | FamilySearch SDK is Python; GEDCOM libs are Python |
| MCP Server | Python (`mcp` SDK) | stdio transport for Claude Code, Streamable HTTP TBD |
| External API | FamilySearch API | OAuth2, free, well-documented |
| Data format | GEDCOM 5.5.1 | What Ancestry exports; 7.0 support is a stretch goal |
| Hosting | Local only (initially) | MCP server runs on Jason's machine |
| Package manager | uv | Installed and in PATH; matches Anthropic Academy course tooling |

## Key design decisions
- **Ancestry is read-only from our perspective.** No scraping, no unofficial API access. Data comes in/out via GEDCOM export/import only.
- **FamilySearch is the programmatic workhorse.** Free API, good Python SDK, OAuth2 auth. Use it for record search, pedigree traversal, cross-referencing.
- **MCP server is the interface.** Claude uses tools to search records, analyze GEDCOM data, suggest next research steps. Jason stays in the loop for all decisions.
- **GEDCOM is the bridge.** Export from Ancestry → process locally → import enriched data back. Manual at the export/import step; automated in between.

## Architecture (planned)
```
Ancestry.com (GEDCOM export/import — manual)
       ↕
Local GEDCOM files (~/genealogy-data/ or similar)
       ↕
genealogy MCP server
  ├── GEDCOM tools: parse, query, validate, enrich
  ├── FamilySearch tools: search records, traverse pedigree, cross-reference
  └── Analysis tools: data quality, timeline generation, branch suggestions
       ↕
Claude Code / Claude Desktop (via stdio transport)
```

## MCP tools (planned)
| Tool | Purpose |
|---|---|
| `parse_gedcom` | Load and parse a local GEDCOM file |
| `search_person` | Search GEDCOM tree by name, date, place |
| `validate_tree` | Find inconsistencies — impossible dates, missing sources, duplicates |
| `search_familysearch` | Search FamilySearch records for a person |
| `cross_reference` | Compare local GEDCOM person against FamilySearch matches |
| `suggest_research` | Given a person, suggest next records to look for |
| `build_timeline` | Generate chronological narrative from scattered records |
| `export_enriched` | Write enriched GEDCOM back to file for Ancestry import |

## FamilySearch API
- Developer portal: https://developers.familysearch.org
- Auth: OAuth2 (3-legged flow — real-world complexity the course's toy examples skip)
- Python SDK available
- **Registration status: NOT YET REGISTERED** — do this before writing any API code

## Dependencies (not yet installed)
- `mcp` — MCP Python SDK
- `python-gedcom` or `ged4py` — GEDCOM parsing
- FamilySearch Python SDK (TBD — evaluate options)
- `httpx` or `requests` — HTTP client for FamilySearch API

## Existing community tools to evaluate
- **GEDCOM Genealogy MCP** — processes local GEDCOM files, runs offline
- **Gramps Web MCP** — 24 tools for tree exploration, connects to Gramps
- **Autoresearch Genealogy** — structured prompts for Claude-assisted research

## What does NOT belong here
- Ancestry scraping or unofficial API access (ToS violation risk)
- DNA analysis (separate domain, Ancestry-only data)
- Anything that requires Ancestry credentials or session tokens
