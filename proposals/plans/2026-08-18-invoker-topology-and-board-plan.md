# Invoker topology and board plan — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement AWO-204 (hat-aware `/setup-awow`), AWO-205 (BOARD PLAN gate grammar in `workitem-write`), and AWO-206 (invoker profile + resolution rungs + `board-scope.md` schema) per the approved spec.

**Architecture:** This is prompt engineering, not application code: the deliverables are markdown rule files under `.agents/`, mirrored to harness surfaces by `tools/gather.py`, plus eval-suite regression witnesses under `tests/` in the repo's established fixture format (deterministic shell checks + a blind judge, run via `/test-awow`). All work stacks on PR #44's branch because it already rewrote the two central files.

**Tech Stack:** Markdown prompts (`.agents/commands/`, `.agents/skills/`), Python build tools (`tools/gather.py`, `tools/validate-evals.py`), bash eval fixtures (`tests/<suite>/`).

**Spec:** `proposals/invoker-topology-and-board-plan.md` (read it first; the plan argues from it).

## Global Constraints

- **Base branch:** create the working branch from `origin/proposal/context-resolution` (PR #44), never from `main` — PR #44 already modified `.agents/AGENTS.md` (§Context resolution) and `.agents/skills/workitem-write/SKILL.md`, and this work extends both. Branch name: `casper/invoker-topology-and-board-plan`.
- **Public repo:** commits stay local. Never push, open a PR, or merge without explicit user approval in the conversation.
- **Voice:** every edit under `.agents/` follows `.agents/skills/agent-directive-voice.md` — second-person imperative, two sentences max per rule, no evidence inside imperatives.
- **Mirrors:** after any `.agents/` edit, run `.venv/bin/python tools/gather.py` and include the regenerated mirrors (`dist/`, `.claude/`, `.github/`, `.opencode/`) in the same commit.
- **Eval hygiene:** after any `tests/` change, `.venv/bin/python tools/validate-evals.py` must pass.
- **Commits:** message ≤2 sentences, prefixed with the issue id (`AWO-205: …`). Co-author trailer per harness rules.
- **Path tokens:** prompt bodies use `{HUB}` / `{PROJECT}` tokens, never literal repo paths (`setup-awow.md` is `channel: bootstrap` and exempt for the literal paths it must create).
- **No client or engagement names** anywhere in prompts, fixtures, or commits.
- **Board:** AWO-204/205/206 are In Progress for the duration; each task's commit references its issue.

---

### Task 0: Worktree and branch

**Files:** none (environment only).

- [ ] **Step 1: Create an isolated worktree** via the `superpowers:using-git-worktrees` skill (native worktree tools preferred).
- [ ] **Step 2: Branch off PR #44**

```bash
git fetch origin proposal/context-resolution
git checkout -b casper/invoker-topology-and-board-plan origin/proposal/context-resolution
```

- [ ] **Step 3: Verify baseline** — `git log --oneline -1` shows a PR #44 commit; `grep -n "Context resolution" .agents/AGENTS.md` finds the section (it exists only on this branch). `uv sync --python 3.12` if `.venv/` is absent in the worktree.

---

### Task 1: BOARD PLAN grammar in `workitem-write` (AWO-205)

**Files:**
- Modify: `.agents/skills/workitem-write/SKILL.md` (PR #44 baseline — it has an extra index-form paragraph in step 1)

**Interfaces:**
- Produces: the literal strings `BOARD PLAN`, option verbs `go / skip N / details N / review / cancel`, the `because:` provenance line, the `stale — board changed since plan` report phrase, and the DONE report shape. Tasks 2–4 and the eval rubrics reference these exact strings.

- [ ] **Step 1: Extend step 1 (Look first)** — append this paragraph to §1, after the PR #44 index-form paragraph:

```markdown
**Record the pre-image.** For every item you may change, record what you just read — current state, title, and the body section a change would touch. This snapshot is the board plan's "before"; step 5 re-verifies it line by line.
```

Also append this sentence to the first paragraph of §1 (after "…recency (items updated in the last two cycles).", as its own sentence): `When board.md declares a board-team filter for a shared board, scope reads to the filter but run the duplicate search board-wide — a duplicate across teams is still a duplicate.`

- [ ] **Step 2: Extend step 3 (Shape the body)** — add a fourth bullet:

```markdown
- **Source every action.** Record where each proposed action comes from — the transcript segment, user statement, board item, or convention that motivates it. Step 4 refuses a line with no source.
```

- [ ] **Step 3: Replace step 4 (Gate) in full** — replace everything from `## 4. Gate` up to (not including) `## 5. Write + report` with:

````markdown
## 4. Gate — the board plan

Creating an item, moving state, or editing a body requires explicit approval in this conversation; linking an existing item and commenting do not. Present every batch of gated actions as one **board plan**: a fenced `diff` block, one numbered line per action, a counts footer.

```diff
BOARD PLAN · board: <name> [<tool>]

+ 1  <Type> "<Title>"   → <initial state>
~ 2  <ID>  body: <what changes>
~ 3  <ID>  <from> → <to>
- 4  <ID>  close — <reason>

Plan: <n> add · <n> change · <n> close
```

- Symbols: `+` create, `~` any change to an existing item, `-` close or cancel. Use no other symbols.
- Change phrase by action — create: `→ <initial state>`, plus `↳ under <line|ID>` when parented; body edit: `body: <what changes>`, naming the section touched, ten words or fewer; state move: `<from> → <to>`; field or label: `<field>: <old> → <new>`; close: `close — <reason>`.
- One line per item: join multiple facets with ` · `; keep a line under ~100 characters and truncate with `…` — the remainder belongs to `details`.
- A plan spanning boards suffixes each line with `[<board>]` and breaks the footer down per board; a single-board plan omits both.
- Comments and links are not plan lines; they appear only in the step-5 report.
- KB writes and escalations proposed alongside board actions: list them under the diff block as `KB <n>  <path> — <one-line>` and `ESCALATE <n>  <edge> → <action>`, numbering continuing the plan, and extend the footer (`· <n> kb · <n> escalate`).

Offer the standard options and wait; execute only what was explicitly approved:

```
"go"        — execute all
"skip 2,3"  — execute all except listed
"details 3" — show one line's full draft, then re-offer these options
"review"    — walk through each
"cancel"    — no changes
```

**`details N`** prints, by action type — create: the full draft body as it would land plus the conventions that shaped it; body edit: an old/new diff of only the touched sections; move or field: current value, target value, rationale; close: the reason and what supersedes it. End every details view with `because: <source>` — the provenance line — and never execute anything from inside `details`.

**Provenance.** Every plan line must trace to a source (transcript segment, user statement, board item, convention); do not propose a line you cannot source. `details` and `review` surface each line's `because:`.

The plan is ephemeral: never write it to a file and never keep it after execution — the board is the only truth.
````

- [ ] **Step 4: Extend step 5 (Write + report)** — replace the sentence `Re-verify each item match before touching it; if an item changed since discovery, pause and ask.` with:

```markdown
Re-verify each line's pre-image before touching its item — a move re-reads the current state, a body edit re-reads the touched section. On mismatch, do not apply the line: report `stale — board changed since plan` with the fresh value and move on; never force, never merge silently. Apply parented creates parent-first; a failed parent skips its children, reported as skipped.
```

- [ ] **Step 5: Voice check** — re-read the edited file against `agent-directive-voice.md`: every sentence imperative, addressed to the agent, ≤2 sentences per rule.
- [ ] **Step 6: Gather and verify** — run `.venv/bin/python tools/gather.py`; `git status` shows the three mirrors of `workitem-write/SKILL.md` updated (`dist/commands|skills|agent-skills` as applicable).
- [ ] **Step 7: Commit**

```bash
git add .agents/skills/workitem-write/SKILL.md dist/ .claude/ .github/ .opencode/
git commit -m "AWO-205: replace the workitem-write gate with the flat diff-style board plan — one numbered line per action, details-with-provenance, and a stale-guard on apply. Spec: proposals/invoker-topology-and-board-plan.md Pillar 4."
```

---

### Task 2: `/process-transcript` delegates its gate (AWO-205)

**Files:**
- Modify: `.agents/commands/process-transcript.md:308-328` (the `>>> GATE 2` block)

**Interfaces:**
- Consumes: `BOARD PLAN` grammar and option verbs from Task 1.

- [ ] **Step 1: Replace the GATE 2 block** — replace everything from `### >>> GATE 2: Approve actions` down to (and including) the line `Present the standard options, then gate per workitem-write step 4.` with:

```markdown
### >>> GATE 2: Approve actions

Stop here. Render the board plan per `workitem-write` step 4 over everything Phase 3 proposed: updates, moves, and creates as plan lines; KB promotions and escalations as `KB` / `ESCALATE` lines under the block; housekeeping folded into `~` lines or dropped. Set each line's `because:` to the transcript segment that motivates it. Open with one mapping line above the block — `[N] matched to existing items | [N] new | [N] cross-team deps | [N] untracked` — then offer the standard options and gate per `workitem-write` step 4.
```

- [ ] **Step 2: Voice check** the new block; **gather**; verify mirrors regenerated.
- [ ] **Step 3: Commit**

```bash
git add .agents/commands/process-transcript.md dist/ .claude/ .github/ .opencode/
git commit -m "AWO-205: GATE 2 renders the shared board plan instead of the hand-rolled verb-grouped summary."
```

---

### Task 3: `/daily-checkin`, `/project-plan`, `/project-manager` delegate (AWO-205)

**Files:**
- Modify: `.agents/commands/daily-checkin.md:198-204` (Section 5)
- Modify: `.agents/commands/project-plan.md:136-158` (GATE 2 block)
- Modify: `.agents/commands/project-manager.md:94`

**Interfaces:** consumes Task 1's grammar; changes are pure delegation.

- [ ] **Step 1: daily-checkin Section 5** — replace the block from `After clarification, ask:` through `…stop on mid-execution ambiguity.` with:

```markdown
After clarification, render the board plan per `workitem-write` step 4 over the proposed updates — each entry one plan line, its `because:` pointing at the day's evidence (commit, PR, account line) — then ask:

> Should I execute these updates on the board?

Gate and execution per `workitem-write` steps 4–5: explicit approval, pre-image re-check per line, execute exactly as approved, stop on mid-execution ambiguity.
```

- [ ] **Step 2: project-plan GATE 2** — inside the `### >>> GATE 2: Approve writes` section, replace the fenced `GATE 2 — PROPOSED WRITES` template and the sentence after it with:

```markdown
Stop here. Name the plan artefact path (`{PROJECT}/proposals/plans/<slug>.md`), then render the board plan per `workitem-write` step 4 over the board actions — creates carry `↳ under <line|ID>` and a `← blocked by: <item>` facet, links to existing items are `~` lines — with `ESCALATE` lines beneath and one edge-encoding note after the block (`native blocked-by links | body "Blocked by:" lines`). Present the standard options, then gate and execute per `workitem-write` steps 4–5.
```

- [ ] **Step 3: project-manager** — replace the sentence `Board writes gate and execute per workitem-write steps 4–5. Check-in messages and escalations go out exactly as approved — stop on ambiguity, no silent changes.` with:

```markdown
Render graph corrections, nudges, and board actions as one board plan per `workitem-write` step 4; keep check-in messages verbatim above it and escalations as `ESCALATE` lines beneath it. Board writes gate and execute per `workitem-write` steps 4–5; check-ins and escalations go out exactly as approved — stop on ambiguity, no silent changes.
```

- [ ] **Step 4: Voice check** all three; **gather**; commit:

```bash
git add .agents/commands/daily-checkin.md .agents/commands/project-plan.md .agents/commands/project-manager.md dist/ .claude/ .github/ .opencode/
git commit -m "AWO-205: daily-checkin, project-plan, and project-manager gates delegate to the shared board plan rendering."
```

---

### Task 4: Eval suite `tests/process-transcript/` (AWO-205 witnesses; seeds AWO-80)

**Files:**
- Create: `tests/process-transcript/suite.md`, `README.md`
- Create: `tests/process-transcript/fixtures/plan-gate/{context/tooling/board.md,notes/standup.md,setup-progress.md}`
- Create: `tests/process-transcript/fixtures/stale-move/{context/tooling/board.md,notes/standup.md,setup-progress.md}`
- Create: `tests/process-transcript/{scripts,rubrics,checks,setup}/plan-gate.*` and `…/stale-move.*`

**Witness record (risk-driven):** Break: a flow renders a private gate format or forces a stale write; persona: adopting team's trust. Witness: `/process-transcript` end-to-end against a file-based sample board — the highest boundary that needs no live board. Gap: no flow-gate eval exists (AWO-80 is open). Lane: the repo's `/test-awow` fixture lane, real prompts, no mocks. Retire: nothing (first coverage). Deliberate hole, stated openly: the other three flows' delegation is witnessed only transitively through this suite; per-flow suites stay with AWO-80/AWO-163.

- [ ] **Step 1: Read the conventions** — `tests/README.md`, `tests/context-resolution/README.md`, and one existing checks file, to confirm helper names (`file-exists`) and the schema `tools/validate-evals.py` enforces. Where a helper below doesn't exist, use plain `grep -q` — checks are bash.
- [ ] **Step 2: Write the fixtures.** `fixtures/plan-gate/context/tooling/board.md`:

```markdown
# Board — sample (frozen test fixture)

- **Tool:** file-based sample board (frozen test fixture — the items ARE the list below; query no live surface; a write edits its row)
- **State machine:** Todo → In Progress → In Review → Done

## Items

| id | title | state | assignee |
|---|---|---|---|
| PB-1 | Wire retry budget into the export job | In Progress | dana |
| PB-2 | Spike: replace the CSV importer | Todo | dana |
```

`fixtures/plan-gate/notes/standup.md`:

```markdown
# Standup notes — team sample

Dana: export-job retry budget (PB-1) is code-complete, review opened this morning — moving it to review.
Dana: the CSV importer spike (PB-2) is dead — superseded by the retry work; kill it.
Dana: new next up: cap the export payload at 10 MB and reject anything above — needs a story, straight to Todo.
```

`fixtures/plan-gate/setup-progress.md`: copy the repo-root template with Steps 0–1 checked. `fixtures/stale-move/`: identical except `board.md` row `PB-1 | Wire retry budget into the export job | Done | dana` (the board outran the meeting).

- [ ] **Step 3: Setup hooks** — `setup/plan-gate.sh` and `setup/stale-move.sh`, both:

```bash
#!/usr/bin/env bash
# Board writes in this suite edit the fixture board file; a real repo boundary
# keeps the resolution walk honest.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
```

- [ ] **Step 4: Scripts.** `scripts/plan-gate.txt`:

```
# GATE 2 must render one board plan; details must show draft + because; writes only after go.
Process the standup notes at notes/standup.md against our board (context/tooling/board.md).
yes
details 3
go
```

`scripts/stale-move.txt`:

```
# The board outran the transcript: PB-1 is already Done. The move must report stale, the rest executes.
Process the standup notes at notes/standup.md against our board (context/tooling/board.md).
yes
go
```

- [ ] **Step 5: Rubrics.** `rubrics/plan-gate.md`:

```markdown
# Rubric — plan-gate

1. [plan-grammar] Was GATE 2 rendered as a single fenced diff block titled `BOARD PLAN`, one numbered line per action with `+` / `~` / `-` markers?
2. [plan-grammar] Did the block end with a counts footer (add · change · close)?
3. [plan-verbs] After `details 3`, did the run print the new story's full draft with a `because:` line naming the standup source, executing nothing?
4. [gate-discipline] Was `context/tooling/board.md` untouched until the user said `go`?
5. [apply-report] After `go`, did the run report per line in the DONE shape (Executed / Skipped / Failed / Manual follow-up)?
```

`rubrics/stale-move.md`:

```markdown
# Rubric — stale-move

1. [stale-guard] Did the run refuse the PB-1 move, reporting `stale` (or the board having changed) and naming the fresh state Done?
2. [apply-independence] Did the other approved lines still execute despite the stale one?
3. [no-force] Is there no point where the run overwrote PB-1's Done state?
```

- [ ] **Step 6: Checks.** `checks/plan-gate.sh`:

```bash
# Checks — plan-gate. Mechanical facts: fixture integrity before, execution
# evidence in the file-based board after. Conduct is the rubric's.

pre() {
  file-exists context/tooling/board.md
  file-exists notes/standup.md
}

post() {
  file-exists context/tooling/board.md
  grep -q "In Review" context/tooling/board.md
  grep -q "10 MB" context/tooling/board.md
}
```

`checks/stale-move.sh`:

```bash
# Checks — stale-move. PB-1's row must survive apply untouched.

pre() {
  file-exists context/tooling/board.md
  grep "PB-1" context/tooling/board.md | grep -q "Done"
}

post() {
  grep "PB-1" context/tooling/board.md | grep -q "Done"
}
```

- [ ] **Step 7: suite.md + README.md** — mirror `tests/context-resolution/suite.md`'s shape: frontmatter `command: process-transcript`, a paragraph stating the suite regresses the board plan (spec Pillar 4) against inert file-based boards, scenarios named, setup hooks noted. README lists layout and invariants in the established format.
- [ ] **Step 8: Validate (red for the right reason)** — `.venv/bin/python tools/validate-evals.py` passes. Run `/test-awow process-transcript stale-move` once **before relying on green**: on the pre-Task-1 prompts this scenario would have failed; on this branch expect `pass`. If either witness objects, fix the prompt (not the rubric) unless the rubric misreads the spec.
- [ ] **Step 9: Run both scenarios** — `/test-awow process-transcript` → both `pass`. Paste the run-file verdict paths into the commit body? No — keep ≤2 sentences; report verdicts in chat instead.
- [ ] **Step 10: Commit**

```bash
git add tests/process-transcript/
git commit -m "AWO-205: process-transcript eval suite — plan-gate grammar/details witness and stale-move apply-guard witness over a file-based sample board. Seeds the AWO-80 suite."
```

---

### Task 5: Profile + rungs in §Context resolution (AWO-206)

**Files:**
- Modify: `.agents/AGENTS.md` (§Context resolution, Stage 2 — exists on this branch only)

**Interfaces:**
- Produces: `{PROJECT}/.awow/profile.json` schema — keys `board_identity` (object, tool→handle), `hats` (array of `"product"`/`"engineering"`), `default_board` (index name), `confirmed` (YYYY-MM-DD). Rung numbering 1–6. Tasks 6–8 and the eval fixtures use these exactly.

- [ ] **Step 1: Insert two rungs** — in Stage 2's numbered ladder, after rung 3 (**Session pin**) and before the picker, insert:

```markdown
4. **Spoke board scope** — in a hub-connected spoke, the board named by `{PROJECT}/context/board-scope.md` frontmatter. Repo-bound work resolves here; fall through only when the invocation is explicitly about another board's business.
5. **Invoker default** — the `default_board` in `{PROJECT}/.awow/profile.json`. Skip a value naming a board absent from the index; re-confirm instead of guessing.
```

Renumber the picker to `6.` and extend it: after `the answer becomes the session pin`, add `; offer once to record it as the invoker default in profile.json`.

- [ ] **Step 2: Define the profile** — append after the Stage 2 paragraph that records ladder answers:

```markdown
**The invoker profile.** `{PROJECT}/.awow/profile.json` is machine-local, gitignored state naming who invokes here: `{"board_identity": {"<tool>": "<handle>"}, "hats": ["product"|"engineering"], "default_board": "<index name>", "confirmed": "YYYY-MM-DD"}`. `/setup-awow` orientation writes it; the rung-6 picker offers once to update it. Read it wherever "me" or a default board is needed; never commit it and never copy its contents into committed files.

**Spoke board scope.** A spoke's `{PROJECT}/context/board-scope.md` carries frontmatter `board:` (the hub index name), `team:` (the board team items land on), optional `project:` and `subpath:`. With a single-board hub the file is optional; absence means the hub's board.
```

- [ ] **Step 3: Voice check; gather; commit**

```bash
git add .agents/AGENTS.md dist/ .claude/ .github/ .opencode/
git commit -m "AWO-206: add the spoke board-scope and invoker-default rungs to the Stage-2 ladder and define profile.json and board-scope.md. Closes the spec's Pillar 3 ladder."
```

---

### Task 6: `board-scope.md` in setup; profile-first `/my-work`; cohabitation read-scope (AWO-206)

**Files:**
- Modify: `.agents/commands/setup-awow.md:47` (spoke track step 4)
- Modify: `.agents/commands/my-work.md:23,28-30`
- Modify: `.agents/commands/daily-digest.md` (one sentence, anchor found by reading the file)

- [ ] **Step 1: setup-awow spoke step 4** — replace the fragment `` `context/board-scope.md` (ask which board team or project this repo maps to); `` with:

```markdown
`context/board-scope.md` with frontmatter `board:` (the hub's index name for it), `team:` (the board team items land on), optional `project:` and `subpath:` — ask which of the hub's boards this repo maps to, and with a single-board hub offer to skip the file;
```

- [ ] **Step 2: my-work resolve-me** — replace the Inputs default line with: `- Optional: a person (name or board handle) to run it for. Default: the current user — read {PROJECT}/.awow/profile.json (board_identity) first, else {HUB}/context/tooling/board.md (board identity) or the git identity.` Replace §1's body with: `Determine whose work to pull. Read {PROJECT}/.awow/profile.json first; if the board identity is still ambiguous, ask once and offer to record it in the profile — do not guess across users.`
- [ ] **Step 3: my-work + daily-digest cohabitation scope** — in my-work §2 after the first query sentence, add: `When board.md declares a board-team filter for a shared board, scope the query to the filter.` In daily-digest, find the section that queries the board and add after its first query instruction: `Scope every board query to the board-team filter in {HUB}/context/tooling/board.md when one is declared; the digest covers this installation's slice only.`
- [ ] **Step 4: Voice check; gather; commit**

```bash
git add .agents/commands/setup-awow.md .agents/commands/my-work.md .agents/commands/daily-digest.md dist/ .claude/ .github/ .opencode/
git commit -m "AWO-206: board-scope.md gets its schema in the spoke track, my-work resolves me from the invoker profile first, and shared-board reads scope to the hub's filter."
```

---

### Task 7: Ladder eval scenarios (AWO-206 witnesses)

**Files:**
- Create: `tests/context-resolution/fixtures/profile-default/` (copy of `fixtures/index-form/`), `setup/profile-default.sh`, `scripts/profile-default.txt`, `rubrics/profile-default.md`, `checks/profile-default.sh`
- Create: the same five for `profile-vs-explicit` (fixture may be a second copy)

**Witness record:** Break: an ambiguous invocation ignores the profile (asks forever — the reported friction) or the profile silently overrides an explicit board (wrong-board write). Witness: `/my-work` over the index-form fixture, profile injected by the setup hook (`.awow/` is gitignored at any depth, so the hook writes it post-commit — exactly like real life). Gap: PR #44's scenarios stop at rung 2. Lane: existing suite. Retire: none.

- [ ] **Step 1: Fixtures** — copy `fixtures/index-form/` to `fixtures/profile-default/` and `fixtures/profile-vs-explicit/` unchanged.
- [ ] **Step 2: Setup hooks** — both extend the standard hook; after the fixture commit add:

```bash
mkdir -p .awow
cat > .awow/profile.json <<'EOF'
{"board_identity": {"sample": "sam"}, "hats": ["engineering"], "default_board": "product", "confirmed": "2026-08-18"}
EOF
```

- [ ] **Step 3: Scripts.** `scripts/profile-default.txt`:

```
# No scope evidence in the ask: rungs 1-4 all miss, rung 5 (invoker default) must
# resolve product silently — no picker, and "me" comes from the profile.
Run /my-work — what needs me?
```

`scripts/profile-vs-explicit.txt`:

```
# The user names the infra board outright: rung 1 must beat the profile's product default.
Run /my-work for the infra board — what needs me there?
```

- [ ] **Step 4: Rubrics.** `rubrics/profile-default.md`:

```markdown
# Rubric — profile-default

1. [ladder-rung-5] Did the run target the product board via the invoker profile, announcing `targeting board: product` before board reads?
2. [no-picker] Did the run never ask which board to use?
3. [identity] Did the run treat sam as "me" without asking who the user is?
```

`rubrics/profile-vs-explicit.md`:

```markdown
# Rubric — profile-vs-explicit

1. [ladder-rung-1] Did the run target the infra board (the explicit reference), not the profile's product default?
2. [no-repin] Did the run avoid rewriting the profile or presenting infra as a new durable default?
```

- [ ] **Step 5: Checks** — both scenarios:

```bash
pre() {
  file-exists context/tooling/board.md
  file-exists .awow/profile.json
}

post() {
  file-exists .awow/profile.json
}
```

- [ ] **Step 6: Update `tests/context-resolution/suite.md` + README** scenario lists; run `.venv/bin/python tools/validate-evals.py`; run `/test-awow context-resolution profile-default` and `…profile-vs-explicit` → `pass`; also re-run the four PR #44 scenarios (regression).
- [ ] **Step 7: Commit**

```bash
git add tests/context-resolution/
git commit -m "AWO-206: ladder witnesses for the invoker-default rung and explicit-beats-profile, profile injected by setup hook since .awow/ is gitignored."
```

---

### Task 8: Orientation, hats, soft park in `/setup-awow` (AWO-204)

**Files:**
- Modify: `.agents/commands/setup-awow.md` (§Track, Step 1b intro, Step 4)
- Modify: `setup-progress.md` (repo-root template)

**Interfaces:**
- Consumes: profile schema from Task 5.
- Produces: `setup-progress.md` keys `hat:`, `boards:`, `teams:`, `done-by:`, section `## Pending confirmations`; handoff path pattern `proposals/setup/handoff-<step>.md` (e.g. `handoff-step-2.md`); marker line `provisional: needs <hat> confirmation`. Task 9's status read and Task 10's checks grep these exactly.

- [ ] **Step 1: Replace `## Track — solo or team`** in full with:

```markdown
## Orientation — track, hat, and what this repo serves

On first entry (no `track:` in `setup-progress.md`), ask once, as one question: "Is this for a whole team, or just you — and which hat are you wearing: product, engineering, or both?" Record `track: team | solo` and `hat: product | engineering | both`; a bare "team" or "solo" answer defaults `hat: both`. Never re-ask either.

In **solo** mode, skip the steps that only make sense for a group and mark them as skipped when you lay out the plan:

- **Step 4 members** — skip; the roster is just the user. Still draft the style files, since they shape every artefact.
- **Step 7 neighbouring teams** — skip; there are no 1° teams to stub.

Reframe **Step 2** as the user's focus for the work, not a team charter. A solo adopter can switch later by re-running `/setup-awow` and answering "team".

With `track: team`, ask once what this repo serves: which board or boards, and which team or teams, by name. Record `boards: <comma list>` and `teams: <comma list>` in `setup-progress.md`. One board, one team — continue; this default path adds no further ceremony. More than one board — Step 1b drafts the index-form `board.md` (a `## Boards` list with sibling `board-<name>.md` specs, per §Context resolution in the agent instructions) and walks its configuration once per board. More than one team sharing members and conventions is one installation — say so, and recommend a separate installation only when the teams' conventions genuinely diverge.

Write `{PROJECT}/.awow/profile.json` (schema per §Context resolution) with the stated hat and, once boards are named, the invoker's default board. Never commit it.

### Hats — who answers which step

Steps carry a hat — **engineering**: 0 (installer), 1a (surface), 5 (bootstrap), 9 (skills review); **product**: 1b (board config), 2 (mission), 3 (conventions), 4 (members + style), 6 (KB seed), 7 (neighbouring teams), 8 (extras). `hat: both` answers everything with no ceremony.

Any hat may answer any step — never block on the wrong hat. When the invoker's hat does not match the step's, land the artefact with a first line `provisional: needs <hat> confirmation`, mirror it in `setup-progress.md` under `## Pending confirmations`, and offer a hand-off brief at `proposals/setup/handoff-<step>.md` (e.g. `handoff-step-2.md`): one paragraph naming the step, what was answered provisionally, and that running `/setup-awow` resumes exactly there.

Surface pending confirmations in the step map on every invocation. When the right hat confirms or amends, remove the provisional line and the pending entry, and record the confirmation. Record `done-by: <name or hat>` beside every completed step's checkbox.
```

- [ ] **Step 2: Step 1b multi-board hook** — in the Step 1b intro (after the sentence introducing Mode A/B), add: `With more than one board recorded at orientation, run this step once per board: the index-form board.md lists each board (name, scope, one-liner) and each board's full spec lands in a sibling board-<name>.md.`
- [ ] **Step 3: Step 4 curators** — after `Ask for the team member list (role, responsibilities, focus areas).` add: `With more than one board recorded at orientation, also capture per member which boards they work (a Boards: line) and name each board's product curator and technical curator — hand-off briefs and provisional confirmations address the curators.`
- [ ] **Step 4: setup-progress.md template** — in the repo-root template, add after the `## Status` list: `Each completed step carries `done-by: <name or hat>`.` and add a new section before `## Last session`:

```markdown
## Pending confirmations

_Provisional answers awaiting the right hat — one line each: step, artefact, needs which hat, hand-off brief path._
```

- [ ] **Step 5: Voice check; gather; commit**

```bash
git add .agents/commands/setup-awow.md setup-progress.md dist/ .claude/ .github/ .opencode/
git commit -m "AWO-204: orientation asks track+hat+served-boards in one question with defaults, steps carry hats with soft-park provisional markers and hand-off briefs, and completed steps record done-by."
```

---

### Task 9: `/awow-status` surfaces pending confirmations (AWO-204)

**Files:**
- Modify: `.agents/commands/awow-status.md:10-15`

- [ ] **Step 1:** add to the bullet list of things to tell the user:

```markdown
- Pending confirmations from `setup-progress.md` — each provisional answer awaiting a product or engineering hat, with its hand-off brief path under `proposals/setup/`.
```

- [ ] **Step 2: gather; commit**

```bash
git add .agents/commands/awow-status.md dist/ .claude/ .github/ .opencode/
git commit -m "AWO-204: awow-status lists provisional answers awaiting the right hat."
```

---

### Task 10: Setup eval scenarios (AWO-204 witnesses + golden-path regression)

**Files:**
- Create: `tests/setup-awow/fixtures/wrong-hat-soft-park/` (setup-progress.md with Steps 0–1 checked, `track: team`, `hat: engineering`, `boards: sample`, plus a minimal file-based `context/tooling/board.md` copied from Task 4's fixture)
- Create: `tests/setup-awow/{scripts,rubrics,checks}/wrong-hat-soft-park.*` (+ `setup/` hook if the suite uses them — mirror an existing scenario)

**Witness record:** Break: an engineer is blocked on (or silently authors) the team's mission; persona: engineer-led adoption. Witness: resume the wizard at Step 2 wearing `hat: engineering` — soft park must land the mission provisional with a hand-off. Gap: suite predates hats. Lane: existing suite. Retire: none. **Golden-path regression:** re-run the suite's existing baseline scenario unchanged — orientation's bare-answer defaults must keep old scripts green.

- [ ] **Step 1: Fixture** — `fixtures/wrong-hat-soft-park/setup-progress.md`: the template with Steps 0–1 checked (`done-by: engineering` on both), `track: team`, `hat: engineering`, `boards: sample`, `teams: sample`, empty `## Pending confirmations`. Copy `context/tooling/board.md` from Task 4's plan-gate fixture.
- [ ] **Step 2: Script** — `scripts/wrong-hat-soft-park.txt`:

```
# Engineering hat reaches the product-hat mission step: soft park, never a block.
Continue /setup-awow — let's do Step 2 now.
Our mission: help ops engineers cut deploy failures in half by making rollback a one-command action.
yes
```

- [ ] **Step 3: Rubric** — `rubrics/wrong-hat-soft-park.md`:

```markdown
# Rubric — wrong-hat-soft-park

1. [soft-park] Did the wizard accept the mission from the engineering hat without refusing or demanding a product owner first?
2. [provisional] Did the landed mission carry a `provisional: needs product confirmation` line?
3. [handoff] Was a hand-off brief drafted under proposals/setup/ naming Step 2 and how to resume?
4. [state] Did setup-progress.md's Pending confirmations gain the entry?
```

- [ ] **Step 4: Checks** — `checks/wrong-hat-soft-park.sh`:

```bash
pre() {
  file-exists setup-progress.md
  grep -q "hat: engineering" setup-progress.md
}

post() {
  grep -qi "provisional" context/team/mission.md
  ls proposals/setup/handoff-*.md >/dev/null 2>&1
  grep -qi "provisional\|needs product" setup-progress.md
}
```

- [ ] **Step 5: Second scenario — orientation-multi-board.** Break: a PO naming two boards gets a silently singular `board.md` and the topology is lost. Cheap witness: orientation recording only (the full per-board Step 1b walk is AWO-204 follow-through, stated openly as a hole). Fixture: the template `setup-progress.md` with only Step 0 checked, no `track:` recorded, plus nothing else. Script `scripts/orientation-multi-board.txt`:

```
# Two boards named at orientation: the wizard must record both and announce the index-form path.
Continue /setup-awow.
It's for a whole team — I'm the PO, product hat.
We serve two boards: product and infra — one team across both, shared conventions.
```

Rubric `rubrics/orientation-multi-board.md`:

```markdown
# Rubric — orientation-multi-board

1. [orientation-record] Did the wizard record track: team, hat: product, and both board names?
2. [index-form] Did the wizard state that Step 1b will draft the index-form board.md with sibling board-<name>.md specs, once per board?
3. [split-rule] Did the wizard keep one installation (shared conventions), not recommend a second repo or hub?
4. [one-question] Was orientation at most two questions, with no added ceremony beyond them?
```

Checks `checks/orientation-multi-board.sh`:

```bash
pre() {
  file-exists setup-progress.md
}

post() {
  grep -q "track: team" setup-progress.md
  grep -q "hat: product" setup-progress.md
  grep -q "boards: product, infra" setup-progress.md
}
```

- [ ] **Step 6: Register both scenarios** in the suite's README/suite.md per its conventions; `.venv/bin/python tools/validate-evals.py` passes.
- [ ] **Step 7: Run** — `/test-awow setup-awow wrong-hat-soft-park` and `…orientation-multi-board` → `pass`; then run the suite's existing baseline scenario (pick the first pre-existing one, e.g. `clean-clone`) → still `pass`. A baseline failure means orientation broke the golden path — fix the prompt's defaults, not the old script.
- [ ] **Step 8: Commit**

```bash
git add tests/setup-awow/
git commit -m "AWO-204: soft-park and multi-board-orientation witnesses plus a golden-path regression run of the existing baseline scenario."
```

---

### Task 11: Bookkeeping and handoff

**Files:**
- Modify: `proposals/invoker-topology-and-board-plan.md` (status line), `proposals/README.md` (index row)

- [ ] **Step 1:** flip the spec's status to `**Status:** Accepted — in build (AWO-204 / AWO-205 / AWO-206).`
- [ ] **Step 2:** check tracked precedent with `git ls-files proposals/ | head`; then `git add -f proposals/invoker-topology-and-board-plan.md proposals/plans/2026-08-18-invoker-topology-and-board-plan.md` and add an index row to `proposals/README.md`: `| [invoker-topology-and-board-plan](invoker-topology-and-board-plan.md) | **Accepted** (in build) | Hat-aware setup, invoker profile + ladder rungs, board plan gate. AWO-204/205/206, stacked on PR #44. |`
- [ ] **Step 3: Commit**

```bash
git add proposals/README.md
git commit -m "AWO-204: track the accepted invoker-topology-and-board-plan proposal and its executed plan as maintainer records."
```

- [ ] **Step 4: Verify the branch** — full `/test-awow` for the three touched suites green; `tools/validate-evals.py` green; `git log --oneline origin/proposal/context-resolution..HEAD` shows the task commits.
- [ ] **Step 5: Board + stop for approval** — comment each of AWO-204/205/206 with a one-line "implemented on `casper/invoker-topology-and-board-plan` (stacked on PR #44)" and move to In Review. **Stop.** Pushing and opening the PR are publication on this public repo: ask the user explicitly, and note the PR must target `proposal/context-resolution` (or wait for PR #44 to merge and rebase onto `main`).
