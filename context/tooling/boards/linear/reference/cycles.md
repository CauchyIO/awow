# Linear — cycles reference

Linear's Cycles are the team's iteration rhythm — typically one or two weeks. They scope "what's in flight right now" and feed cycle-time analytics.

## Convention

| Decision | Recommended | Notes |
|---|---|---|
| Length | 1 or 2 weeks | Pick one; the agent reads but does not change. |
| Auto-add new Issues | Off | Forces explicit refinement before an Issue enters the current cycle. |
| Auto-roll incomplete Issues | On | Carry slipped work to the next cycle so cycle-time stats stay honest. |
| Cycle start day | Monday | Aligns with most working weeks; less load-bearing than the others. |

The agent reads the current cycle to scope `/sprint-review-prep` and to answer "what's in flight" questions. It does not create or close cycles autonomously.

## Cycle time

Linear surfaces cycle-time stats in the Insights tab. The blog (§4 of `input/PROPOSAL.md`'s anchor) recommends measuring your own **85th-percentile cycle time** and treating that as your team Service Level Expectation (SLE), rather than importing thresholds from external benchmarks.

## Wizard responsibilities

**Mode A (from reference).** Ask:

1. Does this team run cycles? Some Linear teams operate flow-style without cycles — that is fine; skip this section.
2. If yes: length, auto-add, auto-roll. Apply via Linear's MCP if the plan exposes cycle settings; otherwise emit a manual checklist for **Settings → Teams → `<team>` → Cycles**.

**Mode B (assess current).** Use the MCP (`mcp__linear-server__list_cycles`) to read existing cycle config. Surface it; ask the user whether to keep, change, or leave alone.

## What lands in `board.md`

```
## Cycles / iterations

Cycles: <in use, 1-week | in use, 2-week | not used>
Auto-add new issues: <on | off>
Auto-roll incomplete: <on | off>
Cycle-time 85th-percentile (SLE): <e.g. 6 days | not yet measured>

Divergence from reference: <none | list>.
```
