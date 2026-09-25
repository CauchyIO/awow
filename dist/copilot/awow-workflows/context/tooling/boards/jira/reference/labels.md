# Jira — label + component taxonomy reference (skeleton)

Jira has two related primitives: **Labels** (flat, free-form) and **Components** (per-project, structured).

| Use | Recommended primitive |
|---|---|
| `type:*` | Issue Type (native) — usually redundant with the work-item-type schema. |
| `area:*` | Component (per-project, structured) **or** label with `area:` prefix if components are not configured. |
| `status:*` | Label with `status:` prefix. |

## Wizard responsibilities

**Mode A.** Recommend Components for area and labels for status. Create initial components via the MCP.

**Mode B.** List existing components and labels. Surface duplication (`area:api` label coexisting with an `api` component).

## What lands in `board.md`

```
## Labels and components

- Components in use: <list>
- Labels with `status:` prefix: <list>
- Other labels: <list — kept legacy or pruned?>

Divergence from reference: <none | list>.
```
