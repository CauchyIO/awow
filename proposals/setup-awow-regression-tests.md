# Proposal — regression test framework for `/setup-awow`

**Status:** Landed — `tests/setup-awow/` suite and `/test-setup-awow` command shipped.
**Scope:** lock the behaviour of `/setup-awow` so future prompt edits do not regress it. Other commands can adopt the same framework later; this proposal scopes to one command to keep it concrete.

---

## Why

`/setup-awow` is a long, branching, state-dependent wizard. The prompt is iterated frequently. Manual walkthroughs are the only current way to confirm the wizard still asks for permission before running the installer, still shows the full plan on every invocation, still detects an existing surface before asking for a URL, etc.

Each walkthrough takes ~1 hour and runs against one fixture (a clean clone). It is not repeatable, not parallelisable, and the grading is informal ("did it feel right?"). The risk: a small wording change silently removes the "ask before running the installer" gate and nobody notices until an adopter loses work.

A regression suite turns the implicit invariants in the prompt into explicit, machine-checkable assertions. It does **not** automate the execution — the maintainer still walks each scenario in a Claude Code session — but it makes the grading deterministic.

---

## Functional design

### Constraint that shapes the design

The maintainer does **not** have an Anthropic API key or a Claude Code subscription. Every test must run inside an interactive Claude Code session the maintainer is already in. No `claude -p`, no programmatic invocation, no API charges. This rules out headless drivers and CI-triggered LLM judges and pushes the design toward "human drives the run, machine grades the result."

### What gets tested

The current `/setup-awow` prompt encodes 14 load-bearing invariants:

| # | Invariant | Source (in `.agents/commands/setup-awow.md`) |
|---|---|---|
| 1 | Every invocation lists all 10 steps with ✓ / ⧗ / ☐ status markers, never a step in isolation | "On every invocation" §2 |
| 2 | Wizard resumes at the right step given `setup-progress.md` state | "On every invocation" §1, §5 |
| 3 | Installer (`./setup/install.sh` / `install.ps1`) is never run without explicit user approval | Step 0 §2 |
| 4 | Harness is self-detected ("am I Claude Code or Copilot?"), not inferred from `.claude/` / `.github/` presence | Step 1 Phase 1a §1 |
| 5 | Existing board surface is detected (settings.json, .mcp.json, .vscode/mcp.json, `gh auth status` for GitHub) before asking for a URL | Step 1 Phase 1a §2 |
| 6 | Wizard refuses to proceed past Step 1 without a board URL | Step 1 Phase 1a §3 |
| 7 | Tool family is inferred from URL hostname; unknown host stops with "not supported" | Step 1 Phase 1a §3 |
| 8 | Every artefact is drafted under `proposals/setup/<step>/` before moving to its final location | "On every invocation" §4 |
| 9 | `context/tooling/board.md` contains: tool & wiring, state machine, hierarchy, label taxonomy, required fields, team-page conventions, cycles/iterations, divergence-from-reference (Mode B) | Step 1 "Record and complete" §9 |
| 10 | Step 9 (skills review) enumerates every entry in `.agents/skills/` and surfaces each skill's bake-in assumption + interplay | Step 9 |
| 11 | Non-MCP read/write surface (`gh` CLI) is accepted as a valid Step 1 outcome and recorded as `surface: gh-cli` in `board.md` | Step 1 Phase 1a §2, §4 |
| 12 | URL inference covers both `github.com/.../issues` and `github.com/orgs/<org>/projects/<n>` | Step 1 Phase 1a §3 |
| 13 | Mode-pick rule: count closed issues; ≥10 → Mode B, <10 → Mode A; surface the count and mode choice to the user before proceeding | Step 1 Phase 1b §5 |
| 14 | Review-and-adjust gate after landing `board.md`: do not silently move on, accept `proceed` / `adjust <section>` / `evaluate <section>`, loop until proceed | Step 1 "Record and complete" §10 |

Earlier drafts included an "MCP write-blocked" invariant. Dropped — exercising it requires either a scoped-down token or a mock failure-mode MCP, and the failure path is not on the critical adoption flow. Manual smoke test once per release is enough.

### Execution model: real execution against scratch, one command

The maintainer stays in their current Claude Code session and types one slash command:

```
> /test-setup-awow             # runs every scenario
> /test-setup-awow clean-clone # runs just one
> /test-setup-awow --keep      # keep scratch dirs around for inspection
```

The command discovers scenarios by listing `tests/setup-awow/scripts/` ∩ `tests/setup-awow/rubrics/`. Per scenario:

1. **Set up scratch.** Bash: `mkdir -p /tmp/awow-test-<scenario>-<ts>/ && cp -R tests/setup-awow/fixtures/<scenario>/. /tmp/awow-test-<scenario>-<ts>/`. The fixture seeds the workspace state the wizard would otherwise be told to start from.
2. **Run the wizard for real.** Read `.agents/commands/setup-awow.md` and follow it **as if invoked with `--root <scratch>`**. Every path resolves to `<scratch>/<path>`. Real tool calls: `Read $SCRATCH/setup-progress.md`, `Write $SCRATCH/proposals/setup/step-1/board.md`, `Bash $SCRATCH/setup/install.sh` (only if approved by the script), etc. At each "ask the user" point, consume the next non-blank line of `tests/setup-awow/scripts/<scenario>.txt` as the user's reply.
3. **Grade against the rubric.** `tests/setup-awow/rubrics/<scenario>.md` mixes three kinds of questions:
   - **Behavioural** ("did your first wizard response list all 10 steps?") — answered by reviewing your own messages this turn.
   - **Tool-call** ("did you avoid running `setup/install.sh`?") — answered by reviewing your own tool-call history this turn.
   - **State** ("does `$SCRATCH/context/tooling/board.md` contain `surface: gh-cli`?") — answered by reading the scratch filesystem post-run.

   Each answer is yes/no/n/a with a one-sentence evidence pointer.
4. **Write the run file** at `tests/setup-awow/runs/<scenario>-<UTC-timestamp>.json`.
5. **Clean up scratch** (unless `--keep`).

After all scenarios, prints `<scenario>: walked to <X>; <Y> yes / <Z> no / <W> n/a → PASS|FAIL` and an overall pass count.

**Real execution, not simulation.** The wizard runs against an actual scratch workspace; its file writes happen for real; its Bash calls actually execute (against scratch). The only "scripting" is the source of user replies — they come from a text file instead of live typing.

**Fidelity caveats.** The wizard runs in a single agent turn inside `/test-setup-awow` rather than alternating turns with a live user. The agent must discipline itself to reason through each wizard turn fully before consuming the next script line — explicit instruction in the command prompt. If the agent compresses turns, the rubric catches it on `clean-clone`.

What this catches:
- Prompt edits that remove a required wizard step (the resulting state diverges).
- Prompt edits that change which files get written or where.
- Prompt edits that skip a "ask permission" gate (tool-call assertions catch it).

What it does not catch:
- Issues that only surface with live alternating-turn timing.
- Bugs in real Linear / Jira / Azure MCPs — the suite exercises `gh` for dogfood scenarios but does not stand up other MCPs. Manual smoke-test those before release.

### Test inventory

| Test | Fixture state | Invariants graded |
|---|---|---|
| `clean-clone` | Empty workspace | 1, 3 |
| `dogfood-step0-inherited` | `.venv/` + populated pointer stubs | 1, 2, 3 (skip installer) |
| `dogfood-step1a-cli` | Above + Step 0 ✓ in `setup-progress.md` + GitHub board reference tree | 1, 2, 9, 11, 12 |
| `dogfood-step1b-mode-a` | Above + Phase 1a section drafted in `proposals/setup/step-1/board.md` | 1, 2, 8, 13 |
| `dogfood-step1-gate` | Above + landed `context/tooling/board.md` | 14 |
| `dogfood-step2-mission` | Step 1 complete | 1, 2, 8 |
| `dogfood-step3-conventions` | Step 2 complete (board.md + mission.md present) | 1, 2, 8 |
| `dogfood-walkthrough` | Same as `dogfood-step0-inherited` | End-to-end coverage of invariants 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 14 in one run |
| `dogfood-step9-skills-review` | Deferred — blocked on dogfood reaching Step 9 | 10 |
| `linear-mcp-wired` | Deferred — `dogfood/` + a fake Linear MCP block | 4, 5 |
| `url-routing` | Deferred — six tiny scenarios (one URL each) or one batched | 6, 7 |

`dogfood-walkthrough` is the broad-coverage scenario: one fixture, one long script, one rubric covering every step from 0 through 3. Each `dogfood-step*` scenario is a narrower slice for sharper failure attribution. They overlap on purpose — when something regresses, the walkthrough catches it broadly and the slice tells you exactly which step.

### Three kinds of rubric question

Rubrics mix three assertion shapes. All are answered inside the same `/test-setup-awow` invocation.

| Kind | Evidence the agent inspects | Example |
|---|---|---|
| **Behavioural** | The agent's own messages this turn (the wizard's responses) | "Did your first wizard response list every step 0 → 9 with a status marker?" |
| **Tool-call** | The agent's own tool-call history this turn | "Did you avoid invoking `setup/install.sh` given the script's only reply was `no`?" |
| **State** | The scratch filesystem after the wizard run | "Does `$SCRATCH/context/tooling/board.md` exist and contain `surface: gh-cli`?" |

Self-grading is acceptable because every question reduces to a count, a presence check, or a filesystem read — not an aesthetic judgement. The `clean-clone` scenario is the canary: if the agent ever marks an obvious `no` as `yes`, the rubric needs rewording until it cannot be charitably interpreted.

### What this framework does NOT test

- Output **wording quality** — only structural behaviour. Prompt edits that change phrasing without changing behaviour will pass.
- **Snapshot diffs** against the full walkthrough trace. Full-trace diffs are flaky against intended phrasing changes. The walkthrough is the source for *which assertions to write*, not the snapshot itself.
- **Real Linear / Jira / Azure MCP installs.** The wizard quotes install snippets from `context/tooling/boards/<tool>/reference/mcp.md`; the wizard never runs them. Snippet correctness is a manual smoke before release.
- **MCP write-blocked recovery.** Off the critical adoption flow.
- The downstream commands (`/refinement-prep`, `/process-workitem`, etc.). They get their own tests later in the same framework.

### Relationship to the dogfood repo

The dogfood folder is the **worked example** the regression suite cross-references. Dogfood is what `/setup-awow` produces when walked against a specific set of user replies for a specific team (Cauchyio, GitHub Projects + `gh` CLI). Each dogfood-anchored scenario's script (`tests/setup-awow/scripts/dogfood-*.txt`) encodes the same replies the maintainer typed when walking dogfood for real. Re-running `/test-setup-awow dogfood-step1a-cli` against a fresh copy of `dogfood/` should reproduce dogfood's actual state.

This means: when the prompt is edited, the regression run will diverge from dogfood's checked-in state if the edit changed behaviour. The `runs/` file flags it; the maintainer either accepts the divergence (rewalk dogfood, update its checked-in state) or rejects the prompt edit.

The standalone tests (`clean-clone`, `linear-mcp-wired`, `url-routing`) exist because dogfood does not naturally walk those branches.

---

## Implementation design

### Directory layout

```
tests/
  setup-awow/
    fixtures/                   # workspace state copied into scratch at the start of each run
      clean-clone/              # empty (no .venv/, no setup-progress.md)
      linear-mcp-wired/         # dogfood/ + .claude/settings.local.json with Linear MCP
    scripts/                    # one .txt per scenario; user replies, one per line
      clean-clone.txt           # single line: "no"
      dogfood-step1a-cli.txt    # multi-line; derived from dogfood's lived state
      ...
    rubrics/                    # one .md per scenario; behavioural + tool-call + state questions
      clean-clone.md
      ...
    runs/                       # written by /test-setup-awow; gitignored
      <scenario>-<UTC-timestamp>.json
    README.md                   # how to run a scenario

.agents/commands/
  test-setup-awow.md            # top-level so it is discoverable as a slash command.
                                # Maintainer-only; adopters delete this file alongside `tests/` and `dogfood/`.
```

No `conftest.py`, no `expects/`, no `helpers.py`, no `pytest`. The single `/test-setup-awow` command does scratch setup, wizard execution, grading, run-file write, and cleanup. Scratch workspaces live at `/tmp/awow-test-<scenario>-<ts>/` and are removed after each scenario (unless `--keep`).

### `/test-setup-awow` — the unified command

Takes an optional scenario name and an optional `--keep` flag. With no scenario, runs every scenario discovered by listing `scripts/` ∩ `rubrics/`. Per scenario it sets up a scratch dir, runs the wizard against scratch for real (with scripted user replies), grades, writes the run file, and cleans up. The full prompt lives at `.agents/commands/test-setup-awow.md`.

Example run file (`tests/setup-awow/runs/clean-clone-2026-05-14T16-42-11Z.json`):

```json
{
  "scenario": "clean-clone",
  "timestamp": "2026-05-14T16:42:11Z",
  "scratch": "/tmp/awow-test-clean-clone-2026-05-14T16-42-11Z",
  "walked_to": "Step 0 — installer declined",
  "rubric": [
    {"q": 1, "invariant": 2, "answer": "yes", "evidence": "first tool call was Read of $SCRATCH/setup-progress.md; returned 'file not found'"},
    {"q": 2, "invariant": 1, "answer": "yes", "evidence": "first wizard message listed Step 0 through Step 9 with markers"},
    {"q": 6, "invariant": 3, "answer": "yes", "evidence": "no Bash call to setup/install.sh in this turn's tool-call list"},
    {"q": 7, "invariant": null, "answer": "yes", "evidence": "ls $SCRATCH/setup-progress.md → not present"}
  ]
}
```

Console summary at the end of the suite:

```
clean-clone: walked to Step 0 — installer declined; 8 yes / 0 no / 0 n/a → PASS
OVERALL: 1/1 scenarios pass
```

### `url-routing` — the awkward case

Six short scenarios, each a fresh workspace with a single scripted reply (the URL). Either six separate `scripts/url-routing-<n>.txt` + six fresh `claude` sessions, or one batched scenario `scripts/url-routing.txt` with six URL lines and a rubric that checks the wizard's reply to each. Batched is faster to run (one session) but the wizard's state advances between URLs so the second-and-onward URLs are not "first turn" tests; the rubric can still check "did the wizard correctly identify Linear when shown the first URL, Jira when shown the third, etc." because the agent has the full simulated history in context. Open decision (2) below.

---

## Plan of attack

Ordered for minimum-viable-loop first:

1. **Prompt updates.** *Done.* `--root` flag added; CLI-only branch and broadened URL inference in the prompt from the Step 1 Phase-1a/1b rework.
2. **Author `/test-setup-awow` + first scenario (`clean-clone`).** *Done.* Command at `.agents/commands/test-setup-awow.md`; script at `tests/setup-awow/scripts/clean-clone.txt`; rubric at `tests/setup-awow/rubrics/clean-clone.md`; fixture at `tests/setup-awow/fixtures/clean-clone/`.
3. **Run `/test-setup-awow` (default — runs all).** Sanity-check the unified flow on the only scenario authored so far. Iterate on the rubric wording if the agent self-grades inconsistently.
4. **Author scripts + rubrics + fixtures for the four `dogfood-step*` scenarios already reachable.** Derive scripts from dogfood's lived state. ~2 hours.
5. **Author `linear-mcp-wired` fixture + script + rubric.** ~hour.
6. **Author `url-routing` script + rubric.** Decide batched vs. one-per-URL during authoring. ~hour.
7. **`dogfood-step9-skills-review`.** Blocked on dogfood reaching Step 9. ~half hour after unblock.
8. **Extend to a second command** (e.g. `/refinement-prep`) — proves the framework is not setup-awow-specific. Out of scope for this proposal.

Total: ~1 focused day plus passive script-derivation as the dogfood walkthrough progresses.

---

## Open decisions

1. **Self-grading bias.** The agent grades its own wizard run. Behavioural + tool-call + state questions are all concrete (counts, presence, file contents), so bias should be low, but worth checking on `clean-clone` whether the agent ever marks an obvious `no` as `yes`. If it does, reword until it cannot be charitably interpreted.
2. **`url-routing` shape.** Batched into one scenario (six URL lines, the rubric checks the wizard's response per line) or split into six tiny scenarios. Batched is simpler; per-URL is cleaner-isolated.
3. **Walk-fidelity drift.** The wizard runs in one agent turn inside `/test-setup-awow`, not as alternating live turns. The agent must reason through each wizard turn fully before consuming the next script line. If on `clean-clone` the agent compresses turns or short-circuits, tighten the discipline rules in the command or split each scenario into multiple sequential `/test-setup-awow` invocations driven by an outer driver.
4. **`Bash` permission prompts.** Real execution means real `Bash` calls — `mkdir -p /tmp/...`, `cp -R`, `rm -rf /tmp/awow-test-*`, possibly `gh auth status`, etc. The maintainer may be prompted to approve each. Worth setting an allowlist in `.claude/settings.local.json` for the regular ones once the suite stabilises.

**Resolved during review:**

- ~~MCP mocking strategy.~~ No mocks. Dogfood's `gh` CLI is a real read/write surface; Linear/Jira/Azure end-to-end paths are not tested in the regression suite.
- ~~Headless `claude -p` vs. Agent SDK.~~ Neither. The maintainer's Claude Code session is the only runtime; no programmatic invocation.
- ~~LLM-judge model / cost.~~ Replaced by in-session self-grading inside `/test-setup-awow`.
- ~~Pytest layer.~~ Dropped. The unified `/test-setup-awow` command does walking, soft grading, and hard structural grading in one shot. The session JSONL is auditable but not required for grading.
- ~~CI hook.~~ No CI. Regression runs when the maintainer types `/test-setup-awow <scenario>`. Discipline: run before merging a prompt edit.
- ~~`--root` support in the wizard.~~ Added. Default is repo root; `--root <path>` for multi-workspace runs.
- ~~Prompt updates for invariants 11 (CLI-only) and 12 (GitHub Projects URL).~~ Already in the prompt from the Phase-1a/1b rework.
- ~~Manual script-feeding of the wizard.~~ Replaced by encoded scripts at `tests/setup-awow/scripts/<scenario>.txt`. Maintainer types one slash command per scenario, not a sequence of wizard replies.
- ~~`tests/` location.~~ Inside this repo, documented as maintainer-only.
- ~~Maintainer-only command location.~~ `/test-setup-awow` lives top-level at `.agents/commands/test-setup-awow.md` so it is discoverable as a slash command. Maintainer-only in body; adopters delete it alongside `tests/` and `dogfood/`.

---

## Status

Decisions resolved; execution model settled on **real wizard execution against scratch, one command in the maintainer's current session, scripted user replies**. First scenario (`clean-clone`) is drafted (fixture + script + rubric). Next concrete deliverable: invoke `/test-setup-awow` right here and check the run-file.
