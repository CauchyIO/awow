# Linear — state machine reference

The agentic way of working uses a five-state contract (per `input/PROPOSAL.md` §4). Linear's default workflow states map cleanly onto it; the only judgement call is whether to model **Blocked** as a workflow state or as a `status:blocked` label.

## Mapping

| Five-state contract | Linear state name | Who moves it |
|---|---|---|
| Backlog / Todo | `Backlog` and `Todo` | Refined into Todo by a person; agent re-orders within Todo. |
| In Progress | `In Progress` | Agent moves on commit, branch creation, or explicit pick-up. |
| In Review | `In Review` | Agent moves on PR open or reviewer request. |
| Blocked | `Blocked` workflow state **or** `status:blocked` label | Agent flags; person confirms. Pick one team-wide. |
| Done | `Done` | Agent moves on merge. |

Linear also ships `Cancelled` (terminal, non-success). Treat it as a sibling of `Done`: the agent moves nothing into `Cancelled` autonomously; humans do.

## Transition ownership

The agent owns the mechanical transitions; humans own the judgement calls.

| Transition | Owner | Trigger |
|---|---|---|
| `Backlog` → `Todo` | Human | Refinement: scoped, prioritised, unblocked. |
| `Todo` → `In Progress` | Agent | First commit on the issue's branch, or explicit pick-up. |
| `In Progress` → `In Review` | Agent | PR opened with `Closes #<issue>` or `Fixes #<issue>`. |
| `In Review` → `Done` | Agent | PR merged. |
| any → `Blocked` | Agent flags; human confirms | External dependency surfaced; the agent comments why. |
| `Blocked` → previous | Human | Dependency resolved. The agent re-picks up only after the human flips the state back. |
| any → `Cancelled` | Human | Scope dropped or duplicate. |

## Wizard responsibilities (Mode A vs. Mode B)

**Mode A (from reference).** Surface the table above. Ask the user:

1. Does your team want **Blocked** as a workflow state or a label? Both work; the convention is one team-wide choice.
2. Do you want the agent to own `In Progress` → `In Review` automatically on PR open?

Where the Linear plan exposes workflow customisation (Standard plan or above), apply the choices via the MCP. On Free / Starter where workflow states are not API-editable, surface a manual checklist for the user to run in **Settings → Workflows** and re-verify after they confirm.

**Mode B (assess current).** Use the MCP to list workflow states for the team (`mcp__linear-server__list_issue_statuses`). Compare against the table above. Surface any divergence (extra states like `In Triage`, missing `In Review`, etc.) and ask the user to (a) accept and record, (b) close the gap, or (c) override the reference. Resolved decisions land in `## State machine` of `context/tooling/board.md`.

## What lands in `board.md`

```
## State machine

| Five-state contract | Linear state | Owner of transition |
|---|---|---|
| Backlog / Todo | Backlog, Todo | Human refines into Todo |
| In Progress | In Progress | Agent (on first commit) |
| In Review | In Review | Agent (on PR open) |
| Blocked | <state OR `status:blocked` label> | Agent flags, human confirms |
| Done | Done | Agent (on merge) |

Blocked is modelled as: <state | label>.
Divergence from reference: <none | list>.
```
