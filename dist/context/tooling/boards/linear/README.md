# Linear — reference index

Linear is the recommended board tool for the agentic operating model. Fast, opinionated, API-first.

## When `/setup-awow` infers Linear

Board URL hostname is `linear.app`. Example:
- `https://linear.app/<org>/team/<TEAM>/...`
- `https://linear.app/<org>/issue/<TEAM>-<num>`

## Reference files

The reference is split per concern, so the wizard can surface one section at a time and the team can override or skip each independently.

| File | Covers |
|---|---|
| [`reference/states.md`](reference/states.md) | Five-state contract → Linear workflow states; transition ownership. |
| [`reference/hierarchy.md`](reference/hierarchy.md) | Initiative / Project / Issue / Sub-issue and what belongs at each level. |
| [`reference/labels.md`](reference/labels.md) | `type:*` / `area:*` / `status:*` prefix scheme; workspace vs. team scope. |
| [`reference/fields.md`](reference/fields.md) | Priority, Estimate, Cycle, Due date, Assignee, Project. |
| [`reference/duplicates.md`](reference/duplicates.md) | Similar-issue surfacing, search, and the native "mark as duplicate" relation. |
| [`reference/team-page.md`](reference/team-page.md) | What a Linear team page and Project description should contain. |
| [`reference/cycles.md`](reference/cycles.md) | Cycles convention; cycle-time as SLE. |
| [`reference/mcp.md`](reference/mcp.md) | MCP install for Claude Code and Copilot; verify checklist; branch naming. |

`/setup-awow` Step 1 reads each file when it walks the team through the corresponding section.

## Tips for adopting teams

- Linear auto-generates branch names from the issue identifier — use them as-is.
- Workspace labels span teams; team labels are scoped. Use workspace labels only for genuinely cross-team concerns.
- Linear's Insights tab gives you cycle-time stats out of the box. Measure your own 85th-percentile and treat that as your team Service Level Expectation rather than importing external thresholds.
- Linear is fast, which makes the agentic loop feel different from slower boards. If you are choosing between candidates and latency matters, factor that in.
