# Board — Cauchyio

## Tool & wiring

- Tool: Linear. Workspace `cauchyio` — https://linear.app/cauchyio. Team **Cauchyio**, issue prefix `CAU`.
- Surface: the `linear-server` MCP (Claude Code). Read access verified 2026-08-25 (`list_teams`, `list_issues`, `list_issue_statuses`, `list_issue_labels`).
- Harness: Claude Code.
- History: until 2026-08-25 this repo's items lived on the awowio workspace's AWO team (session-inferred, never durably wired). New items land on CAU; historic `AWO-###` references in commits, docs, and proposals stay valid against the old board and are not rewritten. Items still open on AWO are ported individually (description ends "Ported from awowio/AWO-###"; the original is Canceled).

## State machine

| Five-state contract | Linear state | Owner of transition |
|---|---|---|
| Backlog / Todo | Backlog, Todo | Human refines into Todo |
| In Progress | In Progress | Agent (on pick-up / first commit) |
| In Review | In Review | Agent (on PR open) |
| Blocked | Blocked (workflow state) | Agent flags with a comment; human confirms |
| Done | Done | Agent (on merge) |

Terminal non-success states: `Canceled` and `Duplicate`. Humans move work there; the agent proposes, never executes.

## Hierarchy

Per the reference: L1 Initiative → L2 Project → L3 Issue → L4 Sub-issue. Issues are the agent-pickable contract — acceptance criteria, status, and comments live there. The agent creates work only at Issue / Sub-issue level; Projects and Initiatives are human-created.

## Label taxonomy

Prefix scheme per `context/team/conventions/REQUIRED/labels.md`: `type:*` / `area:*`; Blocked is a workflow state here, so no `status:*` labels exist.

In use today:

- `type:*` — task, bug, feature, improvement, blog, blocker
- `area:*` — process, content, business, infrastructure, marketing
- `project-type:*` — client-delivery, product, content, education, operations (project layer)
- Engagement- and pipeline-scoped families (`workstream:*`, `client:*`, `course:*`, `content:*`) plus the night-queue markers (`ready:🟢`, `night-ready`) — used by consulting and content work; not applied to awow repo items.

awow repo items carry one `type:*` label, plus `area:process` when the item is way-of-working machinery. Never create labels autonomously; propose first.

## Required fields

Priority is Linear's native field — never a label. Estimates and cycle assignment are human calls; the agent leaves them untouched unless asked.

## Avoiding duplicates

Search before creating, and read Linear's similar-issue suggestions before saving. Found an existing issue? Comment or advance it — do not open a second. Genuine duplicate: use **Mark as duplicate** (not a bare cancel) so the link to the canonical issue is preserved.

## Team page conventions

Not yet captured — deepen via a Step 1b re-run when needed.

## Cycles / iterations

Cycles are active on the team. The agent never assigns work to a cycle autonomously.

## Divergence from reference

- Blocked is modelled as a workflow state (the reference allows state or label; the board already has the state) — accepted.
- `Duplicate` exists as its own terminal state next to `Canceled`; the Mark-as-duplicate relation lands issues there — accepted.
- The label taxonomy extends the reference's prefixes with engagement/pipeline families and night-queue markers — accepted; the agent treats them as out of scope for awow repo items.
- Captured minimally at the 2026-08-25 board-source switch: team-page conventions and a full label normalisation pass were not walked. Re-run `/setup-awow` Step 1b to deepen.
