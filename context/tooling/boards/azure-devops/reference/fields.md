# Azure DevOps — required fields reference

ADO ships many native fields. The load-bearing ones for the operating model:

| Field | Load-bearing? | Why |
|---|---|---|
| Priority | Yes | Drives pick order. ADO uses 1 (highest) – 4 (lowest); map per Linear's convention (Urgent / High / Medium / Low). |
| Effort / Story Points | Optional | Used for cycle-time analysis. Set by humans, not the agent. |
| Iteration Path | Yes | Scopes "what is in this sprint". Agent reads but does not change autonomously. |
| Area Path | Yes | Board scoping; see `labels.md`. |
| Assigned To | Yes | Agent only acts on unassigned or self-assigned work items. |

## Wizard responsibilities

**Mode A (from reference).** Confirm Priority enabled (1–4 scale). Ask if estimates are used. Ask which Area Paths the team owns.

**Mode B (assess current).** Sample 10 recent work items. Check Priority fill rate, Iteration Path fill rate, missing Area Paths.

## What lands in `board.md`

```
## Required fields

- Priority: 1–4 (Urgent → Low).
- Effort: <scale, or "not used">.
- Iteration Path: <root>/<team>/<iteration>.
- Area Path: <root>/<team>/<area>.
- Assigned To: agent only acts on unassigned or self-assigned.

Divergence from reference: <none | list>.
```
