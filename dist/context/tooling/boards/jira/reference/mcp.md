# Jira — MCP reference

**Source docs:** Atlassian's MCP platform announcement at [atlassian.com/blog/announcements/atlassian-mcp-platform](https://www.atlassian.com/blog/announcements/atlassian-mcp-platform) (or the Atlassian developer portal for the current, authoritative install instructions). Confirm against Atlassian's docs at setup time — Atlassian's MCP offering has been moving quickly.

Read-write semantics required.

## Install — Claude Code

TODO (v0.2) — confirmed install command. Likely shape (verify against Atlassian docs before running):

```bash
claude mcp add --transport http jira-server <atlassian-mcp-url>
```

## Install — Copilot

TODO (v0.2) — confirmed `.vscode/mcp.json` snippet. Likely shape:

```json
{
  "servers": {
    "jira-server": {
      "type": "http",
      "url": "<atlassian-mcp-url>"
    }
  }
}
```

## Verify

1. List issues from a known project to verify read access.
2. A no-op write on a scratch issue (set the description to its current value) to verify write access.
3. Record the verification status in `context/tooling/board.md`.

## Branch naming

Jira supports smart commits (e.g. `PROJ-1042 #time 30m #comment …`). Branch convention:

`{user}/{TEAM}-{number}-{slug}` — same as Linear.

## TODO (v0.2)

- Confirmed Atlassian MCP install command and auth flow.
- Smart-commit conventions and how the agent uses them.
- Reference Jira team for examples.
