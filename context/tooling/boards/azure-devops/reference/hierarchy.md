# Azure DevOps — hierarchy reference

ADO enforces a strict four-level hierarchy through its work-item-type schema.

| Concept | ADO primitive | What belongs here |
|---|---|---|
| L1 — Strategic goal | Epic | Multi-quarter outcome. |
| L2 — Capability | Feature | Quarter-scale chunk. Has a single owner. |
| L3 — Deliverable (agent-pickable story) | User Story (Agile) / Product Backlog Item (Scrum) | Days to a week. Has acceptance criteria. |
| L4 — Action | Task | Hours. Optional; only when decomposition is useful. |

ADO is the most opinionated of the supported boards — the hierarchy is enforced by the schema, not by convention.

## Rules

- Tasks **cannot** be promoted to standalone User Stories. If a Task is growing acceptance criteria, the agent proposes splitting it into a sibling User Story under the parent Feature.
- Every User Story must have an **Area Path** and an **Iteration Path** set. The agent refuses to pick up an Issue with no Iteration Path.
- Epics live in the Portfolio Backlog; the agent does not create or move Epics autonomously.

## Wizard responsibilities

**Mode A (from reference).** Confirm the team uses Epic / Feature / User Story / Task. Ask for one or two example Epic names so the agent has a vocabulary anchor. Tell the user the agent only creates User Stories or Tasks autonomously.

**Mode B (assess current).** Read the actual hierarchy in use. Surface anything unusual: Tasks with acceptance criteria, User Stories without parent Features, missing Iteration Paths.

## What lands in `board.md`

```
## Hierarchy

- L1 (Epic): example names: <…>
- L2 (Feature): in use, <N> active.
- L3 (User Story / PBI): agent-pickable level.
- L4 (Task): used for <hourly decomposition | not used>.

Divergence from reference: <none | list>.
```
