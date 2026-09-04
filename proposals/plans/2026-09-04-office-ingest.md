# Office Ingestion via markitdown — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Commands that read team inputs can open `.docx`, `.pptx`, `.xlsx` and `.xls` files through a provenance-stamped markdown sidecar that markitdown writes once beside the source.

**Architecture:** One new packaged skill (`office-ingest`, prose only — the markitdown CLI is the deterministic helper) plus one-line routes in the session reflex, AGENTS.md and three reading commands, and a documented sidecar convention in the quarterly folder. Verification is two scenarios added to the existing `tests/process-transcript/` suite against a frozen `.docx` fixture.

**Tech Stack:** markitdown 0.1.x via `uvx` (verified 0.1.7), Python 3.10+ (`hashlib` for SHA-256), bash eval suites under `tests/`, `tools/gather.py`.

**Spec:** `proposals/office-ingest-design.md` — verbatim blocks below are quoted from it; the spec wins on disagreement.

**Board item:** [CAU-1526](https://linear.app/cauchyio/issue/CAU-1526/implement-office-file-ingestion-through-markitdown-sidecars). Branch: `arie/cau-1526-implement-office-file-ingestion-through-markitdown-sidecars`.

## Global Constraints

- Sidecar name is `<file>.<ext>.md` beside the source; header is exactly `source`, `source_sha256`, `converted`, `converter`. (spec §2.1–2.2)
- Freshness is SHA-256 of the source, never mtime; a matching hash means no markitdown call. (spec §2.3, D5)
- Command ladder: `uvx --from "markitdown[docx,pptx,xlsx,xls]" markitdown …` → PATH `markitdown` → one install offer → ask for PDF/pasted text. (spec §3.2)
- The skill never stages or commits; sidecar tracking follows the source via `git check-ignore`. (spec §2.4, D7)
- PDF is not routed through markitdown. (spec D6)
- Prompt bodies use `{ANCHOR}` tokens, never bare `context/` (`python tools/lint-paths.py`); voice per `.agents/skills/agent-directive-voice.md`.
- Eval exec bits: `setup/*.sh` executable; `checks/*.sh` NOT executable. `python tools/validate-evals.py` gates.
- No CHANGELOG edit; the PR title carries `CAU-1526:` and a one-line summary.
- Commit trailer on every commit:
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`
  `Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej`

---

## File structure

| Path | Responsibility | Task |
|---|---|---|
| `.agents/skills/office-ingest/SKILL.md` | the sidecar contract, command ladder, tracking and fidelity rules | 1 |
| `.agents/skills/README.md` | list + example row | 1 |
| `.agents/skills/using-awow/SKILL.md`, `.agents/AGENTS.md` | route: Office file in hand → office-ingest | 2 |
| `.agents/commands/refinement-prep.md`, `process-transcript.md`, `strategy-flow.md` | one delegating line each; quarterly path fix | 3 |
| `context/quarterly/README.md`, `context/quarterly/INPUT.md` | the sidecar convention for people dropping files | 4 |
| `tests/process-transcript/{fixtures,scripts,rubrics,checks,setup}/{docx-notes,stale-sidecar}*`, `README.md`, `suite.md` | two scenarios | 5 |
| `proposals/README.md`, `proposals/office-ingest-design.md` | status bookkeeping | 6 |

---

### Task 0: Branch and board

- [ ] **Step 1:** CAU-1526 exists and is In Progress.
- [ ] **Step 2:** From `arie/word-export-office-ingest-specs` (which carries the spec and this plan): `git checkout -b arie/cau-1526-implement-office-file-ingestion-through-markitdown-sidecars`. Independent of the word-export branch; the second PR to merge rebases and regenerates `dist/`.
- [ ] **Step 3:** Move the item to In Progress with the comment "Implementation started; plan at proposals/plans/2026-09-04-office-ingest.md".

---

### Task 1: `office-ingest/SKILL.md`

**Files:**
- Create: `.agents/skills/office-ingest/SKILL.md`
- Modify: `.agents/skills/README.md` (line 39 base-plugin list; packaged-skill examples)

**Interfaces:**
- Produces: skill name `office-ingest`, named by Tasks 2–4.

- [ ] **Step 1: Write `SKILL.md`** — spec §4 verbatim, from the frontmatter `name: office-ingest` through the `## Boundaries` list ending `Local CLI only.`
- [ ] **Step 2: Skills README.** Add `office-ingest` to the base-plugin sentence on line 39 (after `knowledge-source-routing`), and add to the packaged-skill examples:

```markdown
- [`office-ingest/`](./office-ingest/) — read `.docx`/`.pptx`/`.xlsx` through a provenance-stamped markdown sidecar written once by markitdown and reused until the source changes. No script; the CLI is the helper.
```

- [ ] **Step 3: Gates.** `python tools/lint-paths.py` → 0; `python tools/gather.py && python tools/gather.py --check` → 0; `ls dist/skills/office-ingest/SKILL.md dist/agent-skills/office-ingest/SKILL.md` both exist; `python3 tests/telemetry-split/test_telemetry_split.py` → 0 (no `channel:` means base plugin).
- [ ] **Step 4: Smoke the ladder by hand** on the probe from the spec: in a scratch dir, `pandoc` any small markdown to `x.docx`, then run the skill's rung-1 command and confirm `x.docx.md` appears with headings intact. (This is the only manual check; the suite in Task 5 covers it end to end.)
- [ ] **Step 5: Commit.**

```bash
git add .agents/skills/office-ingest .agents/skills/README.md dist
git commit -m "CAU-1526: office-ingest skill — Office files read through a provenance-stamped markitdown sidecar" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 2: Routes in the reflex and AGENTS.md

**Files:**
- Modify: `.agents/skills/using-awow/SKILL.md` §Route to the moment (line 44 paragraph)
- Modify: `.agents/AGENTS.md` §Where to read context (bullet list, lines 11–14)

- [ ] **Step 1: Reflex.** In the §Route to the moment paragraph, before the final sentence `Reach for the catalog in your skill listing before hand-rolling.`, insert: `A `.docx`, `.pptx` or `.xlsx` in hand → the `office-ingest` skill first, then the command the content calls for.`
- [ ] **Step 2: AGENTS.md.** After the **Tooling reference** bullet add:

```markdown
- **Office inputs:** a `.docx`, `.pptx`, `.xlsx` or `.xls` anywhere in the context tree is read through its markdown sidecar (`<file>.<ext>.md`) — the `office-ingest` skill creates and refreshes it; never read the binary directly
```

- [ ] **Step 3: Gates.** `python tools/gather.py && python tools/gather.py --check`; `python3 tests/hooks/test_session_start.py` (the reflex text is injected by the hook; the test asserts wording it cares about — if it fails on the new sentence, the test lists the asserted phrases; do not delete assertions, adjust the sentence).
- [ ] **Step 4: Commit.**

```bash
git add .agents/skills/using-awow/SKILL.md .agents/AGENTS.md dist
git commit -m "CAU-1526: route Office files to office-ingest from the reflex and AGENTS.md" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 3: Delegations in the three reading commands

**Files:**
- Modify: `.agents/commands/refinement-prep.md` §Inputs (line ~37)
- Modify: `.agents/commands/process-transcript.md` §1.1 (lines ~78–84)
- Modify: `.agents/commands/strategy-flow.md` Phase 0 (line ~35)

- [ ] **Step 1: refinement-prep.** Replace the bullet `- A slidedeck or document in `input/quarterly/` to extract from` with `- A slidedeck or document in `{ANCHOR}/context/quarterly/` to extract from — Office files through the `office-ingest` skill; read the sidecar it produces`.
- [ ] **Step 2: process-transcript.** After the `- **SRT** (`.srt`) …` bullet add `- **Word notes** (`.docx`) — convert through the `office-ingest` skill, then treat the sidecar as Plain text / Markdown.` Change `Read the file at `$ARGUMENTS`. Support:` to `Read the file at `$ARGUMENTS`; an Office extension routes through `office-ingest` before parsing. Support:`.
- [ ] **Step 3: strategy-flow.** Change `…and everything under `{ANCHOR}/context/quarterly/`.` to `…and everything under `{ANCHOR}/context/quarterly/`, Office files through their `office-ingest` sidecars.`
- [ ] **Step 4: Gates.** `python tools/lint-paths.py`; `python3 tests/command-frontmatter/test_frontmatter.py`; `python tools/gather.py && python tools/gather.py --check`; `python3 tests/payload-commands/test_command_surface.py`; `python3 tests/payload-commands/test_strategy_routing.py`.
- [ ] **Step 5: Commit.**

```bash
git add .agents/commands/refinement-prep.md .agents/commands/process-transcript.md .agents/commands/strategy-flow.md dist
git commit -m "CAU-1526: refinement-prep, process-transcript and strategy-flow read Office inputs via office-ingest; quarterly path corrected" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 4: Quarterly folder convention

**Files:**
- Modify: `context/quarterly/README.md` (new section after `## Naming`, before `## What to drop here`)
- Modify: `context/quarterly/INPUT.md` (same position)

- [ ] **Step 1:** Insert in both files:

```markdown
## Office files

Drop the `.pptx`, `.docx` or `.xlsx` as-is. On first read the agent writes `<file>.<ext>.md` beside it — markitdown's conversion under a four-line provenance header — and reads that. Commit the pair together; the sidecar is regenerated whenever the source changes, and is never edited by hand. If the source is gitignored, the sidecar is too.
```

- [ ] **Step 2: Gates.** `python tools/gather.py --check` (context ships in the payload); `python3 tests/payload-classification/test_classification.py`.
- [ ] **Step 3: Commit.**

```bash
git add context/quarterly dist
git commit -m "CAU-1526: document the Office sidecar convention in the quarterly folder" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 5: Two scenarios in `tests/process-transcript/`

**Files:**
- Create: `tests/process-transcript/fixtures/docx-notes/{setup-progress.md,context/tooling/board.md,notes/notes.md,notes/notes.docx}`
- Create: `tests/process-transcript/fixtures/stale-sidecar/…` (same + `notes/notes.docx.md` stale)
- Create: `tests/process-transcript/fixtures/make-office-fixtures.sh` (executable)
- Create: `scripts/{docx-notes,stale-sidecar}.txt`, `rubrics/{docx-notes,stale-sidecar}.md`, `checks/{docx-notes,stale-sidecar}.sh` (NOT executable), `setup/{docx-notes,stale-sidecar}.sh` (executable)
- Modify: `tests/process-transcript/README.md` (scenarios + invariants), `tests/process-transcript/suite.md` (scenario list sentence)

- [ ] **Step 1: Fixture source.** `fixtures/docx-notes/notes/notes.md`:

```markdown
# Refinement notes — team sample

Dana: the export-job retry budget (PB-1) is code-complete and in review since this morning — move it to In Review.
Priya: the CSV importer spike (PB-2) is superseded by the retry work; propose we cancel it.
Dana: agreed. New item: cap the export payload at 10 MB and reject anything larger — straight to Todo.
Priya: I'll take the 10 MB cap once PB-1 lands.
```

Copy `fixtures/plan-gate/setup-progress.md` and `fixtures/plan-gate/context/tooling/board.md` verbatim into `fixtures/docx-notes/` (same board: PB-1 In Progress, PB-2 Todo).

- [ ] **Step 2: Generator** `fixtures/make-office-fixtures.sh` (`chmod +x`; needs pandoc; CI never runs it):

```bash
#!/usr/bin/env bash
# Build notes.docx once from notes.md, mirror the docx-notes fixture into
# stale-sidecar with a deliberately stale sidecar, and print the docx's
# SHA-256 — paste it into checks/docx-notes.sh and checks/stale-sidecar.sh.
set -euo pipefail
cd "$(dirname "$0")"
pandoc docx-notes/notes/notes.md --from gfm --to docx -o docx-notes/notes/notes.docx
rm -rf stale-sidecar && mkdir -p stale-sidecar && cp -R docx-notes/. stale-sidecar/
cat > stale-sidecar/notes/notes.docx.md <<'MD'
---
source: notes.docx
source_sha256: 0000000000000000000000000000000000000000000000000000000000000000
converted: 2026-01-01
converter: markitdown 0.1.7
---
STALE
MD
python3 -c "import hashlib,sys;print('SHA256', hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" docx-notes/notes/notes.docx
```

Run it once. Copy the printed hash; it is `<HASH>` below. `notes.docx` is frozen from here on — never regenerate it without updating both checks files. Confirm `git check-ignore tests/process-transcript/fixtures/docx-notes/notes/notes.docx` prints nothing.

- [ ] **Step 3: Scripts.**

`scripts/docx-notes.txt`:

```
# Office input: sidecar written with provenance, read for Gate 1; second run reuses it (no second markitdown call).
Process the refinement notes at notes/notes.docx against our board (context/tooling/board.md). Stop after GATE 1 — I only want the segment read for now.
Process notes/notes.docx again the same way, stop after GATE 1.
```

`scripts/stale-sidecar.txt`:

```
# A stale sidecar (hash mismatch) is reconverted, not read.
Process the refinement notes at notes/notes.docx against our board (context/tooling/board.md). Stop after GATE 1.
```

- [ ] **Step 4: Rubrics.**

`rubrics/docx-notes.md`:

```markdown
# Rubric — docx-notes

1. [sidecar-first] Before parsing, did the run route `notes/notes.docx` through the office-ingest skill rather than attempting to read the binary?
2. [provenance] Was `notes/notes.docx.md` written with exactly the four header keys (`source`, `source_sha256`, `converted`, `converter`) above markitdown's body?
3. [gate-read] Did GATE 1 attribute statements to Dana and Priya from the sidecar's content?
4. [reuse] On the second request, did the run compute the hash, find it matching, and proceed from the existing sidecar with no second markitdown invocation in the tool-call list?
5. [quiet] Did the run avoid a fidelity warning (the fixture has no checklists, code, or images to lose)?
```

`rubrics/stale-sidecar.md`:

```markdown
# Rubric — stale-sidecar

1. [freshness] Did the run hash `notes.docx`, compare it to the sidecar's `source_sha256`, and treat the mismatch as "reconvert"?
2. [no-stale-read] Was the word `STALE` never treated as meeting content at GATE 1?
3. [no-ask] Did the run reconvert without asking permission (a stale sidecar is not a user decision)?
4. [provenance] Does the rewritten header carry the real hash and today's date?
```

- [ ] **Step 5: Checks** (NOT executable). Replace `<HASH>` with the value from Step 2.

`checks/docx-notes.sh`:

```bash
# Checks — docx-notes. Mechanical facts: fixture intact before; sidecar with
# provenance after. Reuse on the second turn is the rubric's (tool-call evidence).

pre() {
  file-exists notes/notes.docx
  file-absent notes/notes.docx.md
  file-exists context/tooling/board.md
}

post() {
  file-exists notes/notes.docx.md
  file-contains notes/notes.docx.md "^source: notes.docx$"
  file-contains notes/notes.docx.md "^source_sha256: <HASH>$"
  file-contains notes/notes.docx.md "^converted: [0-9]{4}-[0-9]{2}-[0-9]{2}$"
  file-contains notes/notes.docx.md "^converter: markitdown "
  file-contains notes/notes.docx.md "Priya"
}
```

`checks/stale-sidecar.sh`:

```bash
# Checks — stale-sidecar. The stale header must be gone, the real hash present.

pre() {
  file-exists notes/notes.docx
  file-exists notes/notes.docx.md
  file-contains notes/notes.docx.md "^source_sha256: 0{64}$"
  file-contains notes/notes.docx.md "^STALE$"
}

post() {
  file-contains notes/notes.docx.md "^source_sha256: <HASH>$"
  file-not-contains notes/notes.docx.md "0{64}"
  file-not-contains notes/notes.docx.md "^STALE$"
  file-contains notes/notes.docx.md "Priya"
}
```

- [ ] **Step 6: Setup hooks** — two identical executable files `setup/docx-notes.sh` and `setup/stale-sidecar.sh`:

```bash
#!/usr/bin/env bash
# git-init the fixture repo, then require a markitdown runner: without uv or
# markitdown on PATH the scenario cannot measure the prompt, so exit 1 and let
# the runner compose indeterminate (stage: setup) instead of a graded fail.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
if ! command -v uv >/dev/null 2>&1 && ! command -v markitdown >/dev/null 2>&1; then
  echo "setup: neither uv nor markitdown on PATH — cannot run office-ingest scenarios" >&2
  exit 1
fi
```

`chmod +x tests/process-transcript/setup/docx-notes.sh tests/process-transcript/setup/stale-sidecar.sh`.

- [ ] **Step 7: Suite docs.** In `README.md` add rows to the Scenarios table (`docx-notes` — "reading the binary directly; sidecar without provenance; a second markitdown call on an unchanged source"; `stale-sidecar` — "a stale sidecar read as the meeting; asking permission to reconvert") and the invariants `sidecar-first`, `provenance`, `reuse`, `freshness`, `no-stale-read` to the Invariants list; note the `uv`/markitdown requirement and the frozen `notes.docx`. In `suite.md` extend the Scenarios sentence with the two names.
- [ ] **Step 8: Static gate.** `python tools/validate-evals.py` → 0.
- [ ] **Step 9: Run.** `/test-awow process-transcript docx-notes` and `/test-awow process-transcript stale-sidecar` (payload from this branch: `python tools/gather.py && claude --plugin-dir dist`). Expected PASS both; `INDETERMINATE(setup)` on a machine without `uv`. Also re-run `plan-gate` and `stale-move` to prove the process-transcript edit in Task 3 did not regress them. Paste the `OVERALL:` line into the board item.
- [ ] **Step 10: Commit.**

```bash
git add tests/process-transcript
git commit -m "CAU-1526: process-transcript scenarios docx-notes and stale-sidecar for office-ingest" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 6: Bookkeeping and PR

- [ ] **Step 1:** `proposals/README.md` row `office-ingest-design` → `**Landed** (PR #<n>, <date>)`; `office-ingest-design.md` Status → `Implemented <date>; board item CAU-1526; PR #<n>.`
- [ ] **Step 2: Full local gate** — same CI list as the word-export plan Task 9 Step 2 (minus the artifact-render test if that branch is not merged yet), plus `python tools/validate-evals.py`.
- [ ] **Step 3: Commit, push, PR.**

```bash
git add proposals
git commit -m "CAU-1526: mark office-ingest landed" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
git push -u origin arie/cau-1526-implement-office-file-ingestion-through-markitdown-sidecars
gh pr create --title "CAU-1526: Office inputs read through markitdown sidecars (office-ingest skill)" --body-file <(printf '%s\n' "Spec: proposals/office-ingest-design.md — plan: proposals/plans/2026-09-04-office-ingest.md." "" "- office-ingest skill: sidecar <file>.<ext>.md with source/sha256/date/converter header; uvx-first ladder; tracking follows the source." "- Routes in the reflex, AGENTS.md, refinement-prep, process-transcript, strategy-flow; quarterly README documents the convention." "- Two process-transcript scenarios: docx-notes, stale-sidecar." "" "🤖 Generated with [Claude Code](https://claude.com/claude-code)" "" "https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej")
```

- [ ] **Step 4: Board.** Move CAU-1526 to In Review with the PR link and the `OVERALL:` line.
