# 0001 — Use `gh` CLI as the GitHub board read/write surface, not the GitHub MCP

**Date:** 2026-05-14
**Status:** Accepted

## Context

Setting up the agent's read/write surface for awow's own backlog on `CauchyIO/awow` (GitHub Projects, project `Dogfood` #3). Three candidates:

1. Install `github/github-mcp-server` locally — requires a Personal Access Token managed by every contributor.
2. Use the remote `https://api.githubcopilot.com/mcp/` endpoint — gated behind a GitHub Copilot subscription.
3. Use `gh` CLI, which is already authenticated for the maintainer and is a stable, well-known surface.

The wizard's Step 1 contract phrases the requirement as "a wired-up board MCP" but reads, on inspection, as *"the agent can read and write the board"*. The MCP is an instance, not the contract.

## Decision

Skip the GitHub MCP. Use `gh` CLI in `Bash` as the read/write surface for awow's own backlog. Capture this in `dogfood/context/tooling/board.md` so the choice is legible to future agents.

## Consequences

- Avoids PAT friction (and the implication that adopters need to manage tokens just to use awow).
- `gh` works for both Claude Code and GitHub Copilot harnesses without configuration drift.
- Loses any MCP-specific affordances (richer queries, push notifications). None are needed today; revisit if/when they become load-bearing.
- The wizard's `context/tooling/boards/github-issues/reference/mcp.md` reference documents `gh` CLI as a supported alternative to the MCP (Option 2). Awow adopters who don't want PAT friction now have a legitimate path.
