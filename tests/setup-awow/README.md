# tests/setup-awow — regression suite for `/setup-awow`

Maintainer-only. Adopters who templated this repo can delete this directory; nothing else in awow references it.

The design lives in [`proposals/setup-awow-regression-tests.md`](../../proposals/setup-awow-regression-tests.md). This README only covers how to run the suite.

## Running the suite

In any Claude Code session at the repo root:

```
> /test-setup-awow
```

Runs every scenario that has both a script and a rubric. For a single scenario:

```
> /test-setup-awow clean-clone
```

Add `--keep` if you want to inspect scratch workspaces after the run finishes.

## What the command does, per scenario

Six explicit phases, each printing its own marker line:

1. **Scratch setup** — `mkdir /tmp/awow-test-<scenario>-<ts>/` + `cp -R fixtures/<scenario>/.` into it.
2. **Wizard execution (mandatory, visible)** — reads `.agents/commands/setup-awow.md`, then walks the wizard against `$SCRATCH` for real (real `Read`, `Write`, `Bash`). At each "ask the user" point, the agent must produce a delimited `--- WIZARD TURN N ---` block in its visible output and consume the next script line as the reply.
3. **State inspection** — `ls -laR $SCRATCH` to capture the ground-truth filesystem state.
4. **Grade** — reads the rubric, answers each question yes/no/n/a with evidence pointing to (a) a specific WIZARD TURN block, (b) a specific tool call, or (c) a specific Phase 3 ls line.
5. **Self-check and write run file** — counts the WIZARD TURN blocks. If zero, writes an ABORTED run file (the wizard wasn't actually executed). Otherwise writes the full graded run file to `/tmp/awow-test-runs/<scenario>-<ts>.json`.
6. **Cleanup** — `rm -rf $SCRATCH` (unless `--keep`).

The mandatory-visible-wizard-output rule plus the Phase 5 self-check is what prevents the agent from short-circuiting the run by self-attesting rubric answers.

## End-of-suite summary

```
clean-clone: walked to Step 0 — installer declined; 8 yes / 0 no / 0 n/a → PASS
OVERALL: 1/1 scenarios pass
```

`PASS` = zero `no`. `FAIL` = at least one `no`. `ABORTED` = Phase 2 produced no wizard execution; the run file records this and skips grading.

## Scenarios

| Scenario | Fixture state | What it tests |
|---|---|---|
| `clean-clone` | Empty workspace | Step 0 installer-permission gate; the wizard halts on `no`. |
| `dogfood-step0-inherited` | `.venv/` + populated pointer stubs; no `setup-progress.md` | Wizard detects Step 0 already done (inherited) and advances to Step 1 without running the installer. |
| `dogfood-step1a-cli` | Above + `setup-progress.md` (Step 0 ✓) + `context/tooling/boards/github-issues/` reference tree | Phase 1a: detect existing `gh` surface, accept the URL, draft `board.md`. |
| `dogfood-step1b-mode-a` | Above + Phase 1a section drafted in `proposals/setup/step-1/board.md` | Phase 1b: walk reference sections in Mode A, each section appended to the draft. |
| `dogfood-step1-gate` | Above + landed `context/tooling/board.md` | Review-and-adjust gate accepts `proceed`. |
| `dogfood-step2-mission` | Step 1 complete (landed `board.md`) | Mission ask, refuse-if-trivial, proposal-first land. |
| `dogfood-step3-conventions` | Steps 1 & 2 complete (board.md + mission.md) | Four REQUIRED conventions drafted and landed in Guide mode. |
| `dogfood-walkthrough` | Same as `dogfood-step0-inherited` (empty + .venv/ + stubs + board references) | End-to-end from Step 0 through Step 3 in one run; covers every invariant the per-step scenarios cover, in one walk. |

## Layout

```
tests/setup-awow/
├── fixtures/<scenario>/       # workspace state copied into scratch at start of each run
├── scripts/<scenario>.txt     # scripted user replies, one per non-blank/non-comment line
├── rubrics/<scenario>.md      # behavioural + tool-call + state yes/no questions
└── README.md
```

Run files write to `/tmp/awow-test-runs/<scenario>-<ts>.json` — out of the repo entirely, since they are transient.

## Fixture conventions

- **`.venv/.gitkeep`** + populated `.claude/commands/setup-awow.md` and `.github/prompts/setup-awow.prompt.md` stubs represent "Step 0 inherited from a parent repo." The wizard's Step 0 §1 detection fires on these.
- **`context/tooling/boards/github-issues/`** mirrors the live awow tree — copied at fixture creation, so the wizard's Phase 1a `Read context/tooling/boards/<tool>/reference/mcp.md` and Phase 1b section walk find the files.
- **`setup-progress.md`** signals which step the scenario starts from. The wizard reads it on every invocation and resumes accordingly.
- **`context/tooling/board.md` / `context/team/mission.md`** are pre-seeded (copied from `dogfood/`) for scenarios that start past Step 1 or Step 2.

If a scenario's fixture turns out to mis-represent the starting state (the wizard takes an unexpected branch and the rubric fails for the wrong reason), update the fixture rather than the script.

## Adding a new scenario

1. Add `fixtures/<scenario>/` with the workspace state the wizard should start from.
2. Write the user replies as plain lines in `scripts/<scenario>.txt`. Lines starting with `#` and blank lines are comments and skipped.
3. Author `rubrics/<scenario>.md` with yes/no questions covering wizard behaviour and post-run state, each tagged with the invariant number it grades.
4. Update the test inventory in `proposals/setup-awow-regression-tests.md`.

`/test-setup-awow` picks up new scenarios automatically.
