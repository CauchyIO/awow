# Jira — state machine reference (skeleton)

Jira's workflow is per-project-customisable; there is no single default that fits every team. The wizard treats Mode B (assess and capture current) as the **expected path** for Jira, because most teams have customised their workflow long before they adopt the operating model.

## Mapping (Scrum / Software default)

| Five-state contract | Jira state | Notes |
|---|---|---|
| Backlog / Todo | `To Do` (or `Backlog` + `Selected for Development` if two-stage refinement) | |
| In Progress | `In Progress` | Agent moves on commit. |
| In Review | `In Review` (custom — many projects use `Code Review` or `In Test`) | Agent moves on PR open. |
| Blocked | `Blocked` state **or** `status:blocked` label | Pick one team-wide. |
| Done | `Done` | Terminal. |

## Wizard responsibilities

**Mode A (from reference).** Rare for Jira — most teams arrive pre-configured. If genuinely greenfield, emit a manual checklist for **Project Settings → Workflows** and document the chosen workflow.

**Mode B (assess current).** Use the MCP to list workflow statuses for the project. Map each to the five-state contract. Surface unmappable states ("Cancelled", "Won't Do", "Pending QA") and ask the user how to slot them.

## What lands in `board.md`

```
## State machine

Jira workflow scheme: <Scrum default | Kanban default | custom name>.

| Five-state contract | Jira status | Owner |
|---|---|---|
| Backlog / Todo | <…> | Human |
| In Progress | <…> | Agent (on commit) |
| In Review | <…> | Agent (on PR open) |
| Blocked | <state OR label> | Agent flags |
| Done | <…> | Agent (on merge) |

Divergence from reference: <none | list>.
```
