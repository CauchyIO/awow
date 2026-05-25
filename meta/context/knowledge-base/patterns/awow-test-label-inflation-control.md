# `awow-test` label — board inflation control

## Problem

Repeatedly running awow's downstream commands (`/refinement-prep`, `/process-workitem`, `/board-skill`) against the awow repo for prompt iteration creates issues on `CauchyIO/awow`. Without a discipline, the board accumulates test cruft that obscures real backlog and dilutes any cycle-time metrics derived from the board.

## Pattern

Every issue generated during a test walkthrough carries the `awow-test` GitHub label. This makes it:

1. **Filterable:** `gh issue list -R CauchyIO/awow -l awow-test --state open`.
2. **Bulk-closeable:** `gh issue list … --json number -q '.[].number' | xargs -I{} gh issue close -R CauchyIO/awow {}`.
3. **Distinguishable** from real backlog issues at a glance, both in the GitHub UI and via `gh` queries.

`tools/reset-adopter-state.py` (the engine behind `/awow-reset`) bulk-closes `awow-test`-labelled issues on the repo's `origin` remote as part of its default routine. This makes the maintainer's prompt-iteration loop hygienic by default — re-running `/awow-reset` between iterations leaves no walkthrough cruft.

## Trade-offs

- **Discipline lives in the prompts.** Any command that creates an issue during a test walkthrough must add the label. The convention is codified in `meta/context/team/conventions/REQUIRED/labels.md`.
- **Repo-scoped, not project-scoped.** The `awow-test` label is on the *repo*, but the canonical *project* is `awow` (#3). An issue can be labelled `awow-test` without being on the project; the reverse is also possible. The discipline is `label first, project second`.
- **Escalation path:** if a single iteration produces hundreds of issues, dated scratch projects (`awow — 2026-05`, etc.) with project-level archive become the better lever. Label-only is the day-one default.
- **Adopter safety:** adopters cloning the awow template inherit the `awow-test`-label cleanup path in `tools/reset-adopter-state.py`. It is a safe no-op for them — no `awow-test`-labelled issues exist on their fork unless they choose the same pattern.
