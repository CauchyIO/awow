# Jira — hierarchy reference (skeleton)

Jira's hierarchy depends on the project type and whether Advanced Roadmaps is in use.

| Concept | Jira primitive | Notes |
|---|---|---|
| L1 — Strategic goal | Initiative (Advanced Roadmaps only) **or** large Epic | |
| L2 — Capability | Epic | Default L2 in most teams. |
| L3 — Deliverable (agent-pickable story) | Story (or Task) | This is the level the agent picks up. |
| L4 — Action | Sub-task | Hours. Optional. |

Jira's "Story" is overloaded — clarify with the team which level it represents before mapping. Some teams use Story for L2 and Task for L3.

> **Planning vocabulary.** Quarter planning speaks tool-agnostically in **outcome → epic → feature → story** — and names who sets each level — in `context/quarterly/README.md` and `/refinement-prep`. The same word sits at a different level on each board (here "Epic" is L2, and Jira carries no distinct "Feature" type), so map those concepts onto the primitives above with the team rather than assuming a shared meaning.

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
