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

The official GitHub MCP server: `https://github.com/github/github-mcp-server`. Read-write semantics; uses GitHub's REST and GraphQL APIs.

## TODO

- Label taxonomy specifics
- Branch naming
- Reference team
- v0.2 fills in the rest
