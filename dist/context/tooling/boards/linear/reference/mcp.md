# Linear — MCP reference

**Source docs:** [linear.app/docs/mcp](https://linear.app/docs/mcp) — start here. The install command and config snippets below are summaries; if Linear changes either, the docs page is authoritative.

Read-write semantics required. The agent drafts changes under `proposals/` first; only after human approval does it use Linear's mutation API to land them.

## Install — Claude Code

Run once at the repo root:

```bash
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

This adds a `linear-server` entry to the local `.mcp.json` (or `.claude/settings.json`, depending on scope). Restart Claude Code so the new server is picked up; Linear's OAuth flow runs on first call.

## Install — Copilot

Copilot reads MCP servers from `.vscode/mcp.json`. Add the Linear server entry per [the Linear MCP docs](https://linear.app/docs/mcp); the shape is roughly:

```json
{
  "servers": {
    "linear-server": {
      "type": "http",
      "url": "https://mcp.linear.app/mcp"
    }
  }
}
```

The exact field names (`type`/`transport`, `url`/`endpoint`) and any auth fields can drift — confirm against the Linear docs page when running the wizard.

## Verify

1. `mcp__linear-server__list_issues` to verify read access.
2. A no-op write on a scratch issue (set the description to its current value) to verify write access.
3. Record the verification status (`read-ok`, `write-ok`, `pending`) in `context/tooling/board.md`.

## Branch naming

Linear auto-generates branch names from issue identifiers. The convention:

`{user}/{TEAM}-{number}-{slug}` — e.g. `alex/proj-315-add-tax-columns-to-export`

Use the Linear-generated name; do not invent your own.

## Latency

Linear is fast. The blog (§7) flags latency as more important than rate limits for agent UX; Linear is one of the reasons the agentic way of working feels qualitatively different from slower board tools.
