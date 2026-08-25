# tests/setup-awow — regression suite for `/setup-awow`

Maintainer-only. Adopters who templated this repo can delete this directory.

**Principle.** Fixtures are self-contained snapshots of a clean installation at a given step — standalone test data, not derived from any live workspace. The suite copies a fixture into a scratch dir, runs the real command prompts against it, and grades the result with two independent witnesses (deterministic checks + a blind judge), so `/test-awow setup-awow` re-proves the wizard end-to-end as an adopter's installation would experience it. Design rationale: [`proposals/setup-awow-regression-tests.md`](../../proposals/setup-awow-regression-tests.md), [`proposals/meta-workspace-and-fixture-decoupling.md`](../../proposals/meta-workspace-and-fixture-decoupling.md), and [`proposals/eval-baseline-and-prompt-cleanup.md`](../../proposals/eval-baseline-and-prompt-cleanup.md). Execution mechanics: [`.agents/commands/test-awow.md`](../../.agents/commands/test-awow.md); suite-wide conventions: [`../README.md`](../README.md).

## Running

```
> /test-awow setup-awow               # all scenarios with a script + rubric
> /test-awow setup-awow clean-clone   # one scenario
> /test-awow setup-awow --keep        # leave scratch dirs after the run
```

Outcomes: `pass` (judge has zero `no` AND every post-check passed), `fail` (either witness objects), `indeterminate` (the run could not be graded: broken fixture, broken check, no actual execution, or no judge verdict — the run file's `stage` names which). Run files: `/tmp/awow-test-runs/<suite>-<scenario>-<ts>.json` (schema 2).

## Layout

```
tests/setup-awow/
├── suite.md               # command: setup-awow — what /test-awow executes
├── fixtures/<scenario>/   # workspace state copied into scratch at run start
├── scripts/<scenario>.txt # scripted user replies, one per non-blank/non-comment line
├── rubrics/<scenario>.md  # yes/no questions tagged with the invariant they grade
├── checks/<scenario>.sh   # pre() fixture gate + post() deterministic assertions
└── README.md
```

Scenarios are discovered by intersecting `scripts/*.txt` with `rubrics/*.md`; a fixture at `fixtures/<name>/` and a checks file at `checks/<name>.sh` are then required (`tools/validate-evals.py` enforces this statically).

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
| `preflight-no-git` | `.gitkeep`; runs in an `env/` container without git | Preflight check 1 fatal: stop with a Linux pointer, zero writes. Needs docker. |
| `preflight-not-a-repo` | `.gitkeep`; setup hook strips git-ness | Preflight check 2 fatal: stop with a pointer, zero writes. |
| `preflight-board-blocked` | Step 1a done with a decoy `board-mcp:` identity | Preflight board blocked: repair pointer, board steps gated, wizard proceeds to Step 2. |
| `preflight-ambient-unconfirmed` | Two decoy ambient MCP configs; Step 1a unstarted | Never-silently-adopt: enumerate with provenance, explicit pick, identity-only record, pending verification. |

Per-step scenarios give finer-grained failure signal; the walkthrough is the end-to-end smoke test. Both are intentional.

Scratches are git repositories by default (the runner runs `git init -q` after the fixture copy) — real adopters run `/setup-awow` inside a repo. A scenario that needs different post-copy state ships a `setup/<scenario>.sh` hook, whose existence suppresses the default and which then owns all of it, git-ness included. A scenario that needs a different *machine* (e.g. no git on PATH) ships `env/<scenario>/Dockerfile`; the runner executes its command-directed Bash calls inside that container and composes `indeterminate (stage: env)` when docker is unavailable.

## Fixture conventions

- `.venv/.gitkeep` + populated `.claude/commands/setup-awow.md` and `.github/prompts/setup-awow.prompt.md` stubs = "Step 0 inherited" (the Step 0 §1 detection fires on these). The `.venv/` markers are explicitly re-included in `.gitignore` — they are test data, not real virtualenvs; if `pre()` fails on a fresh clone, check that re-include first.
- `setup-progress.md` signals which step the scenario starts from.
- `context/tooling/board.md` / `context/team/mission.md` are pre-seeded sample state for scenarios past Step 1 or 2 — frozen, standalone (see the principle above).

If a fixture mis-represents the starting state, update the fixture, not the script — the scenario's `pre()` gate is the contract for what "represents" means.

## Adding a scenario

1. `fixtures/<scenario>/` — starting workspace state.
2. `scripts/<scenario>.txt` — user replies (`#`-prefixed and blank lines skipped).
3. `rubrics/<scenario>.md` — yes/no questions, each tagged with its invariant.
4. `checks/<scenario>.sh` — `pre()` asserting the fixture, `post()` mirroring the rubric's mechanical facts (belt-and-braces).
5. Optional: `setup/<scenario>.sh` (executable) when the scratch's post-copy state differs from the default; `env/<scenario>/Dockerfile` when the scenario needs a machine the host cannot impersonate.

Run `python tools/validate-evals.py` to confirm the wiring; `/test-awow setup-awow <scenario>` picks it up automatically.
