# GitHub Issues — required fields reference (skeleton)

GitHub Issues itself has very few native fields (assignee, labels, milestone). Projects v2 adds **custom fields** — that is where Priority, Iteration, Estimate live.

| Field | Surface | Notes |
|---|---|---|
| Status | Projects v2 | See `states.md`. |
| Priority | Projects v2 custom field (single-select) | Recommended options: Urgent / High / Medium / Low. |
| Iteration | Projects v2 native field | Optional; for teams running cycles. |
| Estimate | Projects v2 custom field (number) | Optional. |
| Assignee | Issue native | Agent only acts on unassigned or self-assigned. |
| Milestone | Issue native | Used for date-bound chunks; optional. |

## Wizard responsibilities

**Mode A.** Create the Priority custom field on the Project board via `gh project field-create` or the MCP. Iteration is opt-in.

**Mode B.** Read the Project's custom fields; check fill rate.

## What lands in `board.md`

```
## Required fields

- Status: Projects v2 Status field with five options.
- Priority: <Projects v2 custom field, options listed>.
- Iteration: <in use | not used>.
- Estimate: <in use | not used>.
- Assignee: agent only acts on unassigned or self-assigned.
- Milestone: <"for date-bound chunks" | not used>.

Divergence from reference: <none | list>.
```
