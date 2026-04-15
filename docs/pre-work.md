# Pre-Work Checklist

Tasks that can be done before CCA-F Week 4 (MCP Fundamentals). None of these require MCP knowledge.

## Before Writing Any Code

- [ ] **Export GEDCOM from Ancestry** — Go to your tree on Ancestry.com → Settings → Export Tree. Save the `.ged` file locally. This gives you real data to test against.
- [ ] **Register for FamilySearch developer account** — https://developers.familysearch.org — API key approval can take time, so start early.
- [ ] **Initialize git repo** — `git init`, `.gitignore`, first commit with project structure.
- [ ] **Evaluate existing GEDCOM MCP servers** — Install and test the GEDCOM Genealogy MCP and/or Gramps Web MCP. See what's already built before building your own.

## After Getting GEDCOM Export

- [ ] **Explore the data** — Use `python-gedcom` or `ged4py` to parse your GEDCOM file. See what the data structure looks like. How many people? How many sources? What's the quality like?
- [ ] **Identify the tedious parts** — What specific research tasks are you and your mom spending the most time on? Those are the automation targets.
- [ ] **Document edge cases** — GEDCOM is a messy format. Note anything surprising in your export that the tools will need to handle.

## Waits for Week 4

- [ ] MCP server scaffold
- [ ] Tool definitions and transport layer
- [ ] FamilySearch API integration
- [ ] Wiring into Claude Code
