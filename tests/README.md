# tests/ — eval suites for awow's command prompts

Maintainer-only. Adopters who templated this repo can delete this directory.

Each suite evaluates one command prompt with two independent witnesses, composed into a `pass` / `fail` / `indeterminate` verdict by `/test-awow`:

1. **Deterministic checks** — `tests/<suite>/checks/<scenario>.sh` defines `pre()` (is the fixture intact?) and `post()` (did the mechanical facts land?), executed by the shared driver `tests/run-checks.sh` with the verb vocabulary from `tests/checks-prelude.sh`.
2. **A blind judge** — an agent that grades the scenario's rubric from an evidence bundle (agent turns, tool calls, post-run state) without seeing the runner's reasoning or the check results.

`indeterminate` is a first-class outcome meaning "this run could not measure the prompt" — broken fixture, broken check, or the command never actually ran. It is deliberately distinct from a graded `fail`. Methodology rationale: [`meta/proposals/eval-baseline-and-prompt-cleanup.md`](../meta/proposals/eval-baseline-and-prompt-cleanup.md).

## Layout

```
tests/
├── run-checks.sh            # shared check driver (executable — it is spawned)
├── checks-prelude.sh        # check verbs (not executable — it is sourced)
└── <suite>/
    ├── suite.md             # frontmatter `command:` names the prompt under test
    ├── fixtures/<scenario>/ # workspace state copied into scratch at run start
    ├── scripts/<scenario>.txt
    ├── rubrics/<scenario>.md
    ├── checks/<scenario>.sh # pre() + post() only (not executable — sourced)
    └── README.md
```

The exec-bit asymmetry is load-bearing and validated. Driver exit codes: `0` all checks passed, `1` assertion failed (a graded result), `127` broken check (never graded as a fail — it composes to `indeterminate`).

## Running

```
> /test-awow                       # single suite auto-selected
> /test-awow setup-awow            # one suite, all scenarios
> /test-awow setup-awow clean-clone --keep
```

Static validation (CI-safe, no LLM, no credentials):

```
python tools/validate-evals.py
```

## Adding a suite

1. `tests/<suite>/suite.md` with `command: <name>` frontmatter.
2. Scenarios per the four-file unit above (fixture, script, rubric, checks).
3. `python tools/validate-evals.py` until green — it enforces the structure so `/test-awow` never discovers a half-wired scenario.

Keep rubric questions and checks belt-and-braces: assert a mechanical fact in **both** the rubric (for the judge) and `post()` (for the driver). The composer surfaces any disagreement between the two witnesses as a triage entry — that disagreement is signal, not noise.
