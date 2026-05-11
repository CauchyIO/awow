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

Atlassian's official MCP server: see `https://www.atlassian.com/blog/announcements/atlassian-mcp-platform` (or the Atlassian developer portal for the latest).

## TODO

- Label taxonomy specifics
- Branch naming with smart commits
- Reference team
- v0.2 fills in the rest
