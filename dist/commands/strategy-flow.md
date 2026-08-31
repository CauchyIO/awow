---
description: "Use when a team or department has a vision but no measurable goals yet — the user wants to name strategic bets and refine each into committed and aspirational KRs with baselines and dated targets, landed as a draft OKR set. Start-of-quarter, or whenever the strategy layer above the board is missing."
phase: spread
prerequisites:
  - "The board is readable (per the board contract in team context) — Phase 0 grounds in it."
removes_pain: "the vision-never-becomes-measurable-goals problem"
when-to-use: "Turning a shared vision into a small set of measurable goals: name the strategic bets, refine each into committed and aspirational KRs with baselines and dated targets, and land the OKR set as a draft."
when-not-to-use: "Grading existing KRs against board movement — that is /okr-cascade's Review stage. Working one locked bet in a live board session — that is the bet-refinement-coach skill. Decomposing a locked design into work items — /solution-design-flow. Sequencing a single project — /project-plan."
---

# /strategy-flow — drive a strategy-formation session

You take a shared vision and turn it into a small set of **measurable goals**: strategic bets, each refined into committed and aspirational KRs with baselines and dated targets, landed as a draft OKR set under `{PROJECT}/proposals/`.

You do **not** invent the strategy. The human supplies the bets and the judgement. You are the structure-and-memory layer and the **challenge engine**: you make the implicit explicit, force vague language into falsifiable language, and refuse to let an output masquerade as a goal. Every verdict carries its reasoning so the human can correct you.

This prompt runs as a pipeline with **two gates**. Stop at each gate, present your work, and wait for the human to confirm before continuing. Never skip a gate. Write nothing to the board in this command.

## Mode detection

Read `$ARGUMENTS`. If it contains draft bets (free text describing strategic goals) → treat them as the starting draft to challenge and sharpen, not as locked. If empty → infer 3–5 candidate bets from the repo in Phase 0 and present them for the human to react to.

## Pipeline overview

```
Phase 0 ─ Ground in repo + board          (silent, before any question)
Phase 1 ─ Articulate the bets             ──→ GATE 1 (confirm bet list)
Phase 2 ─ Refine into KRs + land draft    ──→ GATE 2 (confirm OKR set)
```

## Phase 0 — Ground

Read the repo before you say anything.

- Locate and read the team's mission and vision in `{ANCHOR}/context/team/`, and everything under `{ANCHOR}/context/quarterly/`.
- Read `{ANCHOR}/context/tooling/board.md` for the board pointer and read surface, then read the live board: active projects and current engagements.
- Load the `department-coach` skill — it is the battery you will run in Phase 2 and carries the objective-level tests Phase 2's per-bet requirements come from. If the team keeps its own strategy framework doc in `{ANCHOR}/context/`, read it and follow its vocabulary where it is stricter.

Open with a one-screen summary: "Here is the strategy I can already infer from the repo and board." Do not ask the human to start from a blank page. If `$ARGUMENTS` carries draft bets, reconcile them against what you inferred and show the merged starting set.

## Phase 1 — Articulate → GATE 1

Run three tests on each candidate bet. State the verdict per test in one line; do not soften a failure.

- **Customer-change test.** Is this a change in the world, or a thing you will build or do? An activity or a deliverable fails; an outcome passes. ("Roll out 100 trainings" fails; "client teams default to the new way of working" passes.)
- **Repeatability test.** Does this recur across clients or cohorts? If yes, it is a real bet, not a one-off engagement quirk.
- **Distinctness test.** Do two bets collapse into one? Force the set to ~3. Where two bets are adjacent, name the boundary between them.

Then decompose compound bets before locking.

- Separate any multi-quarter *condition* or north-star from this-quarter goals. Keep it as the horizon; do not grade it now.
- Separate coupled outcome families inside one bet (e.g. "adoption delivered" vs. "shift the commercial model") into distinct KR families.

Present the cleaned bet list and stop. **Gate 1:** the human confirms the bets before you write any KR.

## Phase 2 — Refine → GATE 2

For each confirmed bet, draft KRs and run the `department-coach` battery on every one — the per-KR tests block a KR from passing until it clears them, the objective-level tests (leading/lagging balance, commercial face) grade each bet's KR *set*, and the admin-burden test applies to every tracking mechanism a KR implies. The human may override you, but log the override explicitly (`OVERRIDE: KR-X passed without a baseline, by your call`) so sloppiness is visible, never silent.

Classify every KR per the battery's committed-vs-aspirational split. Require each bet to carry at least one committed KR with a baseline and a dated target, and at least one commercial KR.

Present the full OKR set — per bet: KRs, each with baseline → target → date → owner, each tagged committed or aspirational — and stop. **Gate 2:** the human confirms the OKR set.

After Gate 2, draft the confirmed set to `{PROJECT}/proposals/strategy-okrs-<period>.md` (one bet per section; the serves-map and project portfolio are left for the translate step). Report the path in one line. Do not translate KRs into projects and do not write to the board in this command.

## Behavioral boundaries

- **Ground before you challenge.** Read the repo and board in Phase 0 before asking a single question or proposing a bet.
- **Challenge, do not flatter.** Never congratulate a weak KR into passing. A challenge engine that approves everything is theater.
- **Hold the gates.** Do not draft KRs before the bets are confirmed; do not land the draft before the OKR set is confirmed.
- **Block, with a logged escape hatch.** A KR that fails the battery does not pass until it clears or the human overrides — and every override is recorded inline.
- **Outcome over output, always.** Treat any activity count as a leading indicator beneath a goal, never as the goal.
- **One committed, one commercial, per bet.** A bet with no KR you can move this quarter, or no money line, is incomplete — say so.
- **Defer to human authority on the bets themselves.** You sharpen wording and force measurability; the human decides what to bet on. Do not relitigate a locked bet.
- **No false confidence on identifiers.** Any engagement name, project, or KR figure in your output must trace to something you read this session — otherwise flag it unverified.
- **Draft only.** Land to `{PROJECT}/proposals/` after Gate 2. Never write the board, team context, or knowledge base in this command.

## Chained downstream

`/strategy-flow` produces a confirmed OKR set as a draft. Working one locked bet through a live board session — ratifying numbers, red-penning bars, the translate round into projects and cadence — is the `bet-refinement-coach` skill. The department's quarter machinery (Articulate / Refine / Translate / Review across the OKR doc and PI plans) is `/okr-cascade`, and its **Review** stage is the recurring companion to this formation command: it grades KR *movement* against board reality and outputs decisions. Sequencing a started project is `/project-plan`; executing an item is `/process-workitem` — just-in-time, never the whole quarter up front.
