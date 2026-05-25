# tests/setup-awow — regression suite for `/setup-awow`

Maintainer-only. Adopters who templated this repo can delete this directory.

**Principle.** Fixtures are self-contained snapshots of a clean installation at a given step — standalone test data, not derived from any live workspace. The suite copies a fixture into a scratch dir, runs the real command prompts against it, and grades the result, so `/test-setup-awow` re-proves the wizard end-to-end as an adopter's installation would experience it. Design rationale: [`meta/proposals/setup-awow-regression-tests.md`](../../meta/proposals/setup-awow-regression-tests.md) and [`meta/proposals/meta-workspace-and-fixture-decoupling.md`](../../meta/proposals/meta-workspace-and-fixture-decoupling.md). Execution mechanics: [`.agents/commands/test-setup-awow.md`](../../.agents/commands/test-setup-awow.md).

## Running

```
> /test-setup-awow              # all scenarios with a script + rubric
> /test-setup-awow clean-clone  # one scenario
> /test-setup-awow --keep       # leave scratch dirs after the run
```

Outcomes: `PASS` (zero `no`), `FAIL` (≥1 `no`), `ABORTED` (Phase 2 didn't actually run). Run files: `/tmp/awow-test-runs/<scenario>-<ts>.json`.

## Layout

```
tests/setup-awow/
├── fixtures/<scenario>/   # workspace state copied into scratch at run start
├── scripts/<scenario>.txt # scripted user replies, one per non-blank/non-comment line
├── rubrics/<scenario>.md  # yes/no questions tagged with the invariant they grade
└── README.md
```

Scenarios are discovered by intersecting `scripts/*.txt` with `rubrics/*.md`; a fixture at `fixtures/<name>/` is then required.

## Scenarios

| Scenario | Fixture state | What it tests |
|---|---|---|
| `clean-clone` | Empty workspace | Step 0 installer-permission gate; wizard halts on `no`. |
| `install-step0-inherited` | `.venv/` + pointer stubs; no `setup-progress.md` | Wizard detects Step 0 inherited; skips installer. |
| `install-step1a-cli` | + `setup-progress.md` (Step 0 ✓) + board reference tree | Phase 1a: detect `gh` surface, accept URL, draft `board.md`. |
| `install-step1b-mode-a` | + Phase 1a draft in `proposals/setup/step-1/board.md` | Phase 1b: section walk in Mode A. |
| `install-step1-gate` | + landed `context/tooling/board.md` | Review-and-adjust gate accepts `proceed`. |
| `install-step2-mission` | Step 1 complete | Mission ask, refuse-if-trivial, proposal-first land. |
| `install-step3-conventions` | Steps 1 & 2 complete | Four REQUIRED conventions drafted and landed. |
| `install-walkthrough` | Same as `install-step0-inherited` | End-to-end Step 0 → Step 3 in one run. |

Per-step scenarios give finer-grained failure signal; the walkthrough is the end-to-end smoke test. Both are intentional.

## Fixture conventions

- `.venv/.gitkeep` + populated `.claude/commands/setup-awow.md` and `.github/prompts/setup-awow.prompt.md` stubs = "Step 0 inherited" (the Step 0 §1 detection fires on these).
- `setup-progress.md` signals which step the scenario starts from.
- `context/tooling/board.md` / `context/team/mission.md` are pre-seeded sample state for scenarios past Step 1 or 2 — frozen, standalone (see the principle above).

If a fixture mis-represents the starting state, update the fixture, not the script.

## Adding a scenario

1. `fixtures/<scenario>/` — starting workspace state.
2. `scripts/<scenario>.txt` — user replies (`#`-prefixed and blank lines skipped).
3. `rubrics/<scenario>.md` — yes/no questions, each tagged with its invariant.

`/test-setup-awow` picks the scenario up automatically.
