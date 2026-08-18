# GitHub Issues + Projects — reference index

> **v0.1 status:** skeleton. Reference shape matches Linear's; depth lands in v0.2.

GitHub Issues + Projects v2 is the lightest of the supported boards. Best for open-source projects and small teams where the code is the centre of gravity.

## When `/setup-awow` infers GitHub Issues

Board URL is:
- `github.com/<org>/<repo>/issues`
- `github.com/orgs/<org>/projects/<n>`
- `github.com/users/<user>/projects/<n>`

## Reference files

| File | Covers |
|---|---|
| [`reference/states.md`](reference/states.md) | Five-state contract → Projects v2 Status field. |
| [`reference/hierarchy.md`](reference/hierarchy.md) | Milestone / tracking-issue / Issue / task-list. |
| [`reference/labels.md`](reference/labels.md) | GitHub labels with the `type:*` / `area:*` / `status:*` scheme. |
| [`reference/fields.md`](reference/fields.md) | Status, Priority, Iteration, Estimate (Projects v2 custom fields). |
| [`reference/team-page.md`](reference/team-page.md) | Repo README, Org profile, Project description. |
| [`reference/mcp.md`](reference/mcp.md) | GitHub MCP install **and** the `gh` CLI alternative for adopters who want to skip PAT-managed MCPs. |

## When to use the `gh` CLI instead of the MCP

The official `github/github-mcp-server` requires a Personal Access Token to run locally; the remote variant lives behind a Copilot-licensed endpoint. PAT friction is real. Adopters who already have `gh` authenticated can use it as the agent's read/write surface — the Step 1 contract is *"the agent can read and write the board"*, not "an MCP must exist". See `reference/mcp.md` for the `gh` CLI configuration.
