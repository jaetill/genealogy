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