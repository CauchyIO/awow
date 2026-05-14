# Azure DevOps — iterations reference

ADO's Iterations are the team's sprint rhythm.

## Convention

| Decision | Recommended | Notes |
|---|---|---|
| Length | 2 weeks | 1-week iterations work for high-cadence teams. |
| Iteration Path naming | `<root>/<team>/<YYYY>/Sprint <N>` | Predictable; sortable. |
| Default iteration | Current sprint | Agent reads this to scope `/sprint-review-prep`. |

## Cycle / lead time

ADO surfaces Cycle Time and Lead Time in **Analytics Views**. Same advice as Linear: measure your own 85th-percentile cycle time, treat as the team SLE rather than importing external benchmarks.

## Wizard responsibilities

**Mode A (from reference).** Confirm iteration length, naming, and current iteration. Iterations are typically configured outside the MCP scope; emit a manual checklist for **Project Settings → Iterations**.

**Mode B (assess current).** Read existing iterations via the MCP. Surface the cadence and any gaps (missing iterations for upcoming weeks).

## What lands in `board.md`

```
## Iterations

Length: <1-week | 2-week>.
Iteration Path naming: <pattern>.
Current iteration: <name>.
Cycle-time 85th-percentile (SLE): <e.g. 9 days | not yet measured>.

Divergence from reference: <none | list>.
```
