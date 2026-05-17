# ADR-0001: Adopt the Agentic Dev Environment platform

- **Status:** Accepted
- **Date:** 2026-05-16
- **Deciders:** Jason Tilley
- **Tags:** platform, governance, AI-workflows, python

## Context and Problem Statement

`genealogy` is the first **Python** project to adopt the [Agentic Dev Environment](https://github.com/jaetill/agentic-dev-environment) platform. Sibling projects are JS/TS. This ADR records the decision to adopt the platform and the Python-specific deviations from the platform's default (JS-flavored) configurations.

## Decision Outcome

Adopt via the `ai-team` plugin subscription. Phases 1-3 adapted for Python; **Phase 4 lite** for now — defer the Node-centric agent workflows (claude-pr-review, claude-implementer) until they're properly adapted for `uv sync` / `pytest` instead of `npm ci`.

### Phase status

| Phase | Status |
|---|---|
| 1 - Documentation | In this PR |
| 2 - AI configuration (plugin subscription) | In this PR |
| 3 - Quality gates (Python: ruff + mypy + pre-commit + pytest-cov) | Follow-up PR |
| 4 - CI workflows (Python-adapted, minimal) | Follow-up PR |
| 5 - Observability | Not applicable (local MCP server; no production runtime) |
| 6 - IaC | Not applicable (no AWS infra) |
| 7 - User feedback | Not applicable (single-user research tool) |

## Deviations from platform defaults

### Language: Python (uv-managed)

- `pyproject.toml` (already exists) — not `package.json`
- `uv sync` — not `npm ci`
- `pytest` — not `vitest`
- `ruff` — replaces `eslint` + `prettier` for Python
- `mypy` — typechecking (Python equivalent of `tsc --noEmit`)
- `pre-commit` framework — Python's husky equivalent; uses `.pre-commit-config.yaml`

### CI: minimal Python-adapted set

The platform's existing agent workflows (claude-pr-review.yml, claude-implementer.yml) assume `npm ci` + Node tooling. They are NOT copied verbatim into genealogy. Phase 4 adds:

- `ci.yml` — Python lint (ruff) + typecheck (mypy) + test (pytest with coverage)
- `security-scan.yml` — gitleaks (works for any repo); `pip-audit` (Python equivalent of `npm audit`)
- (deferred) — adapted versions of `claude-pr-review.yml` etc.

When the workspace publishes Python-adapted reusable workflows or composite actions, genealogy will switch to those.

### No release-please

Genealogy is a local-only research tool, not a published package. No release-please configuration. Versioning lives in `pyproject.toml`.

## Consequences

### Positive

- Plugin subagents available immediately in Claude Code sessions
- Standards inheritance from the workspace
- First Python consumer of the platform; informs future Python projects' adoption

### Negative

- Phase 4 is lighter than for JS projects — no PR-time agent review yet
- Until Python-adapted workflows are added to the workspace, genealogy is "in the team" but missing the autonomous PR-review loop

### Neutral

- Plugin source `jaetill/agentic-dev-environment` is public; no auth needed.

## Links

- [Workspace ADR-0015](https://github.com/jaetill/agentic-dev-environment/blob/main/docs/adr/0015-platform-as-plugin.md)
- [Workspace ADR-0016](https://github.com/jaetill/agentic-dev-environment/blob/main/docs/adr/0016-finding-lifecycle-calibration-deferral.md)
- Sibling project adoptions: game-night-pwa, meal-planner, ai-teacher, jaetill-portal, splendor, draft, carto (all adopted 2026-05-16)