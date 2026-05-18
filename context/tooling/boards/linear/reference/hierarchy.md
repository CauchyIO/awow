# Linear — hierarchy reference

Linear is flat by design. The four-level hierarchy from `input/PROPOSAL.md` is realised through Linear's primitives:

| Concept | Linear primitive | What belongs here |
|---|---|---|
| L1 — Strategic goal | Initiative | Multi-quarter outcome. Names a customer change, not a deliverable. |
| L2 — Capability | Project | Quarter-scale chunk of an initiative. Has a single project lead. |
| L3 — Deliverable (agent-pickable story) | Issue | Days to a week of work. Has acceptance criteria. This is the level the agent picks up via `/process-workitem`. |
| L4 — Action | Sub-issue | Hours of work. Optional; only when an Issue needs explicit decomposition (e.g. multi-PR rollout). |

Linear's `Sub-issue` is more flexible than ADO's `Task` — sub-issues can be **promoted to standalone issues** if scope grows. The agent should propose promotion rather than letting a sub-issue accrete acceptance criteria of its own.

## Rules

- **Initiatives** are not agent-pickable. The agent never moves work directly under an Initiative; it always lives under a Project.
- **Projects** must have a description that names the customer change and the time horizon. The agent reads this when scoping new Issues.
- **Issues** are the contract. Acceptance criteria live here; status moves here; comments accumulate here.
- **Sub-issues** inherit assignee and labels from the parent unless explicitly overridden.

## Wizard responsibilities

**Mode A (from reference).**

1. Confirm the team intends to use Initiatives at all (some teams skip L1 and operate Project-first). Record the choice.
2. If Initiatives are in use, ask for one or two example initiative names so the agent has a vocabulary anchor.
3. Tell the user the agent will only ever create work at the Issue / Sub-issue level autonomously; Project and Initiative creation is human-only.

**Mode B (assess current).** Use the MCP to list Projects (`mcp__linear-server__list_projects`) and Initiatives where available. Surface:

- Whether Initiatives are in use, and how deep the team goes.
- Which Project descriptions are populated vs. empty (empty Project descriptions are a common source of agent drift).
- Any Issues that have grown >5 Sub-issues (signal that the Issue should have been a Project).

Resolved decisions land in `## Hierarchy` of `context/tooling/board.md`.

## What lands in `board.md`

```
## Hierarchy

- L1 (Initiative): <in use | skipped>. Example names: <…>.
- L2 (Project): in use. <N> active. Project descriptions are <populated | sparse>.
- L3 (Issue): agent-pickable level.
- L4 (Sub-issue): used for <multi-PR rollouts | not used>.

Divergence from reference: <none | list>.
```
