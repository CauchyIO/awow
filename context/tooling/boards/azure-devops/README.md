# Azure DevOps — reference index

Azure DevOps (ADO) is the heavy-enterprise option of the four supported boards. Best when the team is operating inside a larger organisation with established ADO practice.

## When `/setup-awow` infers Azure DevOps

Board URL hostname matches:
- `dev.azure.com/<org>/<project>/...`
- `<org>.visualstudio.com/...` (legacy)

## Reference files

| File | Covers |
|---|---|
| [`reference/states.md`](reference/states.md) | Five-state contract → ADO workflow states. |
| [`reference/hierarchy.md`](reference/hierarchy.md) | Epic / Feature / User Story / Task. |
| [`reference/labels.md`](reference/labels.md) | ADO tags with the `type:*` / `area:*` / `status:*` scheme. |
| [`reference/fields.md`](reference/fields.md) | Priority, Effort, Iteration, Area Path, Assigned To. |
| [`reference/team-page.md`](reference/team-page.md) | Team description and Iteration Path conventions. |
| [`reference/iterations.md`](reference/iterations.md) | Iterations / sprints; cycle-time as SLE. |
| [`reference/mcp.md`](reference/mcp.md) | MCP install; verify checklist; branch naming; rate-limit notes. |

## Enterprise scale

For organisations running ADO at 2,000+ employees with SAFe / Solution Train overlay, the work-item hierarchy is typically extended with Portfolio Epics → Solutions → Capabilities → Features. The four-level mapping above still holds at the team altitude; the higher levels live in a programme-management surface that this repo does not directly model.

## Tips for adopting teams

- Use the native Priority field; do not duplicate priority into tags.
- Area Paths matter for board scoping — pick one team-wide convention and document it.
- ADO has a per-organisation API rate limit. The seed commands batch writes to stay under it; if you customise heavily, watch for `429` responses.
