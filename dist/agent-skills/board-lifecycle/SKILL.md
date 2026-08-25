---
name: board-lifecycle
description: "Use when the board's project layer needs governing — projects without owners or end conditions piling up, nobody sure which containers are alive, or a planning round that needs a trustworthy project overview first. Declares shapes and horizons, sweeps the estate, and turns expiry into a visible exception instead of silent rot or a silent auto-close."
---

# /board-lifecycle — govern the project layer

A board's project list only stays truthful if every project carries two facts: **what kind of thing it is** (its shape) and **when its right to exist expires** (its horizon). This command declares those facts as a team convention, sweeps the estate against them, and turns expiry into a **visible exception that a human resolves** — never silent rot, and never an automatic close.

The user's job is two actions: invoke, and approve (or reject) the exception plan. Classification is read-only and shown, never assumed.

## The mechanism (the rules this command enforces)

- **Shapes.** Every project carries exactly one mutually exclusive shape label — default set `shape:engagement`, `shape:campaign`, `shape:system`; teams may rename or extend in their lifecycle contract. Applied at creation by project template.
- **Shape-specific horizons.** An engagement expires at its contract or SOW end; a campaign at its target date; a system at its scheduled scope review. **A missing horizon is itself an exception** — a project with no end condition has no verifiable right to exist.
- **Exception, never auto-close.** An expired project moves (via the approved plan only) into a reversible exception status — `Needs decision`, or the board's configured equivalent. The project lead renews it with a new horizon or closes it; closure is always a human act. **No path in this command closes a project automatically.**
- **Tripwire.** An exception unresolved for two consecutive cycles marks its initiative `At risk`, and the initiative's rollup states its board state is unverified until the exception resolves. The sweep reports tripwire breaches; the consequence is the convention's, not an automated write.
- **Timestamps are never the staleness signal.** Metadata edits and cross-project touches refresh activity timestamps on dead work, and quiet work can be alive. Expiry is judged against the declared horizon, nothing else.

## Ground — the lifecycle contract

Read the `## Lifecycle` section of `{HUB}/context/tooling/board.md`: the shape set, each shape's horizon rule, and the exception status name (see the boards reference for the section's documented form). When the section is absent, draft it from the defaults above, present it, and — only on explicit approval — append it to `{HUB}/context/tooling/board.md`. Never invent a team's lifecycle silently, and never write team context without that approval.

## Sweep — classify the estate (read-only)

Ground every run on a **dated project-inventory snapshot**:

- Live board reachable → read it (read-only) and record today's snapshot: per project its name, initiative, status, shape label, horizon field, lead.
- Otherwise, or when handed one → `--snapshot <path>` names an existing dated snapshot; use it and state its date in every output (a stale snapshot is a caveat, not a blocker).

Classify every project, one verdict each, and show the table with the basis stated:

| Verdict | Meaning |
| --- | --- |
| `healthy` | shape present, horizon present and in the future |
| `expired` | horizon passed — the project's authorization ran out |
| `missing-horizon` | no horizon for its shape — unverifiable, treated as an exception |
| `missing-shape` | no (or multiple) shape labels — the template gate failed; fix the shape first |
| `in-exception` | already in the exception status; report cycles elapsed and any tripwire breach |

With `--check`, stop after the table. Write nothing.

## The exception plan (gate)

Present one diff-style plan — per project: verdict, proposed action (`→ Needs decision`, `label shape:<x>`, `set horizon <rule>` as an ask to its lead), and the tripwire breaches to surface. Renewals and closures are **not** plan lines — they belong to the humans the plan routes them to. **Write nothing until the user approves.** On approval, apply through the board surface, one action at a time, confirming each; board-write mechanics and re-verification follow the `workitem-write` discipline.

## Routing new work (the creation-side counterpart)

The sweep cleans; this ladder keeps it clean. When new work arrives, walk it in order — every step can end the walk:

1. **Metric or work?** A number to watch goes to the scoreboard or dashboard, never into a project.
2. **Existing container or genuinely new body of work?** Search first; a near-duplicate project is board debt on day one.
3. **Issue or project?** Small enough for one container's backlog → an issue there. A project must clear the gate: a nameable outcome, a before-state, a scope, an owner.
4. **Which initiative?** Every project hangs under one; "none fits" is a conversation with the initiative owners, not a floating project.
5. **Which shape?** Exactly one `shape:*` label, which fixes its horizon rule from day one.
6. **What does it serve?** A `Serves:` line naming the objective or KR, an explicit BAU marker, or — when neither is true — visible drift: the project may exist, but its unalignment is on the surface, not hidden.

"A logical place for everything" therefore does not always mean "create a project": numbers go to the scoreboard, small work becomes an issue, and unaligned work is exposed as drift.

## `--ledger` — adopting the mechanism on a lived-in board

A board that predates the mechanism needs a migration with sign-off, not a bulk sweep. Emit the ledger skeleton to `{PROJECT}/proposals/board-lifecycle-ledger-<date>.md`: one row per project from the snapshot, columns `decision ratified · live re-verified · issue dispositions complete · applied + verified`, all unchecked. The ledger is complete only when every row carries all four marks — until then, "the board is ready" is interpretation, not evidence. Filling the ledger happens in working sessions (the exception plan above, project by project); this command only keeps the skeleton current against newer snapshots.

## Behavioural boundaries

- **No auto-close exists.** Not on expiry, not on tripwire, not on approval of the plan. Closure is a human decision on a named project.
- **Horizon, never timestamp.** Any staleness argument from activity data is refused by construction.
- **Read-only until the gate.** The sweep, the table, and `--check` never write; the lifecycle contract lands in team context only on explicit approval.
- **Shapes are exclusive.** A project with two shapes is `missing-shape`, not "both" — the classification refuses ambiguity rather than picking one.
- **Scope is the project layer.** Issues route through `/process-workitem` and `workitem-write`; KR grading is `/okr-cascade` Review.
