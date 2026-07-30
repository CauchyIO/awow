# Architecture-aware development — a second plane for the build-engine seam

**Status:** Proposed (v2 — incorporates an adversarial design review; see "Design review" at the end)
**Stacks on:** `feat/engine-soft-dependency` (`b51aa1f`) — extends the same PreToolUse hook, `using-awow`,
and `/setup-awow` Step 8. Lands after that PR; diff kept additive to ease the rebase.
**Tracking:** CAU-1153 (Cauchyio · Way of Working).

## The gap

awow keeps the agent honest against the **board plane** — *what* to build — via the
`board-aware-development` seam: a crosswalk skill plus the `board-linkage-check.py` PreToolUse hook that
fires a one-line reminder at each superpowers lifecycle moment (brainstorm → ticket, writing-plans →
acceptance criteria, …).

There is a second plane the seam ignores: the **architecture plane** — *how we have already decided to
build*. That knowledge is durable — ratified ADRs, solution-design records, pattern notes — and in
repos that run a retrieval agent over it, queryable in one call. Today nothing in the build loop
consults it. The superpowers loop is **codebase-aware** (it follows local patterns) but
**architecture-blind**: a plan can faithfully match the surrounding code while contradicting a decided
ADR, or re-design something an existing record already settled. The cheapest place to catch that is
*while the plan is being formed*.

This adds `architecture-aware-development` as the sibling of `board-aware-development`: same shape, same
hook, second plane — but **opt-in and config-gated**, so it is silent everywhere the plane is absent.

## Keystone — the `context/tooling/architecture.md` pointer

awow already declares the board plane in `context/tooling/board.md`. Mirror it for the architecture
plane. A single opt-in artifact that everything keys off:

```markdown
# Architecture plane (awow pointer)
adr_dir:      architecture_decision_record/             # where ratified decisions live (may be empty)
pattern_dir:  context/knowledge-base/patterns/          # durable pattern notes (may be empty)
kb_agent:     cauchy-kb (ask_brain / ask_brain_ultra)   # retrieval tool handle, or "none"
strictness:   stop-and-surface                          # stop-and-surface | warn-only
```

- **Hook gates on this file's existence.** No `context/tooling/architecture.md` → no `[awow
  architecture]` reminder. A cheap, deterministic filesystem check; plane-less repos feel nothing.
- **The skill reads it** for the KB-agent handle and the ADR/pattern locations — so the discipline is
  genuinely generic (any `ask_brain`-style tool, named here), with Cauchy as its first adopter, not
  Cauchy plumbing hard-coded into the pack.
- **`/setup-awow` produces it** only when the team confirms they have a plane — a real artifact, not a
  passing mention.
- **`strictness`** lets the team choose whether a conflict stops work or just warns — matching the
  honest reality that the stop is a disposition, not an enforced gate (below).

## The skill — `architecture-aware-development`

A crosswalk skill at `.agents/skills/architecture-aware-development/SKILL.md`, four beats:

1. **Plane check (graceful no-op).** Read `context/tooling/architecture.md`. Absent → silently do
   nothing. Present but `kb_agent: none` → fall back to reading the named ADR/pattern dirs directly;
   still nothing on disk → no-op. Never invent an ADR that is not there.

2. **Prior-art probe — folded into the board beat, not a new ritual.** At `brainstorming`, *inside* the
   existing "go to the board" beat (board-aware-development already merged brainstorm + board-check into
   one beat), also ask the KB agent: does an ADR / design / pattern **already cover this**? If yes,
   reuse or extend it rather than designing from scratch. This is deliberately light — the start edge
   stays whisper-thin (awow rolled back an earlier over-anchoring; we do not re-add weight here).

3. **Alignment + flag governed parts.** At `writing-plans` (where a spec exists and a query has real
   nouns to bind to), run the alignment: a **targeted query built from the plan's domain nouns**, not a
   vague "any conflicts?" — query specificity is the biggest lever on recall. Then **flag the specific
   plan tasks that touch governed surfaces.** Those flags are the per-part carrier (see below).

4. **Stop-and-surface on conflict; scoped citation on alignment.**
   - **Conflict** with a ratified ADR / established pattern → **do not proceed silently**: surface it
     concretely (ADR id + file path + the contradiction) and seek human reconciliation. This is a
     *disposition the hook prompts*, not a technically enforced gate — same honesty level as every awow
     reflex; `strictness: warn-only` downgrades it to a warning.
   - **Alignment** → cite **"checked against: [the ADRs/patterns actually retrieved]"** — never "no
     conflicts found," which would falsely imply completeness. The citation claims scope-of-check, not
     a global guarantee. Residual recall-miss risk is real and documented: this *reduces*
     architecture-blindness, it does not eliminate it.

**Query tooling.** Cheap retrieval (`ask_brain`) for the prior-art probe and per-part re-checks;
escalate to the deeper call (`ask_brain_ultra`) for the single plan-time alignment, or when cheap
evidence is thin/ambiguous on a *potential conflict* — don't stop, or wave through, on weak evidence.
Named generically in the skill; Cauchy tool names given as the concrete instance.

## The crosswalk

| Engine skill (the moment) | Architecture action |
|---|---|
| `brainstorming` | **Prior-art probe**, folded into the board beat — already decided? reuse/extend. Light. |
| `writing-plans` | **Full alignment** (targeted query) + **flag governed tasks**; stop-and-surface on conflict; scoped citation. |
| `executing-plans` / `subagent-driven-development` / `test-driven-development` | **Re-check the flagged tasks only** — carried by the plan, not a blind per-task query. Hook reminds once at execution start. |

Completion-edge moments (`verification-before-completion`, `requesting-code-review`,
`finishing-a-development-branch`) stay board-only — architecture alignment is a design/build concern.

**Why per-part lives in the plan, not the hook.** The PreToolUse hook fires *once* when
`executing-plans` is invoked — not per task. So true per-part rigor cannot ride the hook. It rides the
**plan**: writing-plans flags the governed tasks, and execution re-checks only those. This is both
honest about the mechanism and cheaper than re-querying every task.

## The hook — extend it, and rename it

`board-linkage-check.py` already fires at superpowers moments under the right gates (tool is `Skill`,
`.agents/AGENTS.md` exists, superpowers installed). Changes:

- Add an `ARCH_SEAM` map keyed on `brainstorming`, `writing-plans`, `executing-plans`,
  `subagent-driven-development`, `test-driven-development`.
- **Add one gate for the architecture line only:** emit it solely if `context/tooling/architecture.md`
  exists in the project dir. (The board line keeps its current gates.)
- Co-emit both reminders in `additionalContext` — `[awow board-linkage]` and `[awow architecture]`; a
  skill in both maps (e.g. `writing-plans`) produces both lines.
- Stays non-blocking on malformed/empty input (exit 0).
- **Rename** `board-linkage-check.py` → `lifecycle-seam-check.py` (it now carries two seams) — one
  `git mv` + one line in `hooks/hooks.json`. Small, removes a file whose name would otherwise lie.

## `using-awow` — one-line discoverability

Add one line to the "When an inner-loop engine is present" section, parallel to the existing
`board-aware-development` reference: the same lifecycle skills are also your *architecture* cues (when a
`context/tooling/architecture.md` plane exists) — see `architecture-aware-development`.

## `/setup-awow` Step 8 — offer the plane pointer

Step 8 detects the build engine. Extend it:
- Mention both seams light up with the engine (board-aware + architecture-aware).
- **Offer to write `context/tooling/architecture.md`** when the team confirms they have an architecture
  plane (ADRs/patterns + a KB agent). Drafted to `proposals/setup/step-8/` first, approved, then landed
  — same proposal-first discipline as the rest of setup. No plane → skip it; the seam stays dormant.

## `gather.py` — mirror the new skill

Run `python tools/gather.py`; commit the regenerated `.claude/` + `.github/` stubs for the new skill.
No code change.

## Out of scope (YAGNI)

- Wiring alignment into `/process-workitem` or `/project-plan` bodies — the hook + plan-carrier cover
  the direct path; the command path is a follow-on if needed. (`/process-workitem` is also the one
  place a near-real gate is possible via a checklist tick — noted for later, not v1.)
- Any change to the `cauchy-kb` agent or to how the KB is seeded from ADRs — this *consumes* the KB.
- Auto-creating or editing ADRs/pattern notes. The skill reads and surfaces; it never writes the plane.

## Efficacy — measured as a follow-up, not gated on v1

The ACs prove the wiring; they do not prove value. Follow-up after rollout: **spot-check a handful of
real planning sessions** — were the "checked against" citations accurate, was any genuine conflict
caught or missed? Optionally fold an architecture-conformance probe into the existing weekly
`kb-agent-eval`. Manual spot-check first — this is a behavioral nudge, not worth a full eval rig up
front.

## Acceptance criteria

1. `architecture-aware-development/SKILL.md` exists, written in generic KB-agent terms, covering the
   four beats (plane-check → folded prior-art probe → alignment+flag → stop-and-surface + scoped
   citation) and the three-moment crosswalk, with the per-part carrier living in the plan.
2. `context/tooling/architecture.md` convention documented (the skill + setup-awow reference it); the
   linear repo's own pointer is created as the first adopter.
3. Hook renamed to `lifecycle-seam-check.py` (with `hooks.json` updated), emits `[awow architecture]`
   for the five named skills **only when `context/tooling/architecture.md` exists**, co-emits with the
   board line for `writing-plans`, and remains non-blocking on malformed input.
4. `using-awow/SKILL.md` references the new skill in one line, parallel to `board-aware-development`.
5. `/setup-awow` Step 8 mentions both seams and offers to write the architecture pointer (proposal-first,
   skipped when no plane).
6. `gather.py` stubs regenerated for the new skill in `.claude/` and `.github/`.
7. Hook behaviour verified by piping sample `PreToolUse` payloads through the renamed hook: the
   `[awow architecture]` line appears for the five skills **with** a pointer file present and is absent
   **without** one; board + architecture lines co-emit for `writing-plans`; malformed/empty input exits
   0 without output. (awow has no automated hook-test harness today — this is the manual stdin check; a
   regression test is worth adding only if/when such a harness exists.)

## Design review (what changed from v1, and why)

An adversarial pass on v1 surfaced two mechanism/intent mismatches and several trade-offs:

- **"Per-part" couldn't ride the hook** (fires once per skill invocation, not per task) → moved the
  per-part carrier into the **plan** (flag governed tasks at writing-plans; re-check only those).
- **The hook fired unconditionally**, noise in every plane-less repo → **config-gated** on the
  `architecture.md` pointer (the keystone), which also makes the skill genuinely generic/opt-in.
- **"Gate" over-promised** an enforcement the mechanism can't deliver → reworded to a **stop-and-surface
  disposition**, with a per-repo `strictness` flag.
- **Citations could lie** on a recall miss → scoped to **"checked against: […]"** + targeted
  domain-noun queries; residual risk documented.
- **Start-edge ceremony** (against awow's whisper-thin stance) → prior-art probe **folded into the
  existing board beat**, rigor biased to writing-plans, plane-less repos feel nothing.
- **Efficacy** had no measure → explicit **follow-up spot-check**, not a v1 gate.
- **Misnamed hook** → renamed to `lifecycle-seam-check.py`.
