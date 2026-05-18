# Jira — hierarchy reference (skeleton)

Jira's hierarchy depends on the project type and whether Advanced Roadmaps is in use.

| Concept | Jira primitive | Notes |
|---|---|---|
| L1 — Strategic goal | Initiative (Advanced Roadmaps only) **or** large Epic | |
| L2 — Capability | Epic | Default L2 in most teams. |
| L3 — Deliverable (agent-pickable story) | Story (or Task) | This is the level the agent picks up. |
| L4 — Action | Sub-task | Hours. Optional. |

Jira's "Story" is overloaded — clarify with the team which level it represents before mapping. Some teams use Story for L2 and Task for L3.

## Wizard responsibilities

**Mode A.** Confirm the team's L2 (Epic vs. Initiative) and L3 (Story vs. Task) primitives.

**Mode B.** List recent issues; surface which types are in use and which feel agent-pickable.

## What lands in `board.md`

```
## Hierarchy

- L1: <Initiative | large Epic | not used>
- L2: <Epic>
- L3 (agent-pickable): <Story | Task>
- L4: <Sub-task | not used>

Divergence from reference: <none | list>.
```
