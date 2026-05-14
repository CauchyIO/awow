# Linear — reference for the agentic way of working

Linear is the recommended board tool for this operating model. Fast, opinionated, API-first.

## When `/setup-awow` infers Linear

Board URL hostname is `linear.app`. Example:
- `https://linear.app/<org>/team/<TEAM>/...`
- `https://linear.app/<org>/issue/<TEAM>-<num>`

## Hierarchy

Linear is flat by design. The hierarchy from `input/research/synthesis.md` and the work-item sizing reference is realised through:

| Concept | Linear primitive |
|---|---|
| L1 — Strategic goal | Initiative |
| L2 — Capability | Project |
| L3 — Deliverable (agent-pickable story) | Issue |
| L4 — Action | Sub-issue |

Linear's `Sub-issue` is more flexible than ADO's `Task` — sub-issues can be promoted to standalone issues if scope grows.

## States — the five-state contract

Recommended state machine (per `input/PROPOSAL.md` anchor §4):

| Linear state name | What it means | Who moves it |
|---|---|---|
| Backlog / Todo | Ready to be picked up. Unblocked, scoped, prioritised. | Refined into Todo by a person; agent re-orders. |
| In Progress | Actively being worked on. | Agent moves on commit, branch creation, or explicit pick-up. |
| In Review | Waiting for a human review. | Agent moves on PR open or reviewer requested. |
| Blocked (or `status:blocked` label) | Waiting for an external dependency. | Agent flags; person confirms. |
| Done | Merged or otherwise completed. | Agent moves on merge. |

Linear's default states map cleanly: Backlog/Todo, In Progress, In Review, Done, Cancelled. The `Blocked` state can be a workflow state or a `status:blocked` label — the convention is one team-wide choice.

## MCP

**Source docs:** [linear.app/docs/mcp](https://linear.app/docs/mcp) — start here. The install command and config snippets below are summaries; if Linear changes either, the docs page is authoritative.

Read-write semantics required. The agent drafts changes under `proposals/` first; only after human approval does it use Linear's mutation API to land them.

### Install — Claude Code

Run once at the repo root:

```bash
claude mcp add --transport http linear-server https://mcp.linear.app/mcp
```

This adds a `linear-server` entry to the local `.mcp.json` (or `.claude/settings.json`, depending on scope). Restart Claude Code so the new server is picked up; Linear's OAuth flow runs on first call.

### Install — Copilot

Copilot reads MCP servers from `.vscode/mcp.json`. Add the Linear server entry per [the Linear MCP docs](https://linear.app/docs/mcp); the shape is roughly:

```json
{
  "servers": {
    "linear-server": {
      "type": "http",
      "url": "https://mcp.linear.app/mcp"
    }
  }
}
```

The exact field names (`type`/`transport`, `url`/`endpoint`) and any auth fields can drift — confirm against the Linear docs page when running the wizard.

### Verify

1. `mcp__linear-server__list_issues` to verify read access.
2. A no-op write on a scratch issue (set the description to its current value) to verify write access.
3. Record the verification status (`read-ok`, `write-ok`, `pending`) in `context/tooling/board.md`.

## Label taxonomy

Per `context/team/conventions/REQUIRED/labels.md`:

| Prefix | Examples |
|---|---|
| `type:` | `type:feature`, `type:bug`, `type:task`, `type:documentation` |
| `area:` | `area:infrastructure`, `area:frontend`, `area:api`, `area:data` |
| `status:` | `status:blocked`, `status:needs-review`, `status:waiting` |

Linear's workspace labels span teams; team labels are scoped. Use workspace labels only for cross-team concerns.

## Branch naming

Linear auto-generates branch names from issue identifiers. The convention:

`{user}/{TEAM}-{number}-{slug}` — e.g. `alex/proj-315-add-tax-columns-to-export`

Use the Linear-generated name; do not invent your own.

## Cycle time

Linear surfaces cycle-time stats in the Insights tab. The blog (§4 of `input/PROPOSAL.md`'s anchor) recommends measuring your own 85th-percentile cycle time and treating that as your Service Level Expectation, rather than importing external thresholds.

## Latency

Linear is fast. The blog (§7) flags latency as more important than rate limits for agent UX; Linear is one of the reasons the agentic way of working feels qualitatively different from slower board tools.

## Tips for adopting teams

- Linear auto-generates branch names from the issue identifier — use them as-is.
- Workspace labels span teams; team labels are scoped. Use workspace labels only for genuinely cross-team concerns.
- Linear's Insights tab gives you cycle-time stats out of the box. Measure your own 85th-percentile and treat that as your team Service Level Expectation rather than importing external thresholds.
- Linear is fast, which makes the agentic loop feel different from slower boards. If you are choosing between candidates and latency matters, factor that in.
