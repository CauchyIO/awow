# Jira — required fields reference (skeleton)

| Field | Load-bearing? | Notes |
|---|---|---|
| Priority | Yes | Highest / High / Medium / Low / Lowest — map per Linear's convention. |
| Story Points | Optional | Common in Scrum teams; agent reads but does not set. |
| Sprint | Yes if running Scrum | Agent reads to scope "what's in flight". |
| Components | Yes | See `labels.md`. |
| Assignee | Yes | Agent only acts on unassigned or self-assigned. |

## Wizard responsibilities

**Mode A.** Confirm Priority enabled. Confirm Sprint vs. Kanban-flow.

**Mode B.** Sample 10 recent issues; check Priority and Sprint fill rate.

## What lands in `board.md`

```
## Required fields

- Priority: <levels in use>.
- Story Points: <scale, or "not used">.
- Sprint: <2-week | 1-week | flow-only>.
- Components: <list>.
- Assignee: agent only acts on unassigned or self-assigned.

Divergence from reference: <none | list>.
```
