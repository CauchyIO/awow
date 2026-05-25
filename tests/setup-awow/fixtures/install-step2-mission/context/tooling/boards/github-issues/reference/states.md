# GitHub Issues — state machine reference (skeleton)

GitHub Issues itself has only Open / Closed. The five-state contract is realised through a **Projects v2 Status field** with custom options.

## Mapping

| Five-state contract | Projects v2 Status option | Notes |
|---|---|---|
| Backlog / Todo | `Backlog`, `Todo` | |
| In Progress | `In Progress` | Agent moves on commit. |
| In Review | `In Review` | Agent moves on PR open. |
| Blocked | `Blocked` status option **or** `status:blocked` label | Pick one team-wide. |
| Done | `Done` | Agent moves on merge. |

If the team is **not** using a Project board, fall back to labels-only: `status:in-progress`, `status:in-review`, `status:blocked`. Open issues map to backlog/in-progress states; closed issues map to Done. This is workable but loses the column view.

## Wizard responsibilities

**Mode A (from reference).** If a Project is in use, configure the Status field via the MCP (or `gh project field-create`). If no Project, propose creating one.

**Mode B (assess current).** List Projects on the org/repo; read the Status field's options. Map to the five-state contract.

## What lands in `board.md`

```
## State machine

Surface: <Projects v2 board | labels-only fallback>.

| Five-state contract | Status option / label | Owner |
|---|---|---|
| Backlog / Todo | <…> | Human |
| In Progress | <…> | Agent (on commit) |
| In Review | <…> | Agent (on PR open) |
| Blocked | <option OR label> | Agent flags |
| Done | <…> | Agent (on merge) |

Divergence from reference: <none | list>.
```
