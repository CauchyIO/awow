# Linear — required fields reference

Linear ships native fields for Priority, Estimate, Cycle, Due date, and Assignee. The agentic operating model leans on some of them more than others.

| Field | Load-bearing? | Why |
|---|---|---|
| Priority | Yes | Drives the agent's pick order in `/process-workitem` when no other signal is present. |
| Estimate | Optional | Useful for cycle-time analysis; the agent neither requires nor proposes estimates by default. |
| Cycle | Yes if the team runs cycles | Scopes "what's in flight this week"; surfaced by `/sprint-review-prep`. See `cycles.md`. |
| Due date | Situational | Used only when a real external deadline exists; the agent never invents one. |
| Assignee | Yes | The agent reads this to know whose work it is picking up; refuses to pick up issues assigned to another human. |
| Project | Yes | Mandatory for any non-trivial Issue — every Issue must live under an L2 Project. |

## Priority

Linear's Priority field has five levels: No priority / Urgent / High / Medium / Low. The convention:

- **Urgent** — actively-on-fire incident. The agent should drop other work to pick this up.
- **High** — committed for this cycle. Default for new Issues entering Todo.
- **Medium** — wanted; will land within the next 2–3 cycles.
- **Low** — opportunistic; only picked up when the queue is otherwise empty.
- **No priority** — refinement not complete. The agent does not pick these up.

Do not duplicate Priority via labels (see `labels.md`).

## Estimate

Linear estimates are configurable per team (Fibonacci, T-shirt, linear 0–5). The convention:

- **If the team estimates,** the agent surfaces estimate-vs-cycle-time delta in `/sprint-review-prep` but does not propose estimates itself.
- **If the team does not estimate,** no agent behaviour depends on it. Skip the field.

## Assignee

The agent **only** acts on Issues that are unassigned or assigned to the human invoking the agent. It refuses to pick up work assigned to another human (read access only; no state changes, no comments).

## Wizard responsibilities

**Mode A (from reference).**

1. Confirm Priority is enabled (it is by default on Linear).
2. Ask whether the team estimates. If yes, ask which scale and record it.
3. Confirm the agent's rule: only acts on unassigned or self-assigned Issues.

**Mode B (assess current).** Use the MCP to list a handful of recent Issues (`mcp__linear-server__list_issues`) and check:

- Are Priority values being set? If most Issues are at `No priority`, surface that as a gap.
- Are estimates being filled? If sparse, recommend dropping estimates from the convention or fixing the discipline.
- Are Issues being created without a Project? That breaks the L2 contract; surface it.

Resolved decisions land in `## Required fields` of `context/tooling/board.md`.

## What lands in `board.md`

```
## Required fields

- Priority: <Urgent | High | Medium | Low — meaning per reference>
- Estimate: <scale, or "not used">
- Cycle: <in use | not used>
- Due date: <"only when external deadline" | other>
- Assignee: agent only acts on unassigned or self-assigned Issues.
- Project: every Issue must live under an L2 Project.

Divergence from reference: <none | list>.
```
