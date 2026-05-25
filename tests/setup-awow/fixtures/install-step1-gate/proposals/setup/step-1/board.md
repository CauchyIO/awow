# Board tooling — Cauchy / awow (GitHub Projects via `gh` CLI)

The board for awow's own backlog. Kept separate from Cauchy's client-engagement boards (which live in Linear under the `Cauchyio` Linear workspace) — awow is public and its planning lives next to its code.

## Tool family

GitHub Issues + Projects v2.

## Board URL

<https://github.com/orgs/CauchyIO/projects/3>

The repo-level project listing (<https://github.com/CauchyIO/awow/projects?query=is%3Aopen>) is the entry point for browsing; the canonical project is *Dogfood* (#3 on CauchyIO).

## Workspace / team identifier

- **Org:** `CauchyIO`
- **Repo:** `CauchyIO/awow` (public, Issues + Projects enabled)
- **Project:** `Dogfood` — project number `3`, id `PVT_kwDODcJdXM4BXrBg`, open, private. Short description: *"Scratch project for awow's own dogfood iterations. Issues here can be bulk-closed via /awow-reset. See dogfood/README.md."*

## Read/write surface — `gh` CLI (no MCP for now)

For dogfood we deliberately **skip the GitHub MCP server** and use the `gh` CLI as the agent's read/write surface. Reasons:

- The official `github/github-mcp-server` requires a Personal Access Token to run locally; the remote variant lives behind a Copilot-licensed endpoint. PAT friction is real and worth avoiding for both this run and any adopter who'd rather not manage another token.
- `gh` is already authenticated for the contributor running this session (`hetspookjee` account; scopes `gist, project, read:org, repo, workflow`).
- The wizard's Step 1 contract is *"the agent can read and write the board"*, not "an MCP must exist". `gh` CLI satisfies the contract; the `context/tooling/boards/github-issues/reference/mcp.md` reference documents this pattern as Option 2 for adopters who want lighter-weight setup (added via CAU-908).

If a future iteration needs MCP-only capabilities (richer queries, push notifications, etc.) install per the [github/github-mcp-server README](https://github.com/github/github-mcp-server) and add an MCP section above this one.

## Verification status

- **MCP installation:** `not-installed` — by design, see above.
- **Read (via `gh` CLI):** `ok` — `gh auth status` shows scopes `gist, project, read:org, repo, workflow`; `gh repo view CauchyIO/awow`, `gh project list --owner CauchyIO --format json`, and `gh project view 3 --owner CauchyIO` all work.
- **Write:** `ok` — `gh project edit 3 --owner CauchyIO --description …` successfully set the Dogfood project's short description on 2026-05-14.

## Open items (housekeeping; do not block Step 1)

1. *(Optional housekeeping)* Close or delete the two abandoned `@hetspookjee's untitled project` entries (CauchyIO projects #1 and #2). They are already `closed: true` but remain visible in the org's projects listing. Deletion (`gh project delete`) requires explicit user authorisation.
2. *(Done as part of CAU-908)* The new `context/tooling/boards/github-issues/reference/mcp.md` documents `gh` CLI as Option 2 alongside the MCP. The `dogfood`-label inflation-control pattern still wants documenting alongside it; follow-up.

## Inflation control — `dogfood` label discipline

Repeated dogfood walkthroughs (running `/refinement-prep`, `/process-workitem`, etc. against this repo) will create issues. To keep the board interpretable across iterations:

- Every issue created during a dogfood iteration carries a `dogfood` label.
- Bulk-close at the start of a new iteration: `gh issue list -R CauchyIO/awow -l dogfood --state open --json number -q '.[].number' | xargs -I{} gh issue close -R CauchyIO/awow {}`.
- The `dogfood` label is added to `context/team/conventions/REQUIRED/labels.md` when Step 3 runs against this dogfood workspace.

If iteration volume grows, escalate to dated scratch projects (`Dogfood — 2026-05`, `Dogfood — 2026-06`) and archive old ones — but the label-based approach is the day-one default.

## Harness scope

- **Claude Code:** the harness running `/setup-awow`. `gh` is shelled out from `Bash`.
- **GitHub Copilot:** not wired. If awow contributors start using Copilot on this repo, the same `gh` CLI surface works there too — no harness-specific install needed.

## Why not Linear for this repo

Cauchy uses Linear (`Cauchyio` workspace) for client engagements (e.g. Boskalis). awow itself is open source on `CauchyIO/awow`; mixing its prompt-iteration backlog into Linear would (a) hide it from external contributors, and (b) contaminate Cauchy's internal cycle-time metrics with the maintainer's own tinkering. Keeping awow's plan on GitHub also makes the "use awow with a different board than your main team uses" pattern legible to adopters.
