# GitHub Issues — hierarchy reference (skeleton)

GitHub's hierarchy is lighter than the other three boards. Discipline comes from conventions, not tool constraints.

| Concept | GitHub primitive | Notes |
|---|---|---|
| L1 — Strategic goal | Project v2 board, or Milestone | A Milestone is a flat date-bound bucket; a Project board can group by any custom field. |
| L2 — Capability | Tracking issue with a task-list | A regular Issue whose body is a checkbox list of child Issues. |
| L3 — Deliverable (agent-pickable story) | Issue | This is the level the agent picks up. |
| L4 — Action | Task in a task-list inside the Issue body | Checkbox lines in the body; not separate Issues. |

The agent treats Issues linked from a tracking-issue's checkbox list as **children** of the tracker. Sub-issues are not native to GitHub; the tracker pattern is the workaround.

> **Planning vocabulary.** Quarter planning speaks tool-agnostically in **outcome → epic → feature → story** — and names who sets each level — in `context/quarterly/README.md` and `/refinement-prep`. GitHub has no native Epic or Feature type, so those planning concepts are carried by Project boards / Milestones (outcome, epic) and tracking issues (feature); map them onto the primitives above with the team rather than assuming a shared meaning.

## Wizard responsibilities

**Mode A.** Recommend Projects-v2 for L1 and tracking-issues for L2.

**Mode B.** Look at recent activity; surface whether the team uses Milestones, Projects, or neither.

## What lands in `board.md`

```
## Hierarchy

- L1: <Project v2 | Milestone | not used>
- L2: <tracking-issue pattern | epic-label pattern | not used>
- L3 (agent-pickable): Issue.
- L4: <task-list within Issue body | not used>.

Divergence from reference: <none | list>.
```
