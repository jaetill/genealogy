# Ancestry.com API & Automation Options

*Research compiled April 2026 — originally from Dispatch, saved to Ancestry work project*

---

## 1. Ancestry.com Public API — Dead

Ancestry does not have a public API and hasn't for years. They had one briefly in the early 2010s, but it was shut down. There's no developer portal, no API keys, no official way to programmatically access tree data, search records, or pull DNA results.

What does exist is an undocumented internal REST API that Ancestry's own apps and select partners use. As of early 2026, Ancestry migrated this to a "new API" — which broke older versions of partner apps like RootsMagic (anything before v11.1.0). This confirms the API exists and is actively maintained, but it's not something you can register for or build against with any stability guarantee.

**Bottom line:** No official programmatic access. Ancestry treats their data as a walled garden.

## 2. Unofficial Tools & Scrapers

Several community tools exist, but they operate in a legal gray area since Ancestry's Terms of Service explicitly prohibit bots, crawlers, and scrapers:

- **Ancestry Image Downloader** — Browser-based tool to bulk download images/documents attached to your tree
- **ancestry-tools** — Python utilities for downloading your own GEDCOM files and media from Ancestry
- **Genscrape** — JavaScript library for scraping genealogy websites (including Ancestry)

**Risk:** Ancestry can and does terminate accounts for ToS violations related to automated access. These tools are generally used for exporting your own data, which is a bit more defensible, but still technically against their terms.

## 3. GEDCOM — Your Best Legal Escape Hatch

GEDCOM (Genealogical Data Communication) is the universal exchange format for genealogy data, and it's the most practical way to work with Ancestry data programmatically.

**What you can do:**

- Export your full tree from Ancestry as a GEDCOM file (Ancestry supports this natively)
- Import modified GEDCOM files back into Ancestry
- Process, analyze, clean, and enrich the data locally between export/import cycles

**Current standards:**

- **GEDCOM 5.5.1** — Most widely supported, what Ancestry exports
- **GEDCOM 7.0** (released 2021) — Modern standard with better Unicode, multimedia handling, and extensibility. Adoption is growing but not universal yet
- **GEDCOM X** — Not a file format but a REST API specification developed by FamilySearch for machine-to-machine data transfer

**GEDCOM parsing libraries:**

- Python: `python-gedcom`, `ged4py`, `gedcompy`
- JavaScript: `gedcom.js`, `parse-gedcom`
- These let you read, modify, validate, and write GEDCOM files programmatically

**The workflow:** Export from Ancestry → process/enrich locally → import back. It's manual at the export/import step, but everything in between can be fully automated.

## 4. Alternative Genealogy APIs — FamilySearch Is the Winner

### FamilySearch API (Best Option)

FamilySearch is the polar opposite of Ancestry on openness. They offer a free, well-documented, public API with:

- Official SDKs for Python, JavaScript, Java, C#
- Endpoints for: person records, pedigree traversal, search, places, historical records, memories/photos
- OAuth2 authentication
- No commercial restrictions
- Developer portal: developers.familysearch.org

FamilySearch's database is collaborative (one shared tree), so it complements Ancestry's private-tree model nicely. Many serious genealogists use both — Ancestry for its record collections and DNA, FamilySearch for its open API and collaborative tree.

### MyHeritage Family Graph API

- Free API with application key
- JSON REST, initially read-only
- Good for cross-referencing data
- familygraph.com

### Findmypast

- Has a documented API on GitHub with minimal docs
- Used by RootsMagic for record matching
- Less mature than FamilySearch's offering

## 5. Browser Extensions & Desktop Integrations

### Browser Extensions

- **Genealogy Assistant** — The most feature-rich option. 100+ features across Ancestry, FamilySearch, MyHeritage. Includes CSV export of trees, batch DNA match selection, advanced image tools. $2.95/mo or $34.95 one-time. Chrome and Firefox.
- **ORA (Online Research Assistant)** — Windows program + browser extension combo. Automates data extraction across Ancestry, FamilySearch, and others.

### Desktop Software (Official Integrations)

These are the only tools with sanctioned Ancestry API access:

- **RootsMagic** — TreeShare feature for direct two-way sync with Ancestry trees. Paid software, but the integration is solid and officially supported.
- **Family Tree Maker** — Direct sync with Ancestry (they're owned by the same parent company). Most seamless integration available.

Both of these bypass GEDCOM for cleaner real-time syncing. If you want the closest thing to API access, RootsMagic's TreeShare is probably it.

## 6. MCP Servers & AI-Assisted Genealogy

### Existing MCP Servers

- **GEDCOM Genealogy MCP** — Processes local GEDCOM files, runs entirely offline. Lets you query your tree data through natural language.
- **Gramps Web MCP** — 24 specialized tools for family tree exploration including full CRUD operations, timeline generation, and relationship analysis. Connects to Gramps (popular open-source genealogy software).
- **Ancestry MCP** — Direct GEDCOM file interaction: read, parse, search, rename operations.
- **Autoresearch Genealogy** — Structured prompts and templates for AI-assisted genealogy research, built for Claude Code.

### What You Could Build

A custom MCP server could realistically automate the tedious parts of your workflow:

- **Record cross-referencing:** Export GEDCOM from Ancestry → use FamilySearch API to search for matching records → present candidates for review
- **Source validation:** Parse your tree's sources, flag incomplete citations, suggest what's missing
- **Branch building assistance:** Given a person, automatically search FamilySearch + other open APIs for potential relatives, census records, vital records
- **Data quality checks:** Find inconsistencies (impossible dates, duplicate entries, missing sources)
- **Timeline generation:** Build chronological narratives from scattered records
- **DNA match analysis:** Export DNA match data and cross-reference with tree data to suggest common ancestors

The practical architecture would be: Ancestry (via GEDCOM export) + FamilySearch API (for record search) + local GEDCOM processing (via MCP) + AI for analysis and suggestions. You'd still do the actual Ancestry work in their UI, but the research, cross-referencing, and data prep would be heavily automated.

## Recommended Strategy

1. **Get RootsMagic** if you don't have it — TreeShare gives you the best programmatic bridge to Ancestry without violating ToS
2. **Register for FamilySearch API access** — it's free and gives you the record search capability Ancestry won't
3. **Set up a GEDCOM-based workflow:** periodic exports from Ancestry, process locally, import back
4. **Try the existing GEDCOM MCP server** to see if AI-assisted tree analysis fits your workflow
5. **Consider building a custom MCP** that combines FamilySearch API search + local GEDCOM analysis — this is where the real tedium-reduction lives

The genealogy automation space is still early but growing fast, especially with MCP making it easy to wire AI into these workflows.

---

## Connection to Existing Projects

- **CCA-F Week 4** already flagged a FamilySearch MCP server as a potential hands-on project (the 3-legged OAuth flow adds real-world auth complexity the course skips)
- Could serve double duty: CCA-F learning project + practical ancestry tool

## Next Steps

- [ ] Deep dive on FamilySearch API documentation and capabilities
- [ ] Evaluate existing GEDCOM MCP server and Gramps Web MCP
- [ ] Decide whether to build FamilySearch MCP as the CCA-F Week 4 project
- [ ] Test GEDCOM export from Ancestry and explore Python processing options
- [ ] Investigate what specific tedious tasks to prioritize automating
- [ ] Look into RootsMagic and the Genealogy Assistant browser extension
