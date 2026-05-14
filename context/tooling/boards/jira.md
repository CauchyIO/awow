# Jira — reference for the agentic way of working

> **v0.1 status:** stub. Full reference lands in v0.2.

Jira is the most-used board in enterprise. The mapping below is the v0.1 starting point; the full reference will be customised based on real engagement data.

## When `/setup-awow` infers Jira

Board URL hostname matches `*.atlassian.net`.

## Hierarchy

Jira's hierarchy depends on the team's configuration:

| Concept | Jira primitive |
|---|---|
| L1 — Strategic goal | Epic (or Initiative if using Advanced Roadmaps) |
| L2 — Capability | Epic (if not used as L1) or Story (large) |
| L3 — Deliverable | Story or Task |
| L4 — Action | Sub-task |

Jira's "Story" is overloaded — clarify with the team which level it represents before mapping.

## States

Jira's default workflow is heavily customised per-project. The wizard reads the project's actual workflow during Step 0.

## MCP

**Source docs:** Atlassian's MCP platform announcement at `https://www.atlassian.com/blog/announcements/atlassian-mcp-platform` (or the Atlassian developer portal for the current, authoritative install instructions). Confirm the install commands below against Atlassian's docs at setup time — Atlassian's MCP offering has been moving quickly.

Read-write semantics required.

### Install — Claude Code

TODO (v0.2) — confirmed install command. Likely shape (verify against Atlassian docs before running):

```bash
claude mcp add --transport http jira-server <atlassian-mcp-url>
```

### Install — Copilot

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

### Verify

1. List issues from a known project to verify read access.
2. A no-op write on a scratch issue (set the description to its current value) to verify write access.
3. Record the verification status in `context/tooling/board.md`.

## TODO

- Label taxonomy specifics
- Branch naming with smart commits
- Reference team
- v0.2 fills in the rest
