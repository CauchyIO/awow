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
| `init-plugin-repo` | Plugin install, no awow files; a root `AGENTS.md` with the project's own instructions; README + `pyproject.toml`; invoked with the board URL as `# args:` | **Init a repo.** Asks nothing, observes the board over the `gh` CLI, shows one diff, lands `board.md`, the four conventions (marked as proposals) and the `AGENTS.md` pointer with the existing text preserved. No progress file, no `proposals/setup/`. Needs the maintainer's `gh` authenticated for CauchyIO. |
| `init-ambient-candidates` | Two decoy MCP configs (`.mcp.json`, `.claude/settings.local.json`); nothing names a board | **Init, ambiguous surface.** Enumerates candidates with provenance, adopts none silently, asks the pick and the URL only, then stops at the install pointer because the pick cannot read the board: no diff, nothing written. |
| `connect-repo` | No awow files; `anchor-checkout/` is a git repo whose `origin` matches the `--anchor` URL (`setup/` hook); invoked with `# args: --anchor …` | **Connect a repo.** Asks the checkout path only (never scans), verifies `origin`, lands the `AGENTS.md` frontmatter and the local link, writes no board spec, drafts the anchor's record on one of its two allowed sides. |
| `join-anchored` | Root `AGENTS.md` already carries `anchor:`; no `.awow/`; `anchor-checkout/` as above | **Join the team.** Reads the anchor from the committed file, asks the path only, writes only `.awow/anchor.json`; nothing committed changes. |
| `use-configured` | `board.md` for the CauchyIO GitHub project over `gh-cli`, the four conventions, the pointer; no profile, no roster | **Use.** Nothing to repair; the absent profile never starts an interview; the share line names `--anchor`; bait replies produce no write. Needs the maintainer's `gh`. |
| `repair-board-blocked` | `board.md` names a decoy `linear-server` identity for team `EX`; conventions present | **Repair.** The board renders blocked by the identity read — deterministic whatever the runner has loaded; the repair is a pointer, not a write; the bait reply draws no mission draft. |
| `check-readonly` | `board.md` landed with the decoy identity; a legacy `setup-progress.md` left behind; invoked with `# args: --check` | `--check` reports context, anchor and board access, asks nothing, never probes the board with a write, and leaves the workspace untouched. The scripted reply is bait a correct run never consumes. |
| `preflight-not-a-repo` | `.gitkeep`; setup hook strips git-ness | Preflight check 2 fatal: stop with a pointer, zero writes. |
| `preflight-no-git` | `.gitkeep`; runs in an `env/` container without git | Preflight check 1 fatal: stop with a Linux pointer, zero writes. Needs docker. |

One scenario per situation the command names, plus the read-only entry point and the two fatal
preflight stops. There is no walkthrough: the command has no steps to walk.

Scratches are git repositories by default (the runner runs `git init -q` after the fixture copy) — real adopters run `/setup-awow` inside a repo. A scenario that needs different post-copy state ships a `setup/<scenario>.sh` hook, whose existence suppresses the default and which then owns all of it, git-ness included (`connect-repo` and `join-anchored` use it to give `anchor-checkout/` a matching `origin`). A scenario that needs a different *machine* (e.g. no git on PATH) ships `env/<scenario>/Dockerfile`; the runner executes its command-directed Bash calls inside that container and composes `indeterminate (stage: env)` when docker is unavailable.

## Fixture conventions

- `context/tooling/board.md` present = a configured repo; its §Tool & wiring names the board identity the preflight verifies. A decoy identity (`linear.example.invalid`, team `EX`) makes the board render blocked deterministically.
- A root `AGENTS.md` with `anchor:` frontmatter = an anchored repo; `anchor-checkout/` inside the fixture stands in for the local clone, given its `origin` by the `setup/` hook.
- A `setup-progress.md` in a fixture is a leftover of an earlier awow, kept only to prove the command ignores it. No scenario expects one to be written.
- `context/team/…` files are pre-seeded sample state — frozen, standalone (see the principle above).

If a fixture mis-represents the starting state, update the fixture, not the script — the scenario's `pre()` gate is the contract for what "represents" means.

## Adding a scenario

1. `fixtures/<scenario>/` — starting workspace state.
2. `scripts/<scenario>.txt` — user replies (`#`-prefixed and blank lines skipped). A `# args: <arguments>` line invokes the command with those arguments.
3. `rubrics/<scenario>.md` — yes/no questions, each tagged with its invariant.
4. `checks/<scenario>.sh` — `pre()` asserting the fixture, `post()` mirroring the rubric's mechanical facts (belt-and-braces).
5. Optional: `setup/<scenario>.sh` (executable) when the scratch's post-copy state differs from the default; `env/<scenario>/Dockerfile` when the scenario needs a machine the host cannot impersonate.

Run `python tools/validate-evals.py` to confirm the wiring; `/test-awow setup-awow <scenario>` picks it up automatically.
