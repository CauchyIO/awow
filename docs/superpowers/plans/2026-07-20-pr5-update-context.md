# PR 5 — `/update-context` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a rule stated in passing a path into the context tree. Today nothing captures *"we always put the ticket ID in the branch name"* — `/kb-mine` reads an activity snapshot and never the conversation, `/process-retro` needs a transcript, `/setup-awow` is a one-time bootstrap. The rule evaporates with the session.

**Architecture:** One new command, `.agents/commands/update-context.md`, carrying `autofire: true` so it becomes the tenth situationally-invoked command (§4.5 Layer 3) rather than a bespoke mechanism. Its front half already exists: PR 1 landed the noticing reflex in `.agents/skills/using-awow/SKILL.md`, which is `cat`-ed into every session by `hooks/session-start` and gates on this command's presence — so it activates the moment this PR lands. The command discriminates candidates on three predicates, routes them in three tiers, shows the actual diff and the verbatim quote at one gate, and stages what it cannot route. Deferred and unrouted candidates go into the existing `context/kb-inbox/` under a widened schema (`kind: guidance`) and drain through `/kb-synthesize`'s new disposition branch. Along the way, PR 5 fixes a live bug on `main`: `/process-retro` writes its instruction diffs into files `gather.py` regenerates.

**Tech Stack:** Python 3.12 stdlib only (no pytest, no third-party). `tools/gather.py` is the build; `tools/lint-paths.py` is the token linter; `.github/workflows/ci.yml` runs both plus `tests/harness/run-harness-tests.sh all`.

**Spec:** `docs/superpowers/specs/2026-07-20-plugin-first-readme-design.md` §4.6, plus §4.5's `autofire` selection rule and format constraint. This plan covers PR 5 of five.

## Global Constraints

- **Python 3.12, stdlib only.** No pytest, no network, no third-party. Tests are plain scripts run as `python3 tests/<dir>/test_<name>.py`, following `tests/awow-lock/test_awow_lock.py`. Every test module opens with a docstring ending in a `Run:` line.
- **Never hand-edit generated files.** `.claude/`, the `.github/` pointer stubs, `dist/`, the root `AGENTS.md`, `.claude/CLAUDE.md`, and `.github/copilot-instructions.md` are `gather.py` output. Edit the source under `.agents/` and re-run the gather.
- **After any `.agents/` edit, run `python tools/gather.py`** and commit the regenerated surfaces alongside the source change, or `--check` fails in CI.
- **Four channel values exist, not two:** `vendored` (excluded from the payload — PR 2 moves `update-awow.md` and `project-manager.md` here), `bootstrap` (`setup-awow.md` — these *do* ship), `telemetry` (added by PR 3; builds into `dist-telemetry/` instead of `dist/`), and the default. Do not assume a binary. `update-context.md` carries no `channel:` field, so it takes the default and ships.
- **`tools/lint-paths.py` scans `.agents/commands/` and `.agents/skills/` only,** and its `BARE` regex at `:11` is `(?<![{/\w.\-])(context|tools|proposals)/`. Every reference to those three roots in a prompt body must be preceded by a token (`{HUB}/`, `{PROJECT}/`, `{AWOW_ROOT}/`, `{AWOW_TOOLS}/`) — **including inside code fences**, which the linter does not exempt. Files under `context/` are not scanned, so `context/kb-inbox/README.md` and `context/knowledge-base/synthesis.md` keep their existing bare-path prose style.
- **Do NOT edit `.agents/skills/using-awow/SKILL.md`.** PR 1 made every amendment to that file in one coherent rewrite, including the `/update-context` reflex paragraph. It is already correct and already gates on this command.
- **Commit message style:** max 2 sentences.
- **Do not create PRs and do not push.** This plan produces commits only.

## What PR 1 already landed (treat as existing fact)

- `{AWOW_ROOT}` is substituted in both `PLUGIN_TOKEN_SUBSTITUTIONS` and `AGENT_SKILLS_TOKEN_SUBSTITUTIONS` in `tools/gather.py`.
- `PAYLOAD_CONTEXT_PATHS`, `TEAM_DATA_CONTEXT_PATHS`, `classify_context_path(rel) -> str`, and `unclassified_context_paths() -> list[str]` exist in `tools/gather.py`.
- `dist/context/` ships the classified machinery; `dist/.github/` ships a generated Copilot payload.
- **Machinery reads use `{HUB}` first, `{AWOW_ROOT}` second.** `context/tooling/knowledge-base.md`, `context/kb-inbox/README.md`, and `context/knowledge-base/synthesis.md` all classify `payload`, so every new reference this PR writes to them uses the two-step form. Team data — `context/team/conventions/`, `context/team/style/` — is `{HUB}` only, no fallback.
- `tests/gather-tokens/` and `tests/payload-classification/` exist and run in CI.

**Consequence for Task 3.** PR 1 Task 6 rewrote the existing `{HUB}/context/knowledge-base/synthesis.md` references inside `.agents/commands/kb-synthesize.md` into the two-step form and dropped their relative markdown links. This plan therefore anchors its `kb-synthesize.md` edits on headings and on lines PR 1 leaves alone (`{HUB}/context/kb-inbox/` classifies as neither payload nor team-data at directory granularity, so PR 1's Step 3 skips it). Where a step tells you to preserve surrounding text, preserve whatever form is actually in the file — do not revert a two-step reference to a bare one.

---

### Task 1: Fix the `/process-retro` mirror-write bug

`process-retro.md` proposes instruction diffs and then lands them in `CLAUDE.md` / `copilot-instructions.md`. `tools/gather.py:333-341` (`plan_top_level`) generates `.claude/CLAUDE.md` and `.github/copilot-instructions.md` from `.agents/AGENTS.md` on every build. Every instruction diff that command has ever landed was destroyed by the next `python tools/gather.py`. This is a live bug on `main` and is independent of the rest of PR 5.

**Files:**
- Create: `tests/context-writes/test_context_writes.py`
- Modify: `.agents/commands/process-retro.md:10`, `:264`, `:284`, `:323-328`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: `tests/context-writes/test_context_writes.py` with the module-level constants `MIRRORS: tuple[str, str]` and `ALLOWED: dict[str, str]` (filename → why it may name a generated instruction file), and the accumulator `FAILURES: list[str]`. Task 4 extends this same file with a `check_update_context_frontmatter() -> None` function and relies on `"update-context.md"` already being in `ALLOWED`.

- [ ] **Step 1: Write the failing test**

Create `tests/context-writes/test_context_writes.py`:

```python
"""Guard: no prompt may land an instruction diff in a generated file.

tools/gather.py generates .claude/CLAUDE.md and .github/copilot-instructions.md
from .agents/AGENTS.md on every build (plan_top_level, gather.py:333-341). A
command that tells the agent to write an instruction diff into one of those is
writing to a build artefact: the edit survives until the next
`python tools/gather.py` and is then silently destroyed. /process-retro did
exactly that from the day it shipped.

Three checks:

  A. Only allowlisted commands may name a generated instruction file at all.
     /setup-awow authors them, /design-system verifies its house-style rule
     survived the bootstrap, /update-context names them only to forbid writing
     them. Anything else is a write target and fails.
  B. Inside /update-context, every mention must sit on a line that also says
     "Never write". The prohibition is deliberately kept on one physical line in
     that file so this can stay a line check — do not reflow it.
  C. /process-retro must still target .agents/AGENTS.md. Deleting the
     loop-closing step is not a fix for writing it to the wrong place.

Pure stdlib; no pytest, no network.

Run:  python3 tests/context-writes/test_context_writes.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS = REPO_ROOT / ".agents" / "commands"

MIRRORS = ("CLAUDE.md", "copilot-instructions.md")

# filename -> why this command is allowed to name a generated instruction file
ALLOWED = {
    "setup-awow.md": "authors them via the CLAUDE.md / AGENTS.md bootstrap (Step 5)",
    "design-system.md": "checks that its house-style rule survived the bootstrap",
    "update-context.md": "names them only inside its Never-write prohibition",
}

FAILURES: list[str] = []


def check_mirror_mentions() -> None:
    for path in sorted(COMMANDS.rglob("*.md")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if not any(m in line for m in MIRRORS):
                continue
            if path.name not in ALLOWED:
                FAILURES.append(
                    f"{rel}:{n} names a generated instruction file. gather.py "
                    f"rewrites it on every build, so a diff landed there is lost. "
                    f"Target .agents/AGENTS.md or {{HUB}}/context/team/ instead.\n"
                    f"    {line.strip()}"
                )
            elif path.name == "update-context.md" and "Never write" not in line:
                FAILURES.append(
                    f"{rel}:{n} names a generated instruction file outside the "
                    f"prohibition. Keep every mention on the single-line "
                    f'"**Never write ...**" boundary.\n    {line.strip()}'
                )


def check_retro_still_closes_the_loop() -> None:
    retro = COMMANDS / "process-retro.md"
    if ".agents/AGENTS.md" not in retro.read_text():
        FAILURES.append(
            ".agents/commands/process-retro.md targets no instruction file at "
            "all. The fix retargets its diffs to .agents/AGENTS.md; removing the "
            "loop-closing step is not the fix."
        )


def main() -> int:
    check_mirror_mentions()
    check_retro_still_closes_the_loop()

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Instruction-file write targets OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/context-writes/test_context_writes.py`

Expected: exit 1, with **four** failures — the three `process-retro.md` mentions plus the missing `.agents/AGENTS.md` target:

```
FAIL .agents/commands/process-retro.md:10 names a generated instruction file. gather.py rewrites it on every build, so a diff landed there is lost. Target .agents/AGENTS.md or {HUB}/context/team/ instead.
    You take a raw retrospective transcript and turn it into **structured signal that closes the loop back into the team's agent instructions** — anti-patterns named, actions owned, recurring issues escalated, and concrete diffs proposed for `CLAUDE.md` / `copilot-instructions.md`.
FAIL .agents/commands/process-retro.md:264 ...
FAIL .agents/commands/process-retro.md:284 ...
FAIL .agents/commands/process-retro.md targets no instruction file at all. The fix retargets its diffs to .agents/AGENTS.md; removing the loop-closing step is not the fix.

4 failure(s).
```

- [ ] **Step 3: Retarget the three mention sites**

In `.agents/commands/process-retro.md`, replace line 10:

```markdown
You take a raw retrospective transcript and turn it into **structured signal that closes the loop back into the team's agent instructions** — anti-patterns named, actions owned, recurring issues escalated, and concrete diffs proposed for `.agents/AGENTS.md`.
```

**The two line numbers below drift.** PR 2 Task 9 inserts a paragraph after `:78` and PR 4 Task 3 inserts a `description:` at line 2, so `:264` and `:284` are `main`-relative only. Match on the quoted old text, not the number. Replace:

```markdown
11. **Instruction-tightening proposals** — concrete diffs for `CLAUDE.md` / `copilot-instructions.md` / specific prompt files. Output as actual code-block diffs with a reason, not vague suggestions.
```

with:

```markdown
11. **Instruction-tightening proposals** — concrete diffs for `.agents/AGENTS.md` (the source the harness instruction files are generated from) or for specific prompt files under `.agents/commands/`. Output as actual code-block diffs with a reason, not vague suggestions.
```

Replace:

```markdown
Ask: *"Land the instruction diffs in `CLAUDE.md` / `copilot-instructions.md`? Save the report to `retro-reports/<team>/`? Anything to redact from the sponsor one-pager before it goes up?"*
```

with:

```markdown
Ask: *"Land the instruction diffs in `.agents/AGENTS.md`? Save the report to `retro-reports/<team>/`? Anything to redact from the sponsor one-pager before it goes up?"*
```

- [ ] **Step 4: Make the write step regenerate the mirrors**

Editing `.agents/AGENTS.md` is only half the job — the mirrors have to be rebuilt or the repo is left out of sync and `gather.py --check` fails in CI. In `.agents/commands/process-retro.md`, replace section 3.2 (lines 323-328, from the `### 3.2` heading through the closing fence of the provenance snippet) with:

```markdown
### 3.2 Apply approved instruction diffs

For each diff approved at Gate 2, edit `.agents/AGENTS.md` (or the named prompt file under `.agents/commands/`). Show the diff inline before saving. Add a one-line provenance comment after each addition:

```markdown
<!-- Added 2026-05-23 from retro: retro-reports/platform-team/2026-05-22-hybrid.md -->
```

**Never edit the generated harness instruction files.** `.agents/AGENTS.md` is the source; run `{AWOW_TOOLS}/gather.py` after landing a diff so the generated surfaces regenerate. A diff written straight into a generated file is destroyed by the next build, which is why every instruction diff this command landed before 2026-07-20 is gone.
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python3 tests/context-writes/test_context_writes.py`
Expected: `Instruction-file write targets OK.` and exit 0.

- [ ] **Step 6: Verify build and lint**

```bash
python tools/gather.py && python tools/lint-paths.py && python tools/gather.py --check
```

Expected: `Path tokens clean.` from the linter, and `--check` exits 0. `.claude/commands/process-retro.md` and `.github/prompts/process-retro.prompt.md` are pointer stubs carrying only the description, so they will not change; `dist/commands/process-retro.md` and `dist/agent-skills/process-retro/SKILL.md` carry the body and **will** change. Confirm:

```bash
git status --porcelain dist/ | sort
```

Expected: exactly two modified paths, `dist/agent-skills/process-retro/SKILL.md` and `dist/commands/process-retro.md`.

- [ ] **Step 7: Wire the test into CI**

In `.github/workflows/ci.yml`, add a step to the `gather-check` job immediately after the `Path-token lint` step (which ends at line 18):

```yaml
      - name: Instruction-file write targets
        run: python3 tests/context-writes/test_context_writes.py
```

- [ ] **Step 8: Commit**

```bash
git add .agents/commands/process-retro.md tests/context-writes/ .github/workflows/ci.yml dist/
git commit -m "Retarget /process-retro's instruction diffs from the generated CLAUDE.md and copilot-instructions.md to their source, .agents/AGENTS.md. Every diff that command landed since it shipped was destroyed by the next gather; a CI guard now blocks the whole class."
```

---

### Task 2: Widen the kb-inbox schema with `kind: guidance`

The inbox is the one staging surface and `/kb-synthesize` is the one drain. A guidance candidate — a rule the team obeys — needs to ride the same rails as a knowledge candidate without pretending to be one, because it promotes into `context/team/` rather than `kb_root` and its dispositions differ.

**Files:**
- Modify: `context/kb-inbox/README.md:21-44` (the `## File format` section), `:48-51` (Lifecycle step 2)

**Interfaces:**
- Consumes: nothing.
- Produces: the schema keys and their vocabularies, as strings, consumed by Task 3's disposition table and Task 4's Phase 4 staging step:
  - `kind` — `"knowledge"` (default) or `"guidance"`.
  - `source` — gains the value `"update-context"`.
  - `suggested_target` — for `kind: guidance`, a repo-relative path to an **existing** file under `context/team/`, or the literal sentinel `UNROUTED`.
  - `source_quote` — required for `kind: guidance`; a single-line double-quoted verbatim sentence.

**Why frontmatter here and nowhere else:** `context/kb-inbox/README.md:26-28` already states the rule — frontmatter is allowed in the inbox precisely because the inbox is transient, and the durable layer stays frontmatter-light. That justification extends to `kind` and `source_quote` unchanged: both are drain-time routing data with no reason to survive promotion. Neither key is ever written into a promoted file.

- [ ] **Step 1: Replace the `## File format` section**

In `context/kb-inbox/README.md`, replace lines 21-44 — the `## File format` heading through the paragraph ending `so promotion is a move, not a rewrite.` — with:

```markdown
## Two lanes, one drain

Candidates arrive in two kinds. Both stage here, both drain through `/kb-synthesize`,
and they differ only in where they promote to and how they are judged:

| `kind` | Feeder | Promotes into | What it is |
|---|---|---|---|
| `knowledge` (default) | `/kb-mine`, transcripts, work items | `kb_root` (`context/knowledge-base/`) | A durable fact about the system or the domain. |
| `guidance` | `/update-context` | `context/team/conventions/` or `context/team/style/` | A durable rule the team obeys — "when X, do Y". |

The split is the P3 predicate `/update-context` applies: normative and team-scoped is
`guidance`; a fact about the world is `knowledge`. *"The staging DB is eu-west-1"* is
knowledge even though it is durable, general, and asserted. A candidate carries exactly
one kind.

## File format

Filename: `YYYY-MM-DD-<source>-<slug>.md` — the date it was captured, the feeder that
produced it, and a short kebab slug (e.g. `2026-07-01-mine-per-tenant-auth.md`).

Frontmatter is allowed **here** precisely because the inbox is transient — the durable
layer stays frontmatter-light (see `context/knowledge-base/README.md`). Keep it to this
fixed schema:

```markdown
---
kind: knowledge | guidance                # which lane this drains into (default: knowledge)
source: mine | transcript | workitem | update-context   # which feeder produced this
source_ref: <TEAM>-123 | <repo>#45 | path/to/transcript.md   # where it came from
date: YYYY-MM-DD                          # capture date
suggested_target: <vocabulary depends on kind — see below>
source_quote: "<the verbatim sentence>"   # kind: guidance only, required
---

<the candidate body, already written in its destination's format — a decisions/
candidate uses the ADR header (Context / Decision / Consequences); a guidance
candidate is the rule itself, in the target file's own format>
```

`suggested_target` is the feeder's routing guess; the drain confirms or overrides it.
Its vocabulary depends on `kind`:

| `kind` | `suggested_target` |
|---|---|
| `knowledge` | `architecture`, `patterns`, `runbooks`, `decisions`, or `glossary` — a `kb_root` subfolder |
| `guidance` | a repo-relative path to an **existing** file under `context/team/`, or the literal `UNROUTED` |

`UNROUTED` means no destination file exists. It is a deliberate terminal state, not a
failure to fix: neither the feeder nor the drain may create a new convention or style
file to resolve it. A file invented at that moment is one no README indexes, no command
reads, and `/setup-awow` does not know about. Unrouted candidates accumulating is the
signal that the context tree is missing a home — inventing one destroys the signal by
looking like a resolution.

`source_quote` is required for `kind: guidance` and holds the **verbatim** sentence the
rule was stated in — one line, double-quoted, never paraphrased. Both gates that can
approve a guidance candidate show it, because a rule approved without seeing the
sentence it came from is guessed rather than approved. A guidance candidate missing it
is malformed: the drain reports it and leaves it in the inbox.

The body is authored in the destination's format so promotion is a move, not a rewrite.
```

- [ ] **Step 2: Extend Lifecycle step 2 to name both lanes**

In `context/kb-inbox/README.md`, replace the Lifecycle step 2 bullet (originally lines 49-51, beginning `2. **Drain**`) with:

```markdown
2. **Drain** — `synthesis.md` reads the committed candidates. For a `kind: knowledge`
   candidate the human-gated drain decides: promote (novel), annotate an existing note
   (matches), no-op (already covered), or drop (thin). A `kind: guidance` candidate
   takes the guidance dispositions instead. See that contract for both sets.
```

- [ ] **Step 3: Verify the payload copy regenerates and nothing else moved**

```bash
python tools/gather.py
python3 tests/payload-classification/test_classification.py
git status --porcelain context/ dist/context/
```

Expected: `Payload classification OK.`, and exactly two modified paths — `context/kb-inbox/README.md` and `dist/context/kb-inbox/README.md`. `context/kb-inbox/README.md` classifies `payload` (it is a contract), so PR 1's bidirectional check requires the shipped copy to track the source.

- [ ] **Step 4: Commit**

```bash
git add context/kb-inbox/README.md dist/
git commit -m "Widen the kb-inbox schema with a kind field so guidance candidates stage on the same rails as knowledge ones, plus the source_quote and UNROUTED vocabulary they need. Frontmatter stays an inbox-only affordance — neither key survives promotion."
```

---

### Task 3: The `kind: guidance` disposition branch

`/kb-synthesize` sequences a contract it does not restate (`kb-synthesize.md:16-21`). Keep that split: the guidance dispositions are defined once in `synthesis.md`, and the command grows only the control flow that reaches them.

**Files:**
- Modify: `context/knowledge-base/synthesis.md:19-25` (Input), insert a new section between `## Reconcile` (ends `:49`) and `## The gate` (`:51`), `:56-63` (The gate), `:65-72` (Autonomous mode)
- Modify: `.agents/commands/kb-synthesize.md:4` (prerequisites), `:44-54` (Phase 0), `:58-68` (Phase 1), `:72-84` (Phase 2), `:88-96` (Behavioral boundaries)

**Interfaces:**
- Consumes: Task 2's `kind`, `source_quote`, `suggested_target`/`UNROUTED` vocabulary.
- Produces: the six guidance dispositions as named strings — `novel`, `sharpens`, `covered`, `contradicts`, `unroutable`, `thin` — and the ten-rule accretion cap. Task 4's command body cites the same cap and the same `UNROUTED` terminal state; the two must not diverge.

**Path-token note.** `synthesis.md` lives under `context/` and is not linted, so it keeps its existing bare-path prose (`context/knowledge-base/`, `context/team/`) exactly as the surrounding sections write it. `kb-synthesize.md` is a linted prompt: every `context/` reference you add there needs a token prefix, and machinery reads take the `{HUB}`-then-`{AWOW_ROOT}` form PR 1 established.

- [ ] **Step 1: Teach `synthesis.md`'s Input section about the two lanes**

In `context/knowledge-base/synthesis.md`, replace lines 19-25 — the `## Input` heading through `` `_synthesis-log.md` and `README.md` are never candidates. `` — with:

```markdown
## Input

The **committed** candidate files in `context/kb-inbox/` (one durable insight or rule
each, with `kind` / `source` / `source_ref` / `date` / `suggested_target` frontmatter,
plus `source_quote` when `kind: guidance`). The drain reads committed state only — an
uncommitted candidate is not yet in scope.

`kind` selects the disposition set: `knowledge` (the default, and the only kind before
`/update-context` existed) takes *Per-candidate disposition* below; `guidance` takes
*Guidance candidates*. A candidate with no `kind` is `knowledge`.

`_synthesis-log.md` and `README.md` are never candidates.
```

- [ ] **Step 2: Add the guidance disposition section**

In `context/knowledge-base/synthesis.md`, insert between the end of `## Reconcile` (line 49) and the `## The gate` heading (line 51):

```markdown
## Guidance candidates (`kind: guidance`)

A guidance candidate is a rule the team obeys, not a fact about the system. It promotes
into `context/team/`, never into `kb_root`. `/update-context` is its only feeder, and
the drain sees it only when the user deferred it at that command's gate or it arrived
`UNROUTED`.

Read the `suggested_target` file **and its siblings** before deciding — the tree is not
deterministic and a rule can plausibly belong in `conventions/` or `style/`. Then:

| Disposition | When | Action |
|---|---|---|
| **Novel** | The target file states no rule covering this. | Append the rule to the target file, in that file's own format. |
| **Sharpens** | An existing rule covers the same ground, less precisely. | Rewrite that rule in place. Do not append a near-duplicate beside it. |
| **Covered** | An existing rule already says this. | **No-op.** The value was confirming it is written down. |
| **Contradicts** | An existing rule says the opposite. | Do not resolve it yourself. Surface both, with the candidate's `source_quote`, and let the user choose which survives and why. |
| **Unroutable** | `suggested_target` is `UNROUTED`, or names a file that does not exist. | Leave the candidate in the inbox and report it. Do not drop it — a growing unrouted pile is the signal that the tree is missing a home. |
| **Thin** | Scoped to one file, one ticket, or one person's preference. | **Drop.** Logged, not promoted. |

Three rules bind every guidance disposition:

- **Never create a convention or style file.** No destination means *unroutable*, always.
  There is no disposition that ends in a new file, at either end of the pipeline.
- **Cap each destination file at ten rules.** Count the unit that file already uses — a
  `## Rule N` section, a row of a rules table, an item of a numbered list. At the cap,
  propose a **merge** of two existing rules or a **replacement** of the one this
  candidate supersedes, and show that diff. Never an eleventh append. `conventions/
  REQUIRED/` is read at the start of every session, so an extra rule there taxes every
  future turn in the repo.
- **Show `source_quote` verbatim at the gate.** A candidate without one is malformed:
  report it and leave it in the inbox.

Provenance for guidance differs from the KB's. A promoted guidance rule carries a
one-line HTML comment immediately after it:

```markdown
<!-- Added YYYY-MM-DD via /update-context: "<source_quote>" -->
```

The KB forbids in-note provenance because the durable layer is frontmatter-light and the
board links into it. `context/team/` has neither property — it is read by agents mid-
session, where knowing a rule came from a named human sentence is what makes it
challengeable. `/process-retro` writes the same shape for the same reason.
```

- [ ] **Step 3: Make the gate's numbered steps kind-aware**

In `context/knowledge-base/synthesis.md`, replace the four numbered steps under `## The gate` (lines 56-61, from `1. Apply each approved disposition` through `— the durable record is now in \`context/knowledge-base/\` plus git history.`) with:

```markdown
1. Apply each approved disposition (write / annotate / no-op / drop, or the guidance
   equivalent).
2. Leave a one-line pointer in the source item's board comment for anything promoted:
   `Promoted to context/knowledge-base/<subfolder>/<x>.md`. Skip this for `kind:
   guidance` — it has no source board item; its provenance is the HTML comment beside
   the landed rule.
3. Append one provenance line per candidate to `context/kb-inbox/_synthesis-log.md`.
   For a guidance candidate, name the destination path and the disposition.
4. **Remove the drained candidate file** from `context/kb-inbox/` and commit the removal
   — the durable record is now in `context/knowledge-base/` or `context/team/`, plus git
   history.
```

- [ ] **Step 4: Extend the autonomous-mode park to both lanes**

In `context/knowledge-base/synthesis.md`, replace the final sentence of the `## Autonomous mode (out of scope here)` section — `Until then, this drain always stops at *The gate*.` — with:

```markdown
Until then, this drain always stops at *The gate*. This binds both lanes, and it is why
`/update-context` ships with no `--auto` mode either: a rule written into
`context/team/` unattended is binding on everyone who opens a session afterwards.
```

- [ ] **Step 5: Branch the command**

Five edits in `.agents/commands/kb-synthesize.md`. Each replaces the quoted text exactly; where a quoted line contains a `{HUB}/context/...` reference that PR 1 rewrote into the two-step form, keep whatever form the file currently has.

**5a — frontmatter prerequisites, near line 4.** This is PR 2 Task 4 Step 3's post-edit text: PR 2 deletes `/daily-routine` and rewrote this line to name `/kb-mine` alone, so anchor on that and never reintroduce the deleted command. (PR 4 Task 3 inserts a `description:` at line 2, so the line number drifts too — match the text.) Replace:

```yaml
  - "{HUB}/context/kb-inbox/ holds one or more candidate files (produced by /kb-mine)"
```

with:

```yaml
  - "{HUB}/context/kb-inbox/ holds one or more candidate files (produced by /kb-mine or /update-context)"
```

If the file still reads `(produced by /kb-mine or /daily-routine)`, PR 2 has not landed — stop and report rather than editing, because the replacement above would leave a shipped prerequisite pointing at a command PR 2 is about to delete.

**5b — Phase 0, line 46.** Replace the sentence:

```markdown
Read the **committed** candidate files in `{HUB}/context/kb-inbox/` (skip `README.md` and
`_synthesis-log.md`). If a file is present but uncommitted, warn and skip it — the drain
operates on committed state (`synthesis.md`, *Input*).
```

with:

```markdown
Read the **committed** candidate files in `{HUB}/context/kb-inbox/` (skip `README.md` and
`_synthesis-log.md`). If a file is present but uncommitted, warn and skip it — the drain
operates on committed state (`synthesis.md`, *Input*).

Read each candidate's `kind`. Absent means `knowledge`. Keep the two lanes separate from
here on: they take different disposition sets and land in different trees. Report the
split in one line (`4 knowledge, 1 guidance`) so the user knows what is about to be
judged against what.
```

**5c — Phase 1, after the paragraph ending `flag any candidate that *contradicts* an existing note for reconciliation.` (line 65).** Insert:

```markdown
For `kind: guidance` candidates, follow that contract's *Guidance candidates* section
instead: read the `suggested_target` file **and its siblings**, then assign **novel**,
**sharpens**, **covered**, **contradicts**, **unroutable**, or **thin**. Count the rules
in the destination first — at ten, the plan carries a merge or a replacement, never an
eleventh append. A candidate with `suggested_target: UNROUTED`, or one naming a file
that does not exist, is **unroutable**: it stays in the inbox and is reported. Never
create a convention or style file to give a candidate somewhere to go.
```

**5d — Phase 2, after the paragraph ending `do not cross it on your own.` (line 74).** Insert:

```markdown
For every guidance candidate in the plan, show its `source_quote` verbatim next to the
diff that would land. A rule the user approves without seeing the sentence it came from
is guessed, not approved. A guidance candidate with no `source_quote` is malformed —
report it, leave it in the inbox, and do not offer it for approval.
```

**5e — Behavioral boundaries, after the `- **Gated writes only.**` bullet (line 93).** Insert:

```markdown
- **Never create a convention or style file.** A guidance candidate with no existing
  destination is *unroutable* and stays in the inbox. Promotion moves a rule into a file
  someone already decided to keep; it never invents one.
```

- [ ] **Step 6: Verify build, lint, and the payload copies**

```bash
python tools/gather.py \
  && python tools/lint-paths.py \
  && python tools/gather.py --check \
  && python3 tests/payload-classification/test_classification.py
```

Expected: `Path tokens clean.`, `--check` exits 0, `Payload classification OK.`

```bash
git status --porcelain | sort
```

Expected exactly these six paths modified: `.agents/commands/kb-synthesize.md`, `context/knowledge-base/synthesis.md`, `dist/agent-skills/kb-synthesize/SKILL.md`, `dist/commands/kb-synthesize.md`, `dist/context/knowledge-base/synthesis.md`, `dist/.github/prompts/kb-synthesize.prompt.md`.

- [ ] **Step 7: Commit**

```bash
git add .agents/commands/kb-synthesize.md context/knowledge-base/synthesis.md dist/
git commit -m "Give the drain a kind: guidance branch — six dispositions, a ten-rule cap per destination file, and a hard bar on creating conventions. The rules live in synthesis.md; /kb-synthesize only sequences them."
```

---

### Task 4: The `/update-context` command

**Files:**
- Create: `.agents/commands/update-context.md`
- Modify: `tests/context-writes/test_context_writes.py` (add `check_update_context_frontmatter`)
- Modify: `.agents/commands/README.md:11` (the `standardise` row of the phase table)

**Interfaces:**
- Consumes: Task 2's inbox schema (`kind: guidance`, `source: update-context`, `source_quote`, `UNROUTED`); Task 3's ten-rule cap and unroutable disposition; PR 1's `{AWOW_ROOT}` token and the `/update-context` reflex paragraph already resident in `using-awow/SKILL.md`.
- Produces: `.agents/commands/update-context.md` with frontmatter `phase: standardise`, `autofire: true`, and a single-line double-quoted `description:`. `autofire` is consumed by PR 4's `dist/skills/` mirror; until PR 4 lands the field is inert data preserved verbatim by `plugin_command_copy` (`gather.py:430-451`) and stripped by `command_skill_stub` (`gather.py:495-513`), which emits `name` + `description` only.

**Three decisions the spec left open, resolved here:**

1. **This PR writes the command's `description:` itself.** §7's table lists sixteen commands and does not include `update-context` — it predates §4.6. PR 4 owns descriptions for the sixteen, but §10 states PR 5 is independent of PR 4 and may land first. Shipping without one means the H1 fallback (`command_description`, `gather.py:198-211`) advertises the command as *"land a rule stated in passing into the context tree"* — a label, not a trigger, on the one command whose whole value is firing at the right moment. So it is written here, following §4.5's format constraint: single-line, double-quoted, no block scalar.

2. **The description contains no double quotes.** `parse_frontmatter` strips surrounding quotes with a plain slice (`gather.py:335-339`) and never unescapes, and `plugin_command_copy` re-escapes on the way out. An inner `\"` survives into the picker as a literal backslash. The phrasing avoids the problem rather than working around it.

3. **`.awow/no-context-prompt` gets no `.gitignore` entry of its own.** PR 2 Task 9 Step 5 already ignores the whole `.awow/` directory, so the flag is covered the moment it is written — a per-file rule beneath a directory rule is dead text. It sits alongside the flags `hooks/session-start:25` and `:46` already read (`.awow/no-setup-prompt`, `.awow/no-engine-prompt`), which that same directory rule covers, and it is adopter-local state in the adopter's repo regardless. If PR 5 lands before PR 2, `.awow/` is momentarily untracked-but-unignored here; that resolves when PR 2 merges and needs no edit in this PR.

- [ ] **Step 1: Extend the guard test with the frontmatter contract**

In `tests/context-writes/test_context_writes.py`, add this function immediately after `check_retro_still_closes_the_loop`:

```python
def check_update_context_frontmatter() -> None:
    """/update-context's frontmatter is load-bearing three ways: `autofire: true`
    selects it for the dist/skills/ mirror (PR 4), `phase: standardise` makes it
    opt-in via /awow-add, and `description:` is what the harness actually matches
    on. parse_frontmatter is line-based — a block scalar (`>-`) is stored as the
    literal string '>-' and every picker entry silently becomes that."""
    path = COMMANDS / "update-context.md"
    if not path.is_file():
        FAILURES.append(".agents/commands/update-context.md is missing.")
        return
    text = path.read_text()
    if not text.startswith("---\n"):
        FAILURES.append("update-context.md has no frontmatter block.")
        return
    end = text.find("\n---", 4)
    if end == -1:
        FAILURES.append("update-context.md frontmatter block is unterminated.")
        return
    fields = {}
    for line in text[4:end].splitlines():
        if not line or line.startswith((" ", "\t", "-", "#")):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()

    if fields.get("phase") != "standardise":
        FAILURES.append(
            f"update-context.md phase is {fields.get('phase')!r}, expected "
            f"'standardise' so it stays opt-in via /awow-add."
        )
    if fields.get("autofire") != "true":
        FAILURES.append(
            f"update-context.md autofire is {fields.get('autofire')!r}, expected "
            f"'true' — it is the tenth autofire command (design spec 4.5)."
        )
    desc = fields.get("description", "")
    if desc[:1] in (">", "|"):
        FAILURES.append(
            f"update-context.md description uses a block scalar ({desc[:2]!r}). "
            f"parse_frontmatter stores the literal indicator, not the text."
        )
    elif not (len(desc) > 2 and desc.startswith('"') and desc.endswith('"')):
        FAILURES.append(
            f"update-context.md description must be a single-line, "
            f"double-quoted string; got {desc!r}."
        )
```

And add the call in `main()`, between the two existing calls:

```python
def main() -> int:
    check_mirror_mentions()
    check_update_context_frontmatter()
    check_retro_still_closes_the_loop()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 tests/context-writes/test_context_writes.py`

Expected: exit 1 with exactly one failure:

```
FAIL .agents/commands/update-context.md is missing.

1 failure(s).
```

- [ ] **Step 3: Write the command**

Create `.agents/commands/update-context.md` with exactly this content. The `**Never write ...**` bullet under *Behavioral boundaries* is one physical line on purpose — Step 1's check B is a line check. Do not reflow it.

```markdown
---
phase: standardise
prerequisites:
  - "Step 2 of /setup-awow complete ({HUB}/context/team/conventions/ exists — this command routes into it, never creates it)"
removes_pain: "a rule someone states in passing evaporating with the session instead of reaching the context tree"
description: "Use when a work session is wrapping up — a commit, a PR, an end-of-day sign-off — and the user stated a durable rule about how the team works along the way, so it lands in the context tree instead of evaporating with the session."
autofire: true
---

# /update-context — land a rule stated in passing into the context tree

You take the rules the user stated in passing this session and land them under
`{HUB}/context/team/`, one gated diff at a time. Not what the work produced — how the
team works. *"We always put the ticket ID in the branch name"* is a convention with
nowhere to live yet; you give it one.

You are the back half of a two-part reflex. The front half is `using-awow`, resident in
every session: it notices a rule mid-task and folds a one-line acknowledgement into the
reply already being written. It never interrupts and it never invokes you. You run once,
later, when the work is done and nothing competes for the turn.

**Read-only until the gate.** You propose diffs and wait. Nothing is written to
`{HUB}/context/`, to the inbox, or to git before explicit approval.

**Paths.** Convention and style destinations are team data: `{HUB}` only, no fallback,
and absence is information. Before any inbox write, resolve `inbox` and `kb_root` from
`{HUB}/context/tooling/knowledge-base.md`, falling back to
`{AWOW_ROOT}/context/tooling/knowledge-base.md` (a vendored copy wins over the shipped
one).

---

## When you run

Run at a **completion edge** and nowhere else: a commit, an opened PR, a merged branch,
or the user signing off — *"that's it for today"*, *"we're done here"*. Offer once per
session. If no completion edge arrives, the batch expires unoffered. Losing a candidate
is acceptable; interrupting is not.

Do not offer mid-task. This holds for every candidate, including one you judge important
— an exception clause reopens the negotiation on every turn, and the interruption
follows.

Before offering, check for `.awow/no-context-prompt`. If it exists, stay silent: the
user has declined for good. Still run when they invoke you by name.

---

## Pipeline overview

```
Phase 0 ─ Load the batch               ──→ candidates, or "Nothing captured this session."
Phase 1 ─ Discriminate (P1/P2/P3)      ──→ survivors, and one reason per reject
Phase 2 ─ Route (tier 1 / 2 / 3)       ──→ a destination file, or UNROUTED
Phase 3 ─ Draft each diff in the destination's own format
Phase 4 ─ GATE (diff + verbatim quote) ──→ write / stage / drop
```

---

## Phase 0 — Load the batch

The batch is what you noticed during this session and acknowledged in line. It is not
stored anywhere — no file, no state, no transcript re-read. If you did not notice a rule
while it was said, it is not a candidate now.

If the batch is empty, say exactly:

```
Nothing captured this session.
```

and stop. Do not scan back through the session hunting for something to justify the run,
and do not stay silent. A run that reports nothing is how the user learns the reflex is
under-firing rather than working; silence is indistinguishable from working.

---

## Phase 1 — Discriminate

A candidate qualifies only if **all three** predicates hold. Test each one explicitly.

| | Predicate | Fails when |
|---|---|---|
| **P1** | **Residue.** After doing exactly what was asked, something remains that changes behaviour in an unrelated session next week — writable as "when X, do Y" without naming this file or this ticket. | Completing the task discharges the instruction entirely. |
| **P2** | **Asserted.** Stated as a rule, in the present tense, as settled. | It was floated: *"we should probably standardise filenames at some point"*. |
| **P3** | **Normative and team-scoped.** A rule the team obeys. | It is a fact about the world — *"the staging DB is eu-west-1"* — which is knowledge, not guidance. Or it is one person's preference — *"stop saying you're absolutely right"* — and a dislike committed to git binds everyone to it. |

**Scoping words veto unconditionally.** *here*, *for this one*, *just this time*, *in
this file*, *for now* — the speaker has already told you the rule does not generalise.
Drop it without testing further.

For every candidate you drop, keep one line naming the predicate that failed, and report
those lines at the gate. A silent drop is indistinguishable from a miss, and the user
cannot correct what they cannot see.

**A P3 failure that is a fact, not a preference, is not yours but is not waste.** Carry
it to Phase 4 as an inbox candidate with `kind: knowledge` and `source: update-context`,
and let `/kb-synthesize` drain it into the knowledge base.

---

## Phase 2 — Route

List the destinations before you choose one. Read the file names under
`{HUB}/context/team/conventions/REQUIRED/`, `{HUB}/context/team/conventions/OPTIONAL/`,
and `{HUB}/context/team/style/`, and read any file you are about to propose writing into.
Do not route from memory of what the tree usually holds.

Then, per candidate:

**Tier 1 — one unambiguous destination.** Propose it with the diff.

**Tier 2 — two or more plausible destinations.** Present a numbered picker. The user
picks a number; never make them type a path.

**Tier 3 — no suitable destination exists.** Stage the candidate with
`suggested_target: UNROUTED` and stop there. **Never create a new convention or style
file.** A file you invent is one no README indexes, no command reads, and `/setup-awow`
does not know about — created at the moment of least deliberation in the whole flow.
Unrouted candidates piling up is useful signal about what the context tree is missing;
an invented file destroys that signal by looking like a resolution.

A destination that is documented but absent is tier 3. `{HUB}/context/tooling/board.md`
and `{HUB}/context/tooling/architecture.md` are referenced across the command set and may
not exist in this repo. Stage `UNROUTED` and name the step that creates them —
`/setup-awow` Step 1 for the board pointer, Step 8 for the architecture plane.

### Accretion duty

Count the rules in the destination file before drafting. A rule is one `## Rule N`
section, one row of a rules table, or one item of a numbered rules list — whichever unit
that file already uses.

At **ten rules**, stop appending. Propose instead a **merge** of two existing rules into
one, or a **replacement** of the rule this candidate supersedes, and show that diff at
the gate like any other. `conventions/REQUIRED/` is read at the start of every session,
so an eleventh rule taxes every future turn in this repo.

---

## Phase 3 — Draft the diff

There is no convention-file template, and three formats coexist in the tree: numbered
`## Rule N` sections, a table of rows, and bulleted prose under a heading. **Infer the
format from the file you are writing into** by reading its existing rules. Add no
frontmatter — the durable layer stays frontmatter-light.

Write the rule in agent-directive voice: second person, imperative, two sentences at most
— the rule, then at most one guardrail. Keep the evidence out of the imperative; the
quote goes in the provenance line, not the rule. (Full voice rules:
`.agents/skills/agent-directive-voice.md`, where the vendored tree is present.)

Add one provenance line immediately after the addition:

```markdown
<!-- Added YYYY-MM-DD via /update-context: "<the verbatim sentence>" -->
```

---

## Phase 4 — The gate

Present every candidate at once, each with the **actual diff** and the **verbatim quote**
it came from. A gate the user can approve without seeing the literal text that will land
is not a gate.

```
UPDATE CONTEXT — 2 candidates from this session

[1] {HUB}/context/team/conventions/REQUIRED/branches.md   (3 rules → 4)
    Heard: "we always put the ticket ID in the branch name"

    + ## Rule 4 — Ticket ID first in every branch name
    +
    + Start every branch name with the board item's identifier. If the work has no
    + board item yet, create it before you create the branch.
    + <!-- Added 2026-07-20 via /update-context: "we always put the ticket ID in the branch name" -->

[2] UNROUTED — no existing file covers release timing
    Heard: "we never merge on a Friday afternoon"
    Staging as a guidance candidate for the next /kb-synthesize drain.

Dropped: 1
  - "stop saying you're absolutely right" — P3: one person's preference, not a team rule.

Reply: 1  /  all  /  none  /  none, stop asking  /  2 → <path>  /  1 defer
```

The options, exactly:

| Reply | You do |
|---|---|
| a number, or `all` | Apply those diffs and leave the rest. |
| `none` | Apply nothing. Do not ask again this session. |
| `none, stop asking` | Apply nothing, create an empty `.awow/no-context-prompt`, confirm in one line, and never offer again in any session. |
| `N → <path>` | Retarget candidate N to that path and re-show its diff. An existing file only. |
| `N defer` | Stage candidate N in the inbox instead of writing it. |

On approval:

1. Apply each approved diff to its destination file under `{HUB}/context/team/`.
2. Write each deferred and each unrouted candidate to the resolved `inbox` — one file per
   candidate, following the schema in `{HUB}/context/kb-inbox/README.md` (falling back to
   `{AWOW_ROOT}/context/kb-inbox/README.md`): `kind: guidance`, `source: update-context`,
   `source_ref` naming this session's branch or PR, `suggested_target` set to the
   destination path or `UNROUTED`, and `source_quote` holding the verbatim sentence.
3. Commit both in one commit naming `/update-context` as the source. A staged candidate
   has to be committed to be seen — the drain reads committed state only.

Say in one line what landed and what was staged. Then stop; do not re-offer.

---

## Behavioral boundaries

- **Never write `.claude/CLAUDE.md`, `.github/copilot-instructions.md`, the root `AGENTS.md`, or `.agents/AGENTS.md`.** The first three are regenerated by `{AWOW_TOOLS}/gather.py` on every build, so a diff landed there is destroyed by the next one; the fourth is the team's own instruction source and is not yours to edit opportunistically. Write under `{HUB}/context/team/` and let propagation happen.
- **Never create a convention or style file.** No destination means tier 3, always.
- **Never write outside the gate**, and never treat an earlier session's approval as
  standing consent.
- **Never run autonomously.** There is no `--auto` mode and no unattended variant, for the
  same reason `{HUB}/context/knowledge-base/synthesis.md` parks one for the KB drain: a
  rule written into `{HUB}/context/team/` unattended binds everyone who opens a session
  afterwards.
- **Never paraphrase the quote.** If you cannot reproduce the sentence verbatim, drop the
  candidate.
- **Never invent a rule the user did not state**, and never widen one they scoped.
- **Once per session.** After you have offered, you are done, whatever else the session
  produces.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 tests/context-writes/test_context_writes.py`
Expected: `Instruction-file write targets OK.` and exit 0.

If check B fires instead, the `**Never write ...**` bullet was reflowed onto two lines. Rejoin it.

- [ ] **Step 5: Register the command in the phase catalogue**

`.agents/commands/README.md` is a hand-written source file (the generated one is `.claude/commands/README.md`). In its phase table, replace the `standardise` row — this is PR 2 Task 5 Step 6's post-edit text, which dropped `weekly-digest` (PR 2 deletes the command) and `project-manager` (PR 2 vendors it) and added the two `phase: standardise` commands that were missing:

```markdown
| `standardise` | Opt-in via `/awow-add <command>` (most of team active) | `daily-checkin`, `daily-digest`, `kb-mine`, `kb-synthesize` |
```

with:

```markdown
| `standardise` | Opt-in via `/awow-add <command>` (most of team active) | `daily-checkin`, `daily-digest`, `kb-mine`, `kb-synthesize`, `update-context` |
```

If the row still names `weekly-digest` or `project-manager`, PR 2 has not landed — stop and report. Appending `update-context` to the pre-PR-2 row would resurrect a deleted command and a vendored one in the catalogue `/awow-add` reads.

- [ ] **Step 6: Build and verify every surface picked the command up**

```bash
python tools/gather.py && python tools/lint-paths.py && python tools/gather.py --check
```

Expected: `Path tokens clean.` and `--check` exit 0. If the linter fails, a `context/` reference in the new body lost its token prefix — the linter does not exempt code fences.

```bash
ls .claude/commands/update-context.md \
   .github/prompts/update-context.prompt.md \
   dist/commands/update-context.md \
   dist/agent-skills/update-context/SKILL.md \
   dist/.github/prompts/update-context.prompt.md
```

Expected: all five paths listed, no errors. The last one exists because PR 1 generates `dist/.github/`.

Do not assert absolute counts here. A number measured against `main` is wrong the moment PR 2 deletes three commands and vendors two, and wrong again after PR 3 moves five skills to `dist-telemetry/`. Derive the expected set from the source tree — `.agents/commands/`, the legacy `commands/`, and `.agents/skills/`, minus whatever their `channel:` field excludes — and diff it against what the build actually emitted:

```bash
python3 - <<'PY'
from pathlib import Path

def channel(p):
    t = p.read_text()
    if not t.startswith("---\n"):
        return "both"
    end = t.find("\n---", 4)
    for line in (t[4:end] if end != -1 else "").splitlines():
        k, sep, v = line.partition(":")
        if sep and k.strip() == "channel":
            return v.strip()
    return "both"

ships = lambda p: channel(p) not in ("vendored", "telemetry")

agent_cmds = sorted(p for p in Path(".agents/commands").glob("*.md") if p.name != "README.md")
root_cmds = sorted(Path("commands").glob("*.md")) if Path("commands").is_dir() else []
shipped = [p for p in agent_cmds + root_cmds if ships(p)]

skills = set()
for e in sorted(Path(".agents/skills").iterdir()):
    if e.name == "README.md":
        continue
    if e.is_dir() and (e / "SKILL.md").is_file():
        if ships(e / "SKILL.md"):
            skills.add(e.name)
    elif e.is_file() and e.suffix == ".md" and ships(e):
        skills.add(e.stem)

def names(d, strip=""):
    p = Path(d)
    if not p.is_dir():
        return set()
    return {x.stem.removesuffix(strip) if strip else x.stem for x in p.glob("*.md")}

def dirs(d):
    p = Path(d)
    return {x.name for x in p.iterdir() if x.is_dir()} if p.is_dir() else set()

def cmp(label, expected, actual):
    if expected == actual:
        print(f"{label} OK ({len(expected)})")
        return
    print(f"{label} MISMATCH: derived {len(expected)}, found {len(actual)}")
    for n in sorted(expected - actual):
        print(f"    missing: {n}")
    for n in sorted(actual - expected):
        print(f"    extra:   {n}")

src = {p.stem for p in agent_cmds}
cmp("claude-commands", src | {"README"}, names(".claude/commands"))
cmp("copilot-prompts", src | {"README"}, names(".github/prompts", strip=".prompt"))
cmp("dist-commands", {p.stem for p in shipped}, names("dist/commands"))
cmp("dist-agent-skills", {p.stem for p in shipped} | skills, dirs("dist/agent-skills"))
cmp("dist-copilot-prompts", {p.stem for p in agent_cmds if ships(p)},
    names("dist/.github/prompts", strip=".prompt"))
PY
```

Expected: five `OK` lines, and `update-context` present in every derived set. With PRs 1-4 landed they read

```
claude-commands OK (23)
copilot-prompts OK (23)
dist-commands OK (17)
dist-agent-skills OK (21)
dist-copilot-prompts OK (16)
```

**The assertion is the word `OK`, not the number.** Landing PR 5 against a different predecessor set moves every count and none of that is a failure. A `MISMATCH` naming `update-context` as `missing` means the build did not pick the command up; a `MISMATCH` naming anything else means an earlier PR left a surface out of sync — stop and report either way rather than adjusting the number.

The two `.claude/` and `.github/` sets carry `README` because `plan_folder_readmes` (`gather.py:657-661`) generates a folder README into each; `dist/.github/prompts` derives from `.agents/commands/` only, because `plan_copilot_payload` does not walk the legacy `commands/` directory and so never emits `awowify`.

- [ ] **Step 7: Verify the rendered payload resolves and the frontmatter survived**

```bash
grep -c '{AWOW_ROOT}\|{HUB}' dist/commands/update-context.md
grep -n 'autofire' dist/commands/update-context.md
grep -c 'CLAUDE_PLUGIN_ROOT' dist/agent-skills/update-context/SKILL.md
head -4 dist/agent-skills/update-context/SKILL.md
```

Expected: the first grep reports `0` unsubstituted `{AWOW_ROOT}` and a non-zero count only if `{HUB}` is present — `{HUB}` ships as-is by design and `{AWOW_ROOT}` does not. The second shows `autofire: true` preserved by `plugin_command_copy`. The third prints `0`: Codex and Pi cannot resolve `${CLAUDE_PLUGIN_ROOT}`. The fourth shows `name: update-context` and the `description:` line — `command_skill_stub` emits those two fields only, so `phase`, `prerequisites`, and `autofire` are correctly absent there.

- [ ] **Step 8: Commit**

```bash
git add .agents/commands/update-context.md .agents/commands/README.md tests/context-writes/ .claude/ .github/ dist/
git commit -m "Add /update-context: the tenth autofire command, which routes rules stated in passing into the context tree behind one completion-edge gate showing the actual diff and the verbatim quote. Unroutable candidates stage as UNROUTED rather than inventing a convention file."
```

---

### Task 5: Full-suite verification

**Files:** none modified.

**Interfaces:**
- Consumes: everything above.
- Produces: the evidence that PR 5 is complete.

- [ ] **Step 1: Run every check CI runs, plus the three PR-1 and PR-5 additions**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/context-writes/test_context_writes.py \
  && python3 tests/gather-tokens/test_tokens.py \
  && python3 tests/payload-classification/test_classification.py \
  && bash tests/harness/run-harness-tests.sh all \
  && python3 tests/awow-lock/test_awow_lock.py \
  && python3 tests/hooks/test_lifecycle_seam_check.py
```

Expected: every one passes, ending with `all checks passed` from the harness runner and `OK` from the two `unittest` suites.

`tests/awow-lock/test_awow_lock.py` builds throwaway git repos and never reads this repo's `tools/awow.lock.json`, so adding a command does not affect it. The tracked lockfile is stale on `main` regardless — it says `awow_version: 0.2.0` and lists `cross-team-view.md`, which no longer exists — and §4.4 assigns its regeneration to PR 2. Do not regenerate it here.

- [ ] **Step 2: Confirm the reflex is now live**

PR 1 landed the noticing paragraph in `using-awow/SKILL.md` gated on this command existing. Confirm both halves are present and that the hook still injects cleanly:

```bash
test -e .agents/commands/update-context.md && echo "command present" || echo "MISSING"
grep -c 'update-context' .agents/skills/using-awow/SKILL.md
CLAUDE_PLUGIN_ROOT="$PWD" bash hooks/session-start | grep -c "Error reading" || true
```

Expected: `command present`, a non-zero count from the grep (PR 1's reflex paragraph names the command), then `0`. If the grep returns `0`, PR 1 did not land its Task 5 and this PR's front half is missing — stop and report rather than editing `SKILL.md` here.

- [ ] **Step 3: Confirm no prompt writes a generated instruction file**

```bash
grep -rn 'CLAUDE\.md\|copilot-instructions\.md' .agents/commands/ | grep -v 'setup-awow.md\|design-system.md\|update-context.md' | wc -l
```

Expected: `0`.

- [ ] **Step 4: Confirm no team data leaked and no context path went unclassified**

```bash
python3 tests/payload-classification/test_classification.py
git ls-files dist/ | grep -E 'context/(team|company|quarterly)/' | wc -l
```

Expected: `Payload classification OK.` then `0`. This PR adds no file under `context/`, so the manifests need no edit — but the two files it *modified* both classify `payload` and their `dist/` copies must have tracked the change, which the first command asserts.

- [ ] **Step 5: Report**

Summarise: files changed, the guard test added and what class of bug it blocks, the four commits, and the fact that `autofire: true` is inert until PR 4 lands the `dist/skills/` mirror. Do not open a PR and do not push — both need explicit approval.

---

## Self-Review

**Spec coverage.** §4.6 *Machinery* (the command, `autofire: true`, routing, format inference, diff generation, the gate, provenance) → Task 4. §4.6 *Queue* (`context/kb-inbox/` with `kind: guidance`) → Task 2. §4.6 *Queue* (`/kb-synthesize` grows a `kind: guidance` branch) → Task 3. §4.6 discrimination rule P1/P2/P3 and the scoping-word veto → Task 4, Phase 1. §4.6 interrupt budget and the once-per-session completion-edge gate → Task 4, *When you run* and Phase 4. §4.6 three-tier routing with `UNROUTED` terminal → Task 4, Phase 2, and Task 3's *unroutable* disposition. §4.6 hard prohibitions → Task 4, *Behavioral boundaries*, enforced by Task 1's guard test. §4.6 *Fix the same bug in `/process-retro`* → Task 1. §4.6 accretion duty (ten-rule cap, merge-or-replace) → Task 4, Phase 2 and Task 3, Step 2. §4.6 under-firing visibility (`"Nothing captured this session."`) → Task 4, Phase 0. §4.6 *Never autonomous* → Task 3, Step 4 and Task 4, *Behavioral boundaries*. §4.5 format constraint (single-line, double-quoted, no block scalar) → Task 4, Step 1's check C. §10 `phase: standardise`, opt-in via `/awow-add` → Task 4, Steps 3 and 5.

**Deliberately not here.** `.agents/skills/using-awow/SKILL.md` is untouched — §10 consolidates every edit to it into PR 1, and Task 5 Step 2 verifies rather than writes. Nothing this PR does depends on PR 4: `autofire: true` is inert data until PR 4 teaches `gather.py:517` to read it, and §10 states PR 5 must not delay the README. `tools/awow.lock.json` is stale on `main` and stays that way; §4.4 gives its regeneration to PR 2, and regenerating it here would collide with that diff. `context/team/style/placement.md:27`'s parked `style/` vs `conventions/` canonicality question is untouched — §4.6 names resolving it as out of scope, which is exactly why Phase 2 tier 2 exists.

**Three things the spec is wrong about, verified against the code.**

1. **The `/process-retro` line numbers are wrong.** §4.6 says *"`process-retro.md:264`, `:284`, `:324` all target `CLAUDE.md` / `copilot-instructions.md` directly."* Line 324 does not: it reads *"For each diff approved at Gate 2, edit the target file."* — generic, no filename. The third site is **line 10**, the command's opening sentence, which the spec missed: *"…concrete diffs proposed for `CLAUDE.md` / `copilot-instructions.md`."* The real set is `:10`, `:264`, `:284`. Task 1 fixes all three and additionally rewrites `:323-328` (section 3.2) — not because it named a mirror, but because retargeting to `.agents/AGENTS.md` without a `gather.py` run leaves the repo out of sync and fails `--check`. This is the third such correction on this spec, and it is why Task 1 leads with a test rather than a grep: the guard finds the sites itself and cannot be wrong about which lines they are on.

2. **`gather.py:336-337` is right about the content but the spec calls it the mirror site loosely.** Verified: `plan_top_level` spans `gather.py:333-341`, and `:336-337` are the `.claude/CLAUDE.md` and `.github/copilot-instructions.md` entries. Root `AGENTS.md` is generated three lines later at `:339-340` and `.github/AGENTS.md` at `:338`. The prohibition in Task 4 names all four because the spec's prohibition list does.

3. **§7's description table omits `/update-context` entirely.** §4.5 lists it as the tenth autofire command and §4.6 specifies it fully, but §7 has sixteen rows and none is this command — a leftover from v3 adding §4.6 after §7 was written. Resolved by writing the description in this PR (Task 4, decision 1) rather than leaving the command to advertise itself by H1 fallback.

**One spec tension, resolved and worth naming.** §4.6 prohibits `/update-context` from writing `.agents/AGENTS.md`, and in the same bullet list instructs `/process-retro` to write exactly that file. Both hold, and the rule that generates the difference is the evidence standing behind the write: `/process-retro` has a whole transcript, a 13-section report, and two explicit human gates behind each diff; `/update-context` has one overheard sentence at a completion edge. The former earns an instruction-level edit, the latter earns a convention-file edit that propagates through `context/`. Task 4's prohibition bullet states this in one clause so the next reader does not treat it as an inconsistency and "fix" it.

**Placeholder scan.** Zero `TODO`, `TBD`, `<name>`-style fill-ins, or "as in Task N" back-references in any code or content step. Three decisions the spec left open were resolved in Task 4's preamble rather than deferred: who writes the `description:` (this PR), why it contains no inner double quotes (`parse_frontmatter` does not unescape), and whether `.awow/no-context-prompt` gets a `.gitignore` entry (no — PR 2 Task 9 Step 5 ignores all of `.awow/`, so a per-file rule under it is dead text). One near-placeholder was caught and removed while writing: Task 4's Phase 3 originally cited `.agents/skills/agent-directive-voice.md` as a markdown link, which resolves to nothing in a plugin install *and* points at a `channel: vendored` file that never ships. The voice rule is now stated inline with the file cited as a where-available reference.

**Type consistency.** `check_mirror_mentions() -> None`, `check_update_context_frontmatter() -> None`, and `check_retro_still_closes_the_loop() -> None` all append to the module-level `FAILURES: list[str]` and are called from `main() -> int`, matching the shape of `tests/gather-tokens/test_tokens.py` and `tests/payload-classification/test_classification.py`. `ALLOWED: dict[str, str]` is keyed by bare filename (`path.name`), not by relative path, so it stays correct if a command moves into a subdirectory of `.agents/commands/`. The frontmatter values compared in check C are the raw post-`partition` strings — `"standardise"` and `"true"` — not booleans; `parse_frontmatter` (`gather.py:326-341`) also stores every value as a string, so the test and the build agree on the type. The disposition names `novel` / `sharpens` / `covered` / `contradicts` / `unroutable` / `thin` appear with those exact spellings in Task 3 Steps 2 and 5c. `UNROUTED` is spelled that way — uppercase, no underscore — in Task 2, Task 3, and Task 4 alike.

**Task boundaries.** Five tasks, four commits, each independently rejectable. Task 1 is a standalone bug fix with its own test and could ship alone against `main`; a reviewer who rejects the whole `/update-context` design should still take it. Tasks 2 and 3 split on the same seam the codebase already uses — schema first, then the contract and the command that reads it — so a reviewer can reject the disposition set without rejecting the frontmatter key. Task 4 is the command, and its README-table row rides with it because a command absent from the phase catalogue is invisible to `/awow-add`, which is the only way a `phase: standardise` command gets adopted. Task 5 adds no code; it exists because the eight-command verification run is what proves the PR, and folding it into Task 4 would let it be skipped.
