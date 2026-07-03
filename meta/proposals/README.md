# meta/proposals/

awow's own product proposals — drafts en route to GitHub issues, or records of decisions that have already shipped. This is awow applied to itself: the parallel of the template's top-level `proposals/`, but holding real awow work.

## How status works

Every proposal carries a `**Status:**` line near the top, drawn from the controlled vocabulary below. This README aggregates them so you can see at a glance what has passed and what is still due, instead of reading every file.

| Status | Meaning |
|---|---|
| **Draft** | Being written or awaiting review. Still due. |
| **Landed** | Implemented; the skill / code / PR is the record (linked in the status line). Candidate for pruning. |
| **Parked** | Deprioritised, with a date and a revisit condition. |
| **Superseded** | Overtaken by another proposal or by reality (linked). |

When a proposal's state changes, update its `**Status:**` line *and* the row below — keep the two in sync.

## Index

| Proposal | Status | Outcome / next step |
|---|---|---|
| [meta-workspace-and-fixture-decoupling](meta-workspace-and-fixture-decoupling.md) | **Landed** | `dogfood/` → `meta/`, test fixtures decoupled (`feature/dry_run_awow`). |
| [session-board-correlation](session-board-correlation.md) | **Landed** | `session-correlation` skill + footer rule + `tools/session_footer_hook.py`. |
| [setup-awow-regression-tests](setup-awow-regression-tests.md) | **Landed** | `tests/setup-awow/` suite + `/test-setup-awow`. |
| [plugin-distribution](plugin-distribution.md) | **Draft** | Second adoption path (Claude Code plugin). Awaiting review. |
| [board-noise-pruning](board-noise-pruning.md) | **Draft** (solutioning) | Comparison-mode; pick an approach before writing the issue. |
| [superpowers-integration-shape](superpowers-integration-shape.md) | **Draft** | Ready to file as a GitHub issue once the AC is confirmed. |
| [eval-baseline-and-prompt-cleanup](eval-baseline-and-prompt-cleanup.md) | **Draft** (Phase 1 built, awaiting review) | Dual-witness `/test-awow` runner (checks + blind judge, `indeterminate` verdicts), per-scenario `pre()`/`post()` checks, `tools/validate-evals.py`. Phases 2–4 (new suites, prompt trims, cleanup) still due. |
| [maintainer-meta-instructions](maintainer-meta-instructions.md) | **Parked** (2026-05-25) | Guide-sync tweak; revisit if the prompt catalogue drifts. |

`setup/` holds the `/setup-awow` wizard's per-step drafts — working artefacts, not tracked here.

## Retention

A **Landed** proposal can be deleted once its record (skill, code, issue, PR) is durable — the version-controlled implementation is the source of truth, not the draft. Keep **Superseded** and **Parked** ones briefly for context; prune at retrospectives.
