# GitHub Issues — reference for the agentic way of working

> **v0.1 status:** stub. Full reference lands in v0.2.

GitHub Issues is the lightest of the supported boards. Best for open-source projects and small teams where the code is the centre of gravity.

## When `/setup-awow` infers GitHub Issues

Board URL is `github.com/<org>/<repo>/issues` or `github.com/<org>/projects/<n>`.

## Hierarchy

GitHub Issues + Projects provides a lightweight hierarchy:

| Concept | GitHub primitive |
|---|---|
| L1 — Strategic goal | GitHub Milestone or Project board |
| L2 — Capability | Tracking issue with task-list |
| L3 — Deliverable | Issue |
| L4 — Action | Task in a task-list (checkbox in an issue body) |

Less enforced than ADO; discipline comes from conventions, not tool constraints.

## States

GitHub Issues has Open / Closed. Projects v2 adds custom status fields. The five-state contract is realised through Project status columns.

## MCP

**Source docs:** The official GitHub MCP server at `https://github.com/github/github-mcp-server`. Repo README has the current install steps; uses GitHub's REST and GraphQL APIs.

Read-write semantics required.

### Install — Claude Code

TODO — confirmed install command. GitHub's MCP can run as a remote HTTP server or locally:

```bash
claude mcp add --transport http github-server https://api.githubcopilot.com/mcp/
```

Auth uses a GitHub PAT (or OAuth via the remote server). Confirm against the repo README before running.

### Install — Copilot

TODO — confirmed `.vscode/mcp.json` snippet. Likely shape:

```json
{
  "servers": {
    "github-server": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

Confirm against the github-mcp-server repo README.

### Verify

1. List issues from a known repo to verify read access.
2. A no-op write on a scratch issue (set a label that's already set) to verify write access.
3. Record the verification status in `context/tooling/board.md`.

## TODO

- Label taxonomy specifics
- Branch naming
- Reference team
- v0.2 fills in the rest
