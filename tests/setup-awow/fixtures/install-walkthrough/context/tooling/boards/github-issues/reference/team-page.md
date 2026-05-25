# GitHub Issues — team page conventions reference (skeleton)

GitHub's "team page" surface is split across three places:

| Surface | What it should contain |
|---|---|
| Repo README | Mission, quickstart, links to docs. Read by every visitor first. |
| Org profile README (`.github` repo) | Team mission across repos; pinned repositories. |
| Project description (Projects v2) | One sentence; the customer change this board tracks. |

For single-repo teams, the repo README is enough. For teams owning multiple repos, an Org profile is the team-page surface.

## What a team profile should contain

Identical to Linear's reference:

1. **Mission** — one sentence.
2. **Members** — link to a `MAINTAINERS.md` or similar.
3. **On-call rotation** — if applicable; often skipped for OSS.
4. **Links** — to dashboards, runbooks, the operating-model repo.

## Wizard responsibilities

**Mode A.** Draft a README section from Steps 2–4 answers. Project description: write via `gh project edit --description` or the MCP.

**Mode B.** Read the existing README, org profile, and Project description.

## What lands in `board.md`

```
## Team page conventions

Repo README mission section: <populated | empty>.
Org profile README: <URL | not used>.
Project description: <populated | empty>.
Divergence from reference: <none | list>.
```
