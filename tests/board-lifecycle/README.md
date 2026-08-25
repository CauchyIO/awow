# tests/board-lifecycle/

Evaluates `/board-lifecycle` (AWO-269) against a real board fixture — a
`board.md` lifecycle contract plus a dated project-inventory snapshot, the same
evidence a real sweep produces.

## Scenario: sweep-and-plan

Eight projects across the three default shapes:

| Project | Shape | Horizon | Trap |
| --- | --- | --- | --- |
| north-star-portal | engagement | 2099-06-30 (future) | stale `last_activity` (2026-02-01) — **alive despite quiet** |
| harbor-rollout | engagement | 2026-07-01 (passed) | fresh `last_activity` (yesterday-ish) — **dead despite churn** |
| spring-campaign | campaign | 2026-06-15 (passed) | — |
| autumn-campaign | campaign | 2099-09-30 (future) | — |
| billing-platform | system | 2099-03-31 (future review) | — |
| legacy-intake | system | *(missing)* | missing horizon |
| drift-experiment | *(no shape label)* | 2099-01-01 | missing shape |
| ops-dashboard | system | 2099-12-31 | healthy |

The script invokes `/board-lifecycle --snapshot board-snapshots/2026-08-20-projects.json`,
then **declines** the exception plan at the gate.

## Invariants

1. **Read-only until the gate, and a declined gate writes nothing** — the
   fixture is byte-identical after the run (post-checks).
2. **Horizon, never timestamp** — `harbor-rollout` classifies `expired`
   (fresh activity ignored); `north-star-portal` classifies `healthy`
   (stale activity ignored). Graded by rubric from the classification table.
3. **Missing horizon and missing shape are exceptions**, not skipped rows.
4. **No auto-close** appears anywhere in the plan.
