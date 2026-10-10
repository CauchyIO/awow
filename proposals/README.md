# proposals/

awow's own product proposals — drafts en route to GitHub issues, or records of decisions that have already shipped — sharing this directory with the wizard's gitignored `proposals/setup/` landing area. Adopters: these are awow-internal records; delete them freely, your own drafts land under `proposals/setup/`. Implementation plans that executed accepted proposals are archived under [`plans/`](plans/).

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
| [word-export-design](word-export-design.md) | **Draft** (2026-09-04) | Word (`.docx`) export target in `/artifact` via pandoc plus a reference doc `/design-system` registers; render mechanics extracted into the `artifact-render` skill (the deferred §3.7 of design-system-capability). CAU-1525; plan at [plans/2026-09-04-word-export.md](plans/2026-09-04-word-export.md). |
| [office-ingest-design](office-ingest-design.md) | **Draft** (2026-09-04) | `.docx`/`.pptx`/`.xlsx` inputs read through provenance-stamped markitdown sidecars beside the source (`office-ingest` skill), wired into refinement-prep, process-transcript, strategy-flow. CAU-1526; plan at [plans/2026-09-04-office-ingest.md](plans/2026-09-04-office-ingest.md). |
| [jit-context](jit-context.md) | **Draft** (2026-08-26) | Fill-on-first-need contract: absence as the marker, `/setup-awow` shrinks to install + board + registration, `company/` pruned. CAU-1422; the reconciliation criterion for the PR #73/#76 overlap, both absorbed into its PR. |
| [setup-awow-preflight](setup-awow-preflight.md) | **Landed** (PR #80, 2026-08-26; amended 2026-08-30) | Read-only preflight (git/repo/board/gh/harness, pointers per miss) + board-MCP confirmation in Step 1a, reconciled per [jit-context](jit-context.md): explicit pick only on ambiguity; verification is identity-bearing (`board-url:` recorded, the read must return the named board). Spec: [setup-awow-preflight-design](setup-awow-preflight-design.md); CAU-1332. |
| [invoker-topology-and-board-plan](invoker-topology-and-board-plan.md) | **Accepted** (in build) | Hat-aware setup, invoker profile + ladder rungs, board plan gate. AWO-204/205/206, stacked on PR #44; plan at [plans/2026-08-18](plans/2026-08-18-invoker-topology-and-board-plan.md). |
| [meta-workspace-and-fixture-decoupling](meta-workspace-and-fixture-decoupling.md) | **Landed** | `dogfood/` → `meta/`, test fixtures decoupled (`feature/dry_run_awow`). `meta/` itself since dissolved: proposals merged here, workspace context frozen at `tests/fixtures/fikkert/_seed/`. |
| [pi-codex-harness-support](pi-codex-harness-support.md) | **Superseded** | Reconciled into hub-and-spoke-design §7/§10; tracked as WI-5. |
| [architecture-aware-development](architecture-aware-development.md) | **Proposed** | v2, incorporates an adversarial design review. |
| [strategy-rollup-capability](strategy-rollup-capability.md) | **Draft** | Awaiting approval (2026-07-08). |
| [marketplace-distribution](marketplace-distribution.md) | **Reference** | Distribution status per harness (self-hosted live; official tiers gated on portal applications). |
| [design-system-capability](design-system-capability.md) | **Landed** | Approved; Phases 1–3 implemented (render skill, §3.7, deferred). |
| [board-as-afterthought](board-as-afterthought.md) | **Draft** | Awaiting approval (2026-05-30). |
| [archetypes-board-anchoring](archetypes-board-anchoring.md) | **Superseded** | Rolled back to generic reference (2026-05-25). |
| [session-board-correlation](session-board-correlation.md) | **Landed** | `session-correlation` skill + footer rule + `tools/session_footer_hook.py`. |
| [setup-awow-regression-tests](setup-awow-regression-tests.md) | **Landed** | `tests/setup-awow/` suite, run via `/test-awow setup-awow`. |
| [plugin-distribution](plugin-distribution.md) | **Draft** | Second adoption path (Claude Code plugin). Awaiting review — candidate for **Superseded** by hub-and-spoke-adoption. |
| [hub-and-spoke-adoption](hub-and-spoke-adoption.md) | **Draft** (WI-1 in build) | Adopt Martijn's two-path hub-and-spoke model: plugin machinery + hub context, connector per project. Work items WI-0..4 + decisions D1–D6 await review. |
| [hub-and-spoke-design](hub-and-spoke-design.md) | **Accepted design** (MVP validated 5/5) | Concrete design from the 2026-07-12 maintainer session: linear as hub, Path A spokes (~4 committed files), identity-based hub resolution, neutral-token path sweep, hub write path, Claude Code/Codex/Pi delivery, MVP validation gate, WI-0..8. |
| [canonical-knowledge-source-routing-design](canonical-knowledge-source-routing-design.md) | **Accepted** (Markdown-first MVP implemented) | Reference-before-capture routing to repository/OKF, SharePoint, vector-backed, and other canonical sources without copying or write-back. |
| [board-noise-pruning](board-noise-pruning.md) | **Draft** (solutioning) | Comparison-mode; pick an approach before writing the issue. |
| [superpowers-integration-shape](superpowers-integration-shape.md) | **Draft** | Ready to file as a GitHub issue once the AC is confirmed. |
| [eval-baseline-and-prompt-cleanup](eval-baseline-and-prompt-cleanup.md) | **Draft** (Phase 1 built, awaiting review) | Dual-witness `/test-awow` runner (checks + blind judge, `indeterminate` verdicts), per-scenario `pre()`/`post()` checks, `tools/validate-evals.py`. Phases 2–4 (new suites, prompt trims, cleanup) still due. |
| [shared-activity-collection-lenses](shared-activity-collection-lenses.md) | **Draft** (built, awaiting review) | Shared gather (`activity-collection.md`) + `/daily-routine` (one gather → overview + KB candidates) + `/daily-digest` & `/kb-mine` standalone lenses. |
| [kb-capture-synthesize-spine](kb-capture-synthesize-spine.md) | **Draft** (built, awaiting review) | Committed `context/kb-inbox/` + tunable `mining-policy.md` + gated `synthesis.md` drain, wired into mining/`/daily-routine`/`/setup-awow` Step 6 — the awow-portable half of linear's KB spine. Phase 4 (feeders, autonomous drain, tuning) deferred. |
| [context-resolution](context-resolution.md) | **Draft** | Which installation, which board: repo-bounded discovery walk + four-rung board ladder + `board.md` index form. Awaiting review (2026-07-30). |
| [maintainer-meta-instructions](maintainer-meta-instructions.md) | **Parked** (2026-05-25) | Guide-sync tweak; revisit if the prompt catalogue drifts. |

`setup/` holds the `/setup-awow` wizard's per-step drafts — working artefacts, not tracked here.

## Retention

A **Landed** proposal can be deleted once its record (skill, code, issue, PR) is durable — the version-controlled implementation is the source of truth, not the draft. Keep **Superseded** and **Parked** ones briefly for context; prune at retrospectives.
