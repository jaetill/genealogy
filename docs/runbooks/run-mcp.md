# Run the genealogy MCP server

The genealogy MCP server runs locally via stdio transport, exposing 13 tools for Claude-assisted research.

## Install

```sh
uv sync
```

## Launch (CLI)

```sh
uv run genealogy-mcp
```

## Wire into Claude Code

Add to your `.claude/mcp.json` (project-local) or `~/.claude/mcp.json` (user-level):

```json
{
  "mcpServers": {
    "genealogy": {
      "command": "uv",
      "args": ["run", "--directory", "/abs/path/to/genealogy", "genealogy-mcp"]
    }
  }
}
```

## Verify

In a Claude Code session:

```
/mcp
# should list `genealogy` with 13 tools available
```

`scripts/verify_real_data.py` is a smoke script that exercises the WikiTree + LoC clients against real data without going through the MCP transport.
## Optional: Sentry crash reporting

The genealogy package includes optional Sentry wiring (see `src/genealogy/observability.py`). When the MCP server entry point is built, it can call `init_sentry()` to enable crash reporting:

```python
from genealogy.observability import init_sentry

init_sentry()  # No-op unless GENEALOGY_SENTRY_DSN is set
```

To enable, export the DSN before launching:

```sh
export GENEALOGY_SENTRY_DSN='https://...@sentry.io/...'
```

Sentry is **off by default** (no DSN set) and never sends PII (send_default_pii=False).