# Azure DevOps — reference for the agentic way of working

Azure DevOps (ADO) is the heavy-enterprise option of the four supported boards. Best when the team is operating inside a larger organisation with established ADO practice.

## When `/setup-awow` infers Azure DevOps

Board URL hostname matches:
- `dev.azure.com/<org>/<project>/...`
- `<org>.visualstudio.com/...` (legacy)

## Hierarchy

ADO enforces a strict four-level hierarchy:

| Concept | ADO primitive |
|---|---|
| L1 — Strategic goal | Epic |
| L2 — Capability | Feature |
| L3 — Deliverable (agent-pickable story) | User Story / Product Backlog Item |
| L4 — Action | Task |

ADO is the most opinionated of the supported boards; the hierarchy is enforced by the schema.

## States — the five-state contract

ADO's default workflow has more states than the five-state contract from the blog. The recommended mapping:

| Blog state | ADO state(s) |
|---|---|
| Todo | New + Approved |
| In Progress | Active / Committed |
| In Review | Resolved (with appropriate `status:` tag) |
| Blocked | Active + `status:blocked` tag |
| Done | Closed |

The wizard reads the team's actual workflow during Step 0 and customises the mapping accordingly.

## MCP

**Source docs:** Microsoft's Azure DevOps MCP server at `https://github.com/microsoft/azure-devops-mcp` (or as included in the official Azure MCP bundle). The repo README has the current install steps and any required env vars (PAT, organisation, project).

Read-write semantics required. ADO has a per-organisation rate limit; `/process-workitem` and `/refinement-prep` batch their writes to stay under it.

### Install — Claude Code

TODO — confirmed install command. The Azure DevOps MCP is typically a local stdio server (not HTTP), so the shape is closer to:

```bash
claude mcp add azure-devops-server -- npx -y @azure/azure-devops-mcp
```

Confirm against the repo README before running. Auth is via a PAT passed through env vars; see the README.

### Install — Copilot

TODO — confirmed `.vscode/mcp.json` snippet. For a stdio-based MCP the shape is roughly:

```json
{
  "servers": {
    "azure-devops-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@azure/azure-devops-mcp"],
      "env": { "ADO_PAT": "${env:ADO_PAT}" }
    }
  }
}
```

Confirm field names and env-var binding against the Azure DevOps MCP repo README.

### Verify

1. List work items from a known project to verify read access.
2. A no-op write on a scratch work item (set a field to its current value) to verify write access.
3. Record the verification status in `context/tooling/board.md`.

## Label / tag taxonomy

ADO calls them tags. Per `context/team/conventions/REQUIRED/labels.md`:

| Prefix | Examples |
|---|---|
| `type:` | `type:feature`, `type:bug`, `type:task`, `type:documentation` |
| `area:` | `area:infrastructure`, `area:frontend`, `area:api`, `area:data` |
| `status:` | `status:blocked`, `status:needs-review`, `status:waiting` |

ADO has a native Priority field; do not duplicate priority via labels.

## Branch naming

ADO does not auto-generate branch names. Convention:

`issue/{TEAM}-{number}` — e.g. `issue/PROJ-1042`

Or per-user: `{user}/{TEAM}-{number}-{slug}`. Pick one team-wide.

## Cycle time

ADO surfaces cycle-time and lead-time in Analytics Views. Same advice as Linear: measure your own 85th-percentile, treat it as your SLE.

## Enterprise scale

For organisations running ADO at 2,000+ employees with SAFe / Solution Train overlay, the work-item hierarchy is typically extended with Portfolio Epics → Solutions → Capabilities → Features. The four-level mapping above still holds at the team altitude; the higher levels live in a programme-management surface that this repo does not directly model (per the iteration plan, programme-level work is a horizon item).

## Tips for adopting teams

- Use the native Priority field; do not duplicate priority into labels.
- Area Paths matter for board scoping — pick one team-wide convention and document it in `context/team/conventions/REQUIRED/labels.md`.
- ADO has a per-organisation API rate limit. The seed commands batch writes to stay under it; if you customise heavily, watch for `429` responses.
