# Proposal — regression test framework for `/setup-awow`

**Status:** draft, awaiting review
**Scope:** lock the behaviour of `/setup-awow` so future prompt edits do not regress it. Other commands can adopt the same framework later; this proposal scopes to one command to keep it concrete.

---

## Why

`/setup-awow` is a long, branching, state-dependent wizard. The prompt is iterated frequently. Manual walkthroughs are the only current way to confirm the wizard still asks for permission before running the installer, still shows the full plan on every invocation, still detects an existing MCP before asking for a board URL, etc.

Each walkthrough takes ~1 hour and runs against one fixture (a clean clone). It is not repeatable, not parallelisable, and not run on every prompt edit. The risk: a small wording change silently removes the "ask before running the installer" gate and nobody notices until an adopter loses work.

A regression suite turns the implicit invariants in the prompt into explicit, machine-checkable assertions.

---

## Functional design

### What gets tested

The current `/setup-awow` prompt encodes ~12 load-bearing invariants. Each becomes one assertion:

| # | Invariant | Source (in `.agents/commands/setup-awow.md`) |
|---|---|---|
| 1 | Every invocation lists all 11 steps with ✓ / ⧗ / ☐ status markers, never a step in isolation | "On every invocation" §2 |
| 2 | Wizard resumes at the right step given `setup-progress.md` state | "On every invocation" §1, §5 |
| 3 | Installer (`./setup/install.sh` / `install.ps1`) is never run without explicit user approval | Step 0 §2 |
| 4 | Harness is self-detected ("am I Claude Code or Copilot?"), not inferred from `.claude/` / `.github/` presence | Step 1 Phase 1a §1 |
| 5 | Existing board surface is detected (settings.json, .mcp.json, .vscode/mcp.json, `gh auth status` for GitHub) before asking for a URL | Step 1 Phase 1a §2 |
| 6 | Wizard refuses to proceed past Step 1 without a board URL | Step 1 Phase 1a §3 |
| 7 | Tool family is inferred from URL hostname; unknown host stops with "not supported" | Step 1 Phase 1a §3 |
| 8 | Every artefact is drafted under `proposals/setup/<step>/` before moving to its final location | "On every invocation" §4 |
| 9 | `context/tooling/board.md` contains: tool & wiring (family, URL, `surface: mcp \| gh-cli \| pending`, identifier, verification, harness), state machine, hierarchy, label taxonomy, required fields, team-page conventions, cycles/iterations, divergence-from-reference (Mode B) | Step 1 "Record and complete" §9 |
| 10 | Step 10 enumerates every entry in `.agents/skills/` and surfaces each skill's bake-in assumption + interplay | Step 10 |
| 11 | Non-MCP read/write surface (`gh` CLI) is accepted as a valid Step 1 outcome and recorded as `surface: gh-cli` in `board.md` | Step 1 Phase 1a §2, §4 |
| 12 | URL inference covers both `github.com/.../issues` and `github.com/orgs/<org>/projects/<n>` | Step 1 Phase 1a §3 |
| 13 | Mode-pick rule: count closed issues; ≥10 → Mode B (assess current), <10 → Mode A (set up from reference); surface the count and mode choice to the user before proceeding | Step 1 Phase 1b §5 |
| 14 | Review-and-adjust gate after landing `board.md`: do not silently move on, summarise the landed file, accept `proceed` / `adjust <section>` / `evaluate <section>`, loop until proceed | Step 1 "Record and complete" §10 |

Invariants 11 and 12, flagged as prompt gaps in earlier drafts, are **now encoded in the prompt** (Step 1 was substantially reworked into Phases 1a/1b with `surface: mcp \| gh-cli` recorded explicitly). The dogfood walkthrough is what surfaced them; the prompt update happened during proposal review. Phase 1 of the execution plan collapses to just the `--root` flag, already landed.

Invariants 13 and 14 are also new — they came in with the Phase 1a/1b rework. They are testable structurally: invariant 13 by asserting the wizard's mode-announcement message matches the closed-issue count in the fixture; invariant 14 by asserting the wizard does not advance to Step 2 until the user types `proceed`.

The previous draft included an "MCP write-blocked" invariant. Dropped — exercising it requires either a scoped-down token or a mock failure-mode MCP, and the failure path is not on the critical adoption flow. Manual smoke test once per release is enough.

### The model: dogfood IS the test suite

Earlier drafts treated the dogfood repo as a *source of fixtures* the tests would `cp -R` from. That was overbuilt. The wizard is **structurally board-family-agnostic** — only invariants 7 and 12 (URL inference) and the install snippet pick in Step 1 differ across families. Everything else (full plan, installer permission, proposal-first, board.md fields, harness self-detect, Step 10 skills review) is identical regardless of board.

So: run the regression suite directly against snapshots of `dogfood/` at each step boundary. The `gh` CLI is a real read/write surface — invariants 5/8/9/11 are exercised genuinely, no mocks needed. The handful of cases dogfood does not naturally cover get tiny synthetic fixtures.

### Test inventory

| Test | Mechanism | Invariants exercised |
|---|---|---|
| `dogfood-step0-inherited` | Run `/setup-awow --root dogfood/` against snapshot of `dogfood/` after Step 0 detected the parent repo's `.venv/` | 1, 2, 3 (skip installer) |
| `dogfood-step1a-cli` | Run against snapshot after Phase 1a wired `gh` CLI | 1, 2, 9, 11, 12 |
| `dogfood-step1b-mode-a` | Run against snapshot mid-Phase 1b walking the reference sections | 1, 2, 8, 13 |
| `dogfood-step1-gate` | Run against snapshot just after `board.md` landed | 14 (review-and-adjust gate) |
| `dogfood-step2-mission` | Run against snapshot after mission landed | 1, 2, 8 |
| `dogfood-step3-conventions` | Run against snapshot after conventions drafted | 1, 2, 8 |
| `dogfood-step10-skills-review` | Run against snapshot after all prior steps ✓ | 10 (deferred — blocked on dogfood reaching Step 10) |
| `clean-clone` | Empty workspace, no `.venv/`, no `setup-progress.md` | 1, 3 (asks permission) |
| `linear-mcp-wired` | `dogfood/` + a `.claude/settings.local.json` containing one Linear MCP block | 4, 5 |
| `url-routing` | First-turn-only prompt-resolution tests against hostnames | 6, 7 |

Ten tests covering invariants 1–14. No FastMCP mocks, no per-family install verification (those are static markdown the wizard quotes — see "What this framework does NOT test").

Each `dogfood-step*` test runs in ~30–90s of model time. `url-routing` is a few seconds per case (first-turn only). Total suite: ~6–10 min.

### Assertion layers

Two flavours, applied per assertion:

- **Hard / structural** — regex or tool-call presence over the trace. Cheap, deterministic. Example: "no `Bash` call whose command matches `setup/install\.(sh|ps1)` appears before a user message containing a yes-equivalent." Covers invariants 2, 3, 5, 8, 9, 11.
- **Soft / LLM-judge** — one extra Claude call against the assistant's first message, with a yes/no rubric. Example: "Does the assistant's opening message present all eleven steps with status markers?" Covers invariants 1, 4, 6, 7, 10, 12 — the ones that resist regex.

LLM-judge calls cost money and are themselves non-deterministic, so the design budget is ≤2 per test.

### What this framework does NOT test

- Output **wording quality** — only structural behaviour. Prompt edits that change phrasing without changing behaviour will pass.
- **Snapshot diffs** against the full walkthrough trace. Full-trace diffs are flaky against intended phrasing changes. The walkthrough is the source for *which assertions to write*, not the snapshot itself.
- **Real Linear / Jira / Azure MCP installs.** The wizard quotes install snippets from `context/tooling/boards/<tool>.md`; the wizard never runs them. Snippet correctness is verified by manual smoke test once per release, not per-PR.
- **MCP write-blocked recovery.** Off the critical adoption flow; manual smoke before release.
- The downstream commands (`/refinement-prep`, `/process-workitem`, etc.). They get their own tests later in the same framework.

### Relationship to the dogfood repo

The dogfood repo (`dogfood/` in this repo) plays two roles, both essential:

1. **Live walkthrough — the source of invariants and snapshots.** Watching `/setup-awow` work against `dogfood/` is the cheapest way to discover load-bearing behaviours and to capture realistic mid-walkthrough state. Each step boundary produces a natural snapshot the regression suite consumes.
2. **Test target.** Unlike the earlier "tests live elsewhere, dogfood is upstream" framing — the regression suite runs the wizard *against snapshots of dogfood*. The snapshots travel with the prompt in this repo, so the suite is self-contained for adopters who template the repo.

**Prerequisite — `--root` support.** Dogfood writes artefacts under `dogfood/`, not the repo root (see `dogfood/setup-progress.md` L4–5: *"the wizard prompt … references paths relative to the repo root, this dogfood run lands artefacts under `dogfood/` instead"*). Two reconciliations:

- **(a)** Teach the wizard a `--root <path>` argument so dogfood writes to canonical locations under `dogfood/`, and the snapshot tool captures `dogfood/...` → `tests/snapshots/<step>/...` (rebasing the prefix on the way in).
- **(b)** Drop the `dogfood/` prefix from the dogfood walkthrough entirely (move artefacts to repo root, accept the cross-pollination cost) and snapshot directly.

Pick before authoring the snapshot tool. Option (a) is the longer-lived answer because adopters will eventually want `--root` for their own multi-workspace cases; option (b) is the cheap-and-now answer.

---

## Implementation design

### Directory layout

```
tests/
  setup-awow/
    runner.py                       # the test harness (see below)
    assertions.py                   # shared assertion helpers
    snapshots/
      step0-inherited/              # cp of dogfood/ at this step boundary
      step1-cli/
      step2-mission/
      step3-conventions/
      step10-skills-review/         # deferred — dogfood not yet at Step 10
    fixtures/
      clean-clone/                  # empty workspace; the only fully synthetic one
      linear-mcp-wired/             # dogfood/ + .claude/settings.local.json with Linear MCP
    unit/
      url-routing.py                # first-turn assertions over URL hostnames
    tests.yaml                      # test → snapshot/fixture + script + expects
    README.md
  tools/
    snapshot-fixture.py             # cp dogfood/ → snapshots/<step>/ (with --root rebasing)
```

### Snapshot capture

`tools/snapshot-fixture.py` runs against the live `dogfood/` workspace. After each manual step boundary the maintainer runs:

```bash
uv run python tools/snapshot-fixture.py --step step1-cli
```

It `cp -R dogfood/ tests/setup-awow/snapshots/step1-cli/`. If `--root` (option a above) is adopted, it also rebases path prefixes so the snapshot looks like a repo-root install. Re-runnable: snapshots are overwritten when the underlying dogfood state changes.

### Script + assertion DSL

Each test in `tests.yaml` references a snapshot or fixture, a `script.jsonl` of user turns, and an `expect` block. One JSON object per line in `script.jsonl`:

```jsonl
{"role": "user", "content": "/setup-awow"}
{"role": "user", "content": "yes, go ahead"}
```

A test that should terminate early (e.g. `unknown-board-url` in `url-routing`) provides only the turns up to the expected stop point; the runner asserts the wizard does not request further input.

`expect` blocks declare assertions:

```yaml
hard:
  - name: "lists setup-progress.md before deciding"
    kind: tool_call
    tool: Read
    arg_match: "setup-progress\\.md$"
    order: first

  - name: "no installer run before user approval"
    kind: ordering
    must_precede:
      user_message_matches: "^(yes|y|go|ok)"
    must_follow:
      bash_command_matches: "setup/install\\."

  - name: "board.md drafted to proposals/setup/step-1/"
    kind: file_write
    path_match: "proposals/setup/step-1/board\\.md$"

soft:
  - name: "opening message shows full plan with status markers"
    target: assistant_messages[0]
    rubric: |
      Does this message list all eleven setup steps (0 through 10)
      with a status marker (✓ / ⧗ / ☐ or equivalent) on each, and
      identify which step is being resumed?
    expect: yes
```

Three `kind`s in v1: `tool_call`, `ordering`, `file_write`. Easy to extend.

### Driver

Use `claude -p` in headless mode with `--input-format stream-json` and `--output-format stream-json`. The runner:

1. Copies the snapshot or fixture into a temp dir.
2. Spawns `claude -p` in that dir.
3. Feeds `script.jsonl` lines on stdin, one at a time, waiting for the assistant's stop event between turns.
4. Collects the full JSON stream as the trace.
5. Evaluates the test's `expect` block against the trace.

Why headless `claude -p` over the Agent SDK: zero extra dependency, same prompt resolution path as the user's real invocations, MLflow tracing already wired. The SDK becomes worth it if you need tool-call interception or sandboxed permissions later.

### URL-routing unit tests

`url-routing.py` is a thin harness around `claude -p` that runs only the first turn (the URL paste) and asserts the wizard's response. Cases:

- `https://linear.app/cauchyio/team/CAU` → picks Linear install path (soft assertion)
- `https://github.com/orgs/CauchyIO/projects/3` → picks GitHub Projects path (soft assertion; invariant 12)
- `https://github.com/CauchyIO/awow/issues` → picks GitHub Issues path
- `https://acme.atlassian.net/jira/...` → picks Jira path
- `https://dev.azure.com/...` → picks Azure path
- `https://trello.com/...` → refuses (hard assertion: assistant message contains "not supported", no follow-up question)

No MCP, no fixture state, just the prompt resolution. ~6 cases × 5–10s each = under a minute.

### `gh` in CI

The `dogfood-step1-cli` test inherits dogfood's `gh` CLI surface. In CI: install `gh`, authenticate with a token scoped to a read-only org so writes against the Dogfood project fail loudly. Or run that test only locally / nightly, not per-PR. Open decision (4) below.

### Trace adapter

The runner reuses the trace shape that `awow-usage-coach` and `prompt-skill-analysis` already parse (tool calls, files modified, assistant messages). Same parser, new consumer. Avoids reinventing a trace model.

### Running

```bash
# all tests
uv run python tests/setup-awow/runner.py

# one test, useful while iterating on the prompt
uv run python tests/setup-awow/runner.py --test dogfood-step1-cli --verbose

# write blessed traces (first time only, after a manual walkthrough confirms behaviour)
uv run python tests/setup-awow/runner.py --bless
```

`--bless` is for the first run only — it stores the raw trace alongside each test for later debugging, never as a diff target.

### CI hook

A GitHub Actions workflow at `.github/workflows/setup-awow-tests.yml` runs the suite on any PR that touches `.agents/commands/setup-awow.md` or `.agents/skills/setup-awow/`. Roughly $0.10–$0.30 per run at current rates (small input × eight tests × one LLM-judge call per soft assertion).

Manual local trigger: `uv run python tests/setup-awow/runner.py`.

---

## Plan of attack

Ordered for minimum-viable-loop first:

1. **Prompt updates.** *Done.* `--root` flag added; CLI-only branch and broadened URL inference already in the prompt from the Step 1 Phase-1a/1b rework. ~10 lines net.
2. **`runner.py` + `clean-clone` test.** Proves the driver works and the assertion vocabulary feels right. ~half a day.
3. **`snapshot-fixture.py` + first dogfood snapshot.** Capture `step1a-cli` from the live dogfood state, wire `dogfood-step1a-cli` test against it. ~2 hours.
4. **Remaining dogfood snapshots** — `step0-inherited`, `step1b-mode-a`, `step1-gate`, `step2-mission`, `step3-conventions`. Snapshot as dogfood progresses through them. ~hour each, parallel with the dogfood walkthrough.
5. **`linear-mcp-wired` synthetic fixture + test.** ~hour.
6. **`url-routing` unit tests.** ~hour.
7. **`step10-skills-review`** — blocked on dogfood reaching Step 10. Snapshot once it does. ~half hour after unblock.
8. **CI workflow** — wire to `pull_request` filtered on the prompt paths. ~half hour.
9. **Extend to a second command** (e.g. `/refinement-prep`) — proves the framework is not setup-awow-specific. Out of scope for this proposal.

Total to a green suite (excluding the Step 10 test waiting on dogfood): ~1 focused day plus passive snapshot capture during the dogfood walkthrough.

---

## Open decisions

1. **Headless `claude -p` vs. Agent SDK.** Proposal favours `claude -p` for simplicity. Switch to SDK if Phase 2 reveals it cannot script multi-turn cleanly. *(Probed during Phase 2; no pre-decision needed.)*
2. **LLM-judge model.** Haiku 4.5 should be sufficient for yes/no rubrics. Worth confirming on the first soft assertion.
3. **Per-test API budget guardrail.** Worth adding a hard timeout / token cap per test so a runaway wizard turn does not silently rack up cost. *(Set during Phase 5 CI wiring.)*

**Resolved during review:**

- ~~MCP mocking strategy.~~ No MCP mocks. Dogfood's `gh` CLI is a real read/write surface that exercises invariants 5/8/9/11 genuinely. Linear/Jira/Azure end-to-end paths are not tested — install snippets are static markdown the wizard quotes, and snippet correctness is a manual smoke test before release.
- ~~MCP write-blocked invariant.~~ Dropped from the regression suite. Off the critical adoption flow.
- ~~`--root` support in the wizard.~~ Add `--root <path>` flag to `/setup-awow`; default is the repo root. Maintainer explicitly passes `--root dogfood/` for dogfood runs. Snapshot tool rebases the prefix on capture.
- ~~Prompt updates for invariants 11 (CLI-only) and 12 (GitHub Projects URL).~~ Land first, as PR #1, before any test that locks them in.
- ~~`gh` in CI for `dogfood-step1-cli`.~~ Read-only token in CI; writes fail loudly. Acceptable side-effect profile.
- ~~`tests/` location.~~ Inside this repo at `tests/setup-awow/`. Documented as maintainer-only, alongside `dogfood/` — adopters who template the repo can delete `tests/` the same way they can delete `dogfood/`. Nothing in the adopter flow references it; nothing breaks when it is gone.

---

## Status

Decisions resolved (D3/D4/D6/D7 above). Phase 1 (prompt-iteration PR) unblocked.
