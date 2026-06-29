# Architecture-aware development — a second plane for the build-engine seam

**Status:** Proposed
**Stacks on:** `feat/engine-soft-dependency` (`b51aa1f`) — extends the same three surfaces (the PreToolUse hook, `using-awow`, `/setup-awow` Step 8). Should land after that PR.
**Tracking:** Cauchy (CAU) Linear issue — to be created from this proposal.

## The gap

awow already keeps the agent honest against the **board plane** — *what* to build — via the
`board-aware-development` seam: a crosswalk skill plus the `board-linkage-check.py` PreToolUse hook
that fires a one-line reminder at each superpowers lifecycle moment (brainstorm → ticket,
writing-plans → acceptance criteria, …).

There is a second plane the seam ignores: the **architecture plane** — *how we have already decided
to build*. That knowledge is real and durable — ratified ADRs, solution-design records, durable
pattern notes — and in repos that run a retrieval agent over it (an `ask_brain`-style KB agent) it is
queryable in one call. Today nothing in the build loop consults it. The superpowers loop is
**codebase-aware** (it explores files and follows local patterns) but **architecture-blind**: a plan
can faithfully match the surrounding code while quietly contradicting a decided ADR, or re-design
something an existing record already settled. The cheapest place to catch that is *while the plan is
being formed*, not after a diff exists.

This proposal adds `architecture-aware-development` as the exact sibling of `board-aware-development`:
same shape, same hook, second plane.

## Design

### The skill — `architecture-aware-development`

A new crosswalk skill at `.agents/skills/architecture-aware-development/SKILL.md`. It defines the
"how" the hook nudges toward, in four beats, in order:

1. **Existence check first (graceful degradation).** Before anything, establish whether an
   architecture plane is even present in this repo: a retrieval agent over the knowledge base (an
   `ask_brain`-style MCP tool), and/or ADRs / solution-design docs / durable pattern notes on disk.
   **If the plane is absent or thin → silently no-op.** Never block, never invent an ADR that is not
   there. This is what makes the skill safe to ship in the *public* awow pack: an adopter with no KB
   simply never feels it. (In a Cauchy repo this resolves to the `cauchy-kb` agent + the
   `architecture_decision_record/` and `context/knowledge-base/patterns/` trees.)

2. **Prior-art probe (reuse before reinvent).** At the *design* moment, ask the KB agent whether an
   ADR, solution-design, or pattern note *already covers the thing being planned*. If one exists,
   reuse or extend it rather than designing from scratch. This is the first, cheapest win — it stops
   the loop re-deriving settled decisions.

3. **Alignment.** At the *plan* moment, query the governing ADRs/patterns for the plan's scope and
   reconcile the plan against them.

4. **Gate on conflict + cite on alignment.**
   - **Conflict** with a ratified ADR or an established pattern → **stop**, surface it concretely
     (the ADR id + file path + the specific contradiction), and require human reconciliation before
     proceeding. Matches awow's approval-gated ethos.
   - **Clean alignment** → **cite** the governing ADRs/patterns (with file paths) into the plan as a
     provenance trail, even when there is no conflict.

**Query tooling.** Use the KB agent's cheap retrieval call for the prior-art probe and the per-part
checks (in Cauchy: `ask_brain` — a Haiku gather returning an evidence bundle the caller synthesises).
Escalate to the deeper, server-synthesised call for the single plan-time alignment, or whenever the
cheap evidence is thin/ambiguous on a *potential conflict* — you do not want to gate, or wave
through, on weak evidence (in Cauchy: `ask_brain_ultra`).

All KB-agent references in the skill are written **generically** ("your KB agent", "an
`ask_brain`-style retrieval MCP") with the Cauchy tool names given only as the concrete instance, so
the skill is a real public-pack discipline rather than Cauchy-coupled.

### The crosswalk (which moment does what)

| Engine skill (the moment it fires) | Architecture action riveted to it |
|---|---|
| `brainstorming` (design starting) | **Prior-art probe** — does an ADR / design / pattern already cover this? Reuse/extend, don't reinvent. |
| `writing-plans` (a spec exists) | **Full alignment** — query governing ADRs/patterns for the scope; gate on conflict, cite conforming ones into the plan. |
| `executing-plans` / `subagent-driven-development` / `test-driven-development` (per part) | **Per-part re-check** — lightweight probe against that part's specific surface; gate if the part drifts from a decided pattern. |

Completion-edge moments (`verification-before-completion`, `requesting-code-review`,
`finishing-a-development-branch`) stay board-only — architecture alignment is a design/build-time
concern, not a landing concern.

### The hook — extend `board-linkage-check.py`

The existing PreToolUse hook already fires at superpowers lifecycle moments under the right gates
(tool is `Skill`, `.agents/AGENTS.md` exists, superpowers installed). Extend it minimally:

- Add a second reminder map, `ARCH_SEAM`, keyed on `brainstorming`, `writing-plans`,
  `executing-plans`, `subagent-driven-development`, `test-driven-development`.
- For a given skill invocation, collect **both** the board reminder (if any) and the architecture
  reminder (if any) and emit them together in `additionalContext` — board prefixed
  `[awow board-linkage]`, architecture prefixed `[awow architecture]`. A skill in both maps (e.g.
  `writing-plans`) produces both lines.
- The hook stays a dumb, non-blocking nudge under the **same gates** as today. The
  *existence-check / no-op* logic lives in the **skill**, not the hook — the hook cannot cheaply know
  whether a KB agent is wired, so it nudges unconditionally and the skill degrades. The architecture
  nudge is therefore worded conditionally ("if this repo has an ADR/KB plane, align against it") so
  it reads as mild guidance, not noise, in a plane-less repo.

Keep the filename (`board-linkage-check.py` is wired in `hooks/hooks.json`); broaden its docstring to
"lifecycle-seam reminders (board + architecture)". A rename to `lifecycle-seam-check.py` is **out of
scope** — it would touch the hook wiring for cosmetic gain.

### `using-awow` — one-line discoverability

Add a single line to `using-awow/SKILL.md` "When an inner-loop engine is present" section, parallel
to the existing `board-aware-development` reference: the same lifecycle skills are also your
*architecture* cues — see `architecture-aware-development` for the crosswalk.

### `/setup-awow` Step 8 — mention the second seam

Step 8 already detects the build engine and notes the `board-aware-development` seam activates. Update
the **Found** and **Not found** branches so they mention that installing superpowers lights up *both*
the board-aware **and** architecture-aware seams, and add one clause: the architecture seam consults
a KB/ADR plane if the repo has one and silently no-ops otherwise (so it is zero-config — no install
step, just discoverability).

### `gather.py` — mirror the new skill

The new skill is auto-mirrored to `.claude/` and `.github/` stubs by running `python tools/gather.py`.
No code change; just run it and commit the generated stubs.

## Why this shape

- **Rides the existing seam.** The firing mechanism for "brainstorm + plan + each part" already
  exists — the PreToolUse hook that watches superpowers invocations. No new SessionStart injector, no
  repo-local overlay. The user's instinct was right: bake it into the awow package and it follows
  automatically wherever awow is installed.
- **Public-pack safe by construction.** The existence-check / silent-no-op means the discipline is
  generic awow, not Cauchy plumbing — it lights up only where an architecture plane exists.
- **Reuse before conformance.** Prior-art probe first, gate second: the highest-value move is not
  catching conflicts but stopping the loop from re-deciding what an ADR already settled.

## Out of scope (YAGNI)

- Renaming the hook file or the hook event wiring.
- Wiring architecture alignment into `/process-workitem` or `/project-plan` command bodies — the
  hook-driven nudge at superpowers moments covers the direct path; the command path can be a
  follow-on if it proves needed.
- Any change to the `cauchy-kb` agent itself, or to how the KB is seeded from ADRs — this consumes
  the KB agent, it does not modify it.
- Auto-creating or auto-editing ADRs/pattern notes. The skill reads the plane and gates; it never
  writes to it.

## Acceptance criteria

1. `architecture-aware-development/SKILL.md` exists, written in generic KB-agent terms, covering the
   four beats (existence-check → prior-art probe → alignment → gate+cite) and the three-moment
   crosswalk.
2. `board-linkage-check.py` emits an `[awow architecture]` reminder at `brainstorming`,
   `writing-plans`, `executing-plans`, `subagent-driven-development`, and `test-driven-development`,
   alongside any board reminder, under the existing gates; remains non-blocking on malformed input.
3. `using-awow/SKILL.md` references the new skill in one line, parallel to `board-aware-development`.
4. `/setup-awow` Step 8 mentions both seams and the KB-agent no-op behaviour.
5. `gather.py` stubs regenerated for the new skill in `.claude/` and `.github/`.
6. Hook behaviour verified by piping sample `PreToolUse` payloads through `board-linkage-check.py`:
   the `[awow architecture]` reminder appears for the five named skills, board + architecture lines
   co-emit for `writing-plans`, and malformed/empty input still exits 0 without output. (awow has no
   automated hook-test harness today — verification is this manual stdin check; a regression test is
   only worth adding if/when such a harness exists.)
