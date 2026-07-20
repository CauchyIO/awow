# PR 2 — Surface Trim and Board Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut the shipped command surface from twenty to sixteen, and stop three commands hard-stopping on a file that exists nowhere on `main`. After this PR a plugin-installed `/daily-digest` in a repo with no `context/` asks one question and produces a digest, instead of halting.

**Architecture:** Four commands leave `dist/commands/` — two by moving to `channel: vendored`, two by merging into `/daily-digest`. `/daily-digest` absorbs the weekly window as a parameter and loses its email delivery path entirely, becoming markdown-with-front-matter plus a review gate plus a PR. Then the §4.2 board fallback replaces the absent-`board.md` hard stop in eleven surviving commands, preserving the auth-failure half of each guard.

**Tech Stack:** Python 3.12 stdlib only (no pytest, no third-party). Bash for the harness and eval suites. `tools/gather.py` is the build; `tools/lint-paths.py` is the token linter; `tools/validate-evals.py` statically validates the eval suites; `.github/workflows/ci.yml` runs `gather.py --check`, `lint-paths.py`, and `tests/harness/run-harness-tests.sh all`.

**Spec:** `docs/superpowers/specs/2026-07-20-plugin-first-readme-design.md` §4.2 and §4.4. This plan covers PR 2 of five.

**Assumed landed: PR 1.** Every task below treats these as existing facts:

- `{AWOW_ROOT}` exists and is substituted in both `PLUGIN_TOKEN_SUBSTITUTIONS` and `AGENT_SKILLS_TOKEN_SUBSTITUTIONS` in `tools/gather.py`.
- `PAYLOAD_CONTEXT_PATHS`, `TEAM_DATA_CONTEXT_PATHS`, `classify_context_path(rel) -> str`, and `unclassified_context_paths() -> list[str]` exist in `tools/gather.py`.
- `dist/context/` ships the classified machinery; `dist/.github/` ships a generated Copilot payload.
- `.agents/skills/using-awow/SKILL.md` already carries all three amendments — four-token resolution, the ask-once board rule, and the inert `/update-context` reflex. **No task in this plan may edit that file.** The spec consolidates every `using-awow` edit into PR 1.
- `tests/gather-tokens/` and `tests/payload-classification/` exist and run in CI.

**Line numbers below are pre-PR-1 numbering** and are given so you can find the right region fast. PR 1 Task 6 rewrote the `{HUB}/context/tooling/activity-collection.md` and `.../mining.md` references in several of these files to carry an `{AWOW_ROOT}` fallback, which shifts line numbers in `daily-digest.md`, `kb-mine.md`, and others by one or two lines. **Every edit in this plan anchors on literal quoted text, not on a line number.** If a quoted anchor does not match, stop and report — do not guess at the intent.

## Global Constraints

- **Python 3.12, stdlib only.** No pytest, no network, no third-party. Tests are plain scripts run as `python3 tests/<dir>/test_<name>.py`, following `tests/awow-lock/test_awow_lock.py`. Every test module opens with a docstring ending in a `Run:` line.
- **Three channels exist, not two:** `vendored` (excluded from the payload), `bootstrap` (`setup-awow.md` and, until Task 2, `update-awow.md` — these **do** ship, because they create the vendored tree and their literal paths are the deliverable, per `lint-paths.py:36-38`), and the default. Never assume a binary. `lint-paths.py:38` skips `vendored` and `bootstrap` alike, so Task 2's `bootstrap` → `vendored` move is lint-neutral.
- **Never hand-edit generated files.** `.claude/`, the `.github/` pointer stubs, `dist/`, root `AGENTS.md`, `.claude/CLAUDE.md`, and `.github/copilot-instructions.md` are `gather.py` output. Edit the source under `.agents/` and re-run the gather.
- **After any `.agents/` edit, run `python tools/gather.py`** and commit the regenerated surfaces alongside the source change, or `--check` fails in CI.
- **`tools/lint-paths.py` needs no change.** Its `BARE` regex at `:11` is `(?<![{/\w.\-])(context|tools|proposals)/`. `digests/`, `.awow/`, and `{AWOW_ROOT}/context/` all pass it. If a task makes lint fail, the task is wrong, not the linter.
- **Commit message style:** max 2 sentences.
- **Do not create PRs and do not push.** This plan produces commits on `feat/plugin-first-readme` only.

---

### Task 1: Delete `/test-setup-awow`

**Files:**
- Delete: `.agents/commands/test-setup-awow.md` (19 lines, `channel: vendored`, self-declared deprecated alias)
- Delete (via gather orphan removal): `.claude/commands/test-setup-awow.md`, `.github/prompts/test-setup-awow.prompt.md`
- Modify: `meta/proposals/eval-baseline-and-prompt-cleanup.md:40`, `meta/proposals/pi-codex-harness-support.md:72`, `meta/proposals/README.md:24`, `tests/setup-awow/README.md:15`
- Modify: `setup/awowify.sh:74`, `tools/awow_lock.py:79`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed by later tasks. `dist/commands/` is unchanged — the file is already `channel: vendored` and never shipped, so this is a repo cleanup, not a surface cut.

**Why the exclude entries go too:** `awow_lock.py:41-42` states the sync constraint — `STARTER_PATHS` / `ALWAYS_EXCLUDE` / `SOLO_EXCLUDE` mirror `awowify.sh` and must stay in sync. Both name `.agents/commands/test-setup-awow.md`, which will no longer exist. Removing it from both keeps them in sync and drops dead config. It is safe for a vendored adopter who still has the file: `awow_lock` will now manage it, upstream no longer has it, and the verdict is `removed-upstream` — "upstream removed (left in place)", no file operation (`awow_lock.py:269`, `:426`).

- [ ] **Step 1: Delete the command and its stubs**

```bash
git rm .agents/commands/test-setup-awow.md
python tools/gather.py
git status --porcelain .claude/ .github/
```

Expected: `git status` shows `.claude/commands/test-setup-awow.md` and `.github/prompts/test-setup-awow.prompt.md` deleted. `gather.py` removes them as orphans because both carry `GENERATED_MARKER` and no longer have a planned target (`find_orphans:707`).

- [ ] **Step 2: Update the live `meta/proposals/` references**

Three references are live claims about the present. The rest — `meta/proposals/setup-awow-regression-tests.md`, `meta/proposals/meta-workspace-and-fixture-decoupling.md`, `meta/plans/2026-07-12-wi2-neutral-token-sweep.md`, `meta/proposals/eval-baseline-and-prompt-cleanup.md:26`, `:28`, `:123` — are historical records of what was built and when. Leave those alone; rewriting history to match the present destroys the record.

In `meta/proposals/eval-baseline-and-prompt-cleanup.md`, replace line 40:

```markdown
5. **Generalise the runner.** `/test-setup-awow` → `/test-awow [suite] [scenario]` reading `tests/<suite>/`; the six-phase protocol is already suite-agnostic except for hardcoded paths. Keep `/test-setup-awow` as an alias until the rename settles.
```

with:

```markdown
5. **Generalise the runner.** *(Done.)* `/test-setup-awow` → `/test-awow [suite] [scenario]` reading `tests/<suite>/`; the six-phase protocol was already suite-agnostic except for hardcoded paths. The `/test-setup-awow` alias was kept until the rename settled, then deleted (2026-07-20).
```

In `meta/proposals/pi-codex-harness-support.md`, replace line 72:

```markdown
- **WI-7** — regression tests (extend `tests/setup-awow/` + `/test-setup-awow`) for both surfaces and both manifests.
```

with:

```markdown
- **WI-7** — regression tests (extend `tests/setup-awow/`, run via `/test-awow setup-awow`) for both surfaces and both manifests.
```

In `meta/proposals/README.md`, replace line 24:

```markdown
| [setup-awow-regression-tests](setup-awow-regression-tests.md) | **Landed** | `tests/setup-awow/` suite + `/test-setup-awow`. |
```

with:

```markdown
| [setup-awow-regression-tests](setup-awow-regression-tests.md) | **Landed** | `tests/setup-awow/` suite, run via `/test-awow setup-awow`. |
```

- [ ] **Step 3: Fix the one live reference outside `meta/proposals/`**

The spec says "the two `meta/proposals/` references" and misses this. `tests/setup-awow/README.md:15` currently reads:

```markdown
(`/test-setup-awow` remains as a deprecated alias.)
```

That sentence becomes false the moment Step 1 lands. Delete the line.

- [ ] **Step 4: Drop the dead exclude entries from both manifests**

In `setup/awowify.sh`, remove line 74 from the `EXCLUDES` array so it reads:

```bash
# Always excluded — awow-maintainer tooling adopters never run.
EXCLUDES=(
  setup/awowify.sh
  tools/distribute.py
  tools/reset-adopter-state.py
  tools/sync-dist.sh
  .agents/commands/awow-reset.md
)
```

In `tools/awow_lock.py`, remove line 79 from `ALWAYS_EXCLUDE` so it reads:

```python
ALWAYS_EXCLUDE = {
    "setup/awowify.sh",
    "setup/awowify.ps1",
    "tools/distribute.py",
    "tools/reset-adopter-state.py",
    "tools/sync-dist.sh",
    ".agents/commands/awow-reset.md",
    LOCK_REL,
    STAMP_REL,
}
```

- [ ] **Step 5: Verify nothing live still names the command**

```bash
grep -rn 'test-setup-awow' --include='*.md' --include='*.sh' --include='*.py' \
  .agents/ tests/ tools/ setup/ dist/ .claude/ .github/ meta/proposals/README.md \
  meta/proposals/pi-codex-harness-support.md; echo "exit=$?"
```

Expected: no output and `exit=1` (grep found nothing). The remaining hits under `meta/proposals/setup-awow-regression-tests.md`, `meta/proposals/meta-workspace-and-fixture-decoupling.md`, `meta/plans/`, and `eval-baseline-and-prompt-cleanup.md:26,28,123` are the historical records Step 2 deliberately left.

- [ ] **Step 6: Verify the build, lint, and both suites**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tools/validate-evals.py \
  && bash tests/harness/run-harness-tests.sh all
```

Expected: `--check` prints nothing and exits 0; `Path tokens clean.`; `OK: 2 suite(s), 12 scenario(s), 0 finding(s)`; the harness suite passes.

- [ ] **Step 7: Commit**

```bash
git add .agents/commands .claude/ .github/ meta/proposals/ tests/setup-awow/README.md setup/awowify.sh tools/awow_lock.py
git commit -m "Delete the deprecated /test-setup-awow alias now the /test-awow rename has settled. Update the live references and drop the dead exclude entry from both starter manifests."
```

---

### Task 2: `update-awow` moves to `channel: vendored`

**Files:**
- Modify: `.agents/commands/update-awow.md:5` (`channel: bootstrap` → `channel: vendored`), plus one added paragraph on merged commands

**Interfaces:**
- Consumes: nothing.
- Produces: `dist/commands/update-awow.md`, `dist/agent-skills/update-awow/`, and `dist/.github/prompts/update-awow.prompt.md` (generated by PR 1 Task 7) all disappear. `is_vendored_channel` at `gather.py:424` is the single filter that does this; PR 1's `plan_copilot_payload` calls it too, so all three surfaces drop together.

**Why:** §4.4. In plugin-land this command actively corrupts. `backfill` writes a near-empty lockfile, `_compute_plan` walks `dist/`, classifies plugin internals as `new`, and `apply` dumps them into the user's repo under the banner "updating awow". It is also redundant there — its own L36-38 tells plugin users to run `/plugin update awow`, which *is* their entire update. It stays in the repo as the vendored adopter's update path.

- [ ] **Step 1: Confirm it ships today**

```bash
ls dist/commands/update-awow.md dist/agent-skills/update-awow/SKILL.md dist/.github/prompts/update-awow.prompt.md
```

Expected: all three listed. This is the state Step 2 removes.

- [ ] **Step 2: Change the channel**

In `.agents/commands/update-awow.md`, replace the frontmatter (lines 1-6):

```markdown
---
phase: meta
prerequisites: ["Step 0 of /setup-awow complete"]
removes_pain: "the how-do-I-pull-in-newer-awow-versions-without-clobbering-my-config problem"
channel: bootstrap
---
```

with:

```markdown
---
phase: meta
prerequisites: ["Step 0 of /setup-awow complete"]
removes_pain: "the how-do-I-pull-in-newer-awow-versions-without-clobbering-my-config problem"
channel: vendored
---
```

- [ ] **Step 3: State what the update means for a vendored adopter mid-upgrade**

§4.4 requires this. A vendored adopter's lockfile still lists `daily-routine.md`, `weekly-digest.md`, and `cross-team-view.md`. Upstream no longer has them, so `_verdict` returns `removed-upstream` (`awow_lock.py:269`) and `apply` performs no file operation (`:426`) — the adopter keeps working copies of commands that no longer exist upstream, silently, forever. The command must say so.

In `.agents/commands/update-awow.md`, in the `## Steps` section, replace step 5 (currently beginning "5. **Report.** Summarise: version moved from → to"):

```markdown
5. **Report.** Summarise: version moved from → to, N updated, M added, and list
   every `<file>.awow` the user still needs to merge (then delete the `.awow`).
   If any conflicts landed, remind them the update is not "done" until each
   `.awow` is merged. Recommend reviewing the whole update as one `git diff` on
   a branch — git is the backstop for anything step 2's caution missed.
```

with:

```markdown
5. **Report.** Summarise: version moved from → to, N updated, M added, and list
   every `<file>.awow` the user still needs to merge (then delete the `.awow`).
   If any conflicts landed, remind them the update is not "done" until each
   `.awow` is merged. Recommend reviewing the whole update as one `git diff` on
   a branch — git is the backstop for anything step 2's caution missed.

   **Call out `removed-upstream` explicitly.** Files upstream has dropped are
   left in place by design — `apply` never deletes. As of 0.6.0 that covers
   `.agents/commands/daily-routine.md`, `weekly-digest.md`, and
   `cross-team-view.md`: `/daily-routine` and `/weekly-digest` merged into
   `/daily-digest` (the weekly view is now `/daily-digest --week`), and
   `/cross-team-view` was never built. Name each one, say it is now unmaintained,
   and offer to delete it and re-run `python tools/gather.py`. Silence here
   leaves a team invoking a command upstream no longer supports.
```

- [ ] **Step 4: Verify it left all three payload surfaces**

```bash
python tools/gather.py
for p in dist/commands/update-awow.md dist/agent-skills/update-awow dist/.github/prompts/update-awow.prompt.md; do
  test -e "$p" && echo "LEAK: $p" || echo "gone: $p"
done
ls dist/commands/ | wc -l
```

Expected: three `gone:` lines, then `19` (twenty commands minus `update-awow`; `awowify.md` is in that count and `test-setup-awow` never was).

- [ ] **Step 5: Verify build and lint**

```bash
python tools/gather.py --check && python tools/lint-paths.py
```

Expected: both pass. `lint-paths.py:38` skips `vendored` and `bootstrap` identically, so this file's literal `tools/awow_lock.py` and `python tools/gather.py` references stay legal.

- [ ] **Step 6: Commit**

```bash
git add .agents/commands/update-awow.md .claude/ .github/ dist/
git commit -m "Mark /update-awow channel: vendored — in a plugin install it dumps payload internals into the user's repo, and plugin users update with /plugin update awow instead. Make it name the commands upstream has dropped rather than leaving them silently in place."
```

---

### Task 3: `project-manager` moves to `channel: vendored`

**Files:**
- Modify: `.agents/commands/project-manager.md:1-9` (add `channel: vendored`)

**Interfaces:**
- Consumes: nothing.
- Produces: `dist/commands/project-manager.md`, `dist/agent-skills/project-manager/`, and `dist/.github/prompts/project-manager.prompt.md` disappear. `dist/commands/` drops to 18.

**Why:** §4.4. `project-manager.md:13` is a self-declared park notice — *"No active adopter runs this loop — the maintainer has never invoked it, and the one nominal adopter uses cloud routines for coordination instead."* The file stays, with its re-entry condition written into it; it just stops occupying a slot in the shipped picker.

**Its `/weekly-digest` reference at `:21` is deliberately left for Task 6,** which is the task that deletes `/weekly-digest`. Fixing it here would edit a line whose correct replacement is not yet decided.

- [ ] **Step 1: Add the channel to the frontmatter**

In `.agents/commands/project-manager.md`, replace the frontmatter (lines 1-9):

```markdown
---
phase: standardise
argument-hint: "[scope: a project / team / initiative] [--report to produce the weekly MT roll-up] (optional — omit to run the loop over all active work)"
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "A project plan with a stated dependency graph exists — produced by /project-plan from a /solution-design-flow design and published to the board"
  - "More than one person or team coordinating on shared work"
removes_pain: "the who's-waiting-on-whom-and-what-only-I-can-unblock problem"
---
```

with:

```markdown
---
phase: standardise
argument-hint: "[scope: a project / team / initiative] [--report to produce the weekly MT roll-up] (optional — omit to run the loop over all active work)"
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "A project plan with a stated dependency graph exists — produced by /project-plan from a /solution-design-flow design and published to the board"
  - "More than one person or team coordinating on shared work"
removes_pain: "the who's-waiting-on-whom-and-what-only-I-can-unblock problem"
channel: vendored
---
```

- [ ] **Step 2: Verify it left all three payload surfaces**

```bash
python tools/gather.py
for p in dist/commands/project-manager.md dist/agent-skills/project-manager dist/.github/prompts/project-manager.prompt.md; do
  test -e "$p" && echo "LEAK: $p" || echo "gone: $p"
done
ls dist/commands/ | wc -l
```

Expected: three `gone:` lines, then `18`.

- [ ] **Step 3: Verify build and lint**

```bash
python tools/gather.py --check && python tools/lint-paths.py
```

Expected: both pass.

- [ ] **Step 4: Commit**

```bash
git add .agents/commands/project-manager.md .claude/ .github/ dist/
git commit -m "Mark /project-manager channel: vendored — the file's own park notice says no adopter runs it, so it stops occupying a slot in the shipped picker. The re-entry condition stays written into the file."
```

---

### Task 4: Merge `/daily-routine` into `/daily-digest`

**Files:**
- Modify: `.agents/commands/daily-digest.md` (append one closing section)
- Delete: `.agents/commands/daily-routine.md` (120 lines)
- Modify: `.agents/commands/kb-mine.md:13`, `:56-57`; `.agents/commands/kb-synthesize.md:4`, `:51`; `.agents/commands/setup-awow.md:209`; `context/knowledge-base/mining.md:8`

**Interfaces:**
- Consumes: nothing.
- Produces: `dist/commands/` drops to 17. `context/knowledge-base/mining.md` is classified `payload` by PR 1's manifest and ships to `dist/context/knowledge-base/mining.md`, so its `/daily-routine` mention would otherwise reach every plugin install as a pointer to a command that does not exist.

**Why:** §4.4. Its sole justification is the gather-once optimisation, but both children already reuse the snapshot independently (`daily-digest.md:56`, `kb-mine.md:56-57`), and its own `:37` calls the phases *"independent projections… not a chain."*

**Where the closing offer goes, and why it goes there.** It is appended as a section at the **end of the file**, after `## Behavioral boundaries` — not folded into Phase 3's Delivery step. Task 6 rewrites everything between Phase 3's Delivery and `## Behavioral boundaries`; a fold-in there would have to be restated. At the tail it survives Task 6 untouched, and it is true whether or not the PR opened.

- [ ] **Step 1: Append the closing offer to `daily-digest.md`**

At the very end of `.agents/commands/daily-digest.md`, after the final `- **Never hardcode recipients.**` line, append:

```markdown

---

## Handing off

The day's snapshot (`activity/YYYY-MM-DD.json`) is the expensive part and it is now on disk. The deep projection over the same snapshot — the durable-knowledge candidates — is a separate lens with its own gate, so offer it rather than running it:

> Run `/kb-mine` against the same snapshot? It reads each item's deep `payload` for knowledge worth keeping, and stages candidates for the `/kb-synthesize` gate. Nothing lands in the knowledge base without your approval.

Offer once. If the user declines, or if this run produced no snapshot, say nothing further.
```

- [ ] **Step 2: Delete the command**

```bash
git rm .agents/commands/daily-routine.md
```

- [ ] **Step 3: Repoint the five source references**

In `.agents/commands/kb-mine.md`, replace the sentence at `:13-15`:

```markdown
the standalone counterpart to `/daily-routine` Phase 3 — same projection, without the
overview. Reach for it when you want candidates for a day you did not digest, or to
backfill a past day.
```

with:

```markdown
the deep counterpart to `/daily-digest`'s shallow projection — same snapshot, different
lens. Reach for it when you want candidates for a day you did not digest, or to
backfill a past day.
```

In the same file, replace the clause at `:56-57`:

```markdown
produce `activity/YYYY-MM-DD.json`, or **reuse it** if a peer run (`/daily-digest` or
`/daily-routine`) already produced it for the day. That step owns the board / code /
```

with:

```markdown
produce `activity/YYYY-MM-DD.json`, or **reuse it** if a peer run (`/daily-digest`)
already produced it for the day. That step owns the board / code /
```

In `.agents/commands/kb-synthesize.md`, replace the prerequisite at `:4`:

```markdown
  - "{HUB}/context/kb-inbox/ holds one or more candidate files (produced by /kb-mine or /daily-routine)"
```

with:

```markdown
  - "{HUB}/context/kb-inbox/ holds one or more candidate files (produced by /kb-mine)"
```

In the same file, replace at `:51`:

```markdown
user at `/kb-mine` or `/daily-routine` to produce some.
```

with:

```markdown
user at `/kb-mine` to produce some.
```

In `.agents/commands/setup-awow.md`, replace at `:209`:

```markdown
- **Capture.** Mining a day's activity (`/kb-mine`, or `/daily-routine` Phase 3) stages candidates as committed files in `context/kb-inbox/` — one durable insight per file. Point the user at `context/kb-inbox/README.md`.
```

with:

```markdown
- **Capture.** Mining a day's activity (`/kb-mine`) stages candidates as committed files in `context/kb-inbox/` — one durable insight per file. Point the user at `context/kb-inbox/README.md`.
```

- [ ] **Step 4: Repoint the shipped contract**

`context/knowledge-base/mining.md` ships in the payload. In it, replace `:8-10`:

```markdown
This is a **projection contract, not a command.** Both the combined `/daily-routine`
and the standalone `/kb-mine` follow it. It assumes the day snapshot already
exists (produced by the shared collection step, `context/tooling/activity-collection.md`)
```

with:

```markdown
This is a **projection contract, not a command.** `/kb-mine` follows it. It assumes
the day snapshot already exists (produced by the shared collection step,
`context/tooling/activity-collection.md`)
```

- [ ] **Step 5: Verify no live source still names the command**

```bash
python tools/gather.py
grep -rn 'daily-routine' .agents/ context/ dist/ tests/ .claude/ .github/ ; echo "exit=$?"
```

Expected: no output and `exit=1`. Hits remaining elsewhere in the repo are `.gitignore` (a comment on the `activity/` rule — leave it, the directory is still produced), `meta/proposals/*` (historical records), and `docs/superpowers/` (this plan and the spec).

- [ ] **Step 6: Verify build, lint, payload, and count**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/payload-classification/test_classification.py
ls dist/commands/ | wc -l
test -e dist/context/knowledge-base/mining.md && grep -c 'daily-routine' dist/context/knowledge-base/mining.md
```

Expected: `--check` and lint pass; `Payload classification OK.`; `17`; then `0` from the final grep (grep exits 1 with a `0` count — that is the pass condition).

- [ ] **Step 7: Commit**

```bash
git add .agents/commands .claude/ .github/ context/knowledge-base/mining.md dist/
git commit -m "Merge /daily-routine into /daily-digest: both lenses already reuse the day snapshot independently, so the gather-once wrapper bought nothing. /daily-digest now closes by offering /kb-mine against the same snapshot."
```

---

### Task 5: Merge the weekly window into `/daily-digest`, and delete `/weekly-digest`

**Files:**
- Modify: `.agents/commands/daily-digest.md` — frontmatter, H1, the read-only header, Phase 0, Phase 1, Phase 2, Phase 3
- Delete: `.agents/commands/weekly-digest.md` (199 lines)
- Modify: `.agents/commands/project-manager.md:21`, `.agents/commands/awow-add.md:14`, `.agents/commands/README.md:11`

**Interfaces:**
- Consumes: Task 4's `daily-digest.md` (the `## Handing off` tail must still be the last section afterwards).
- Produces: `/daily-digest` accepts a window argument. `dist/commands/` drops to 16 — the §4.4 target. Task 6 consumes the Phase 0-3 structure this task leaves and renumbers Phases 4-6 exactly once.

**Why no alias:** §12. `/weekly-digest` is removed outright. The weekly window survives as a `/daily-digest` parameter; the name does not. An alias would keep a picker entry and a trigger description alive for a command that no longer has a body.

**Why this is bigger than a template fold-in.** `weekly-digest.md` carries nine output subsections (`:81-181`), ISO-week/Mon–Fri resolution (`:32-40`), an extra primary source — every `digests/YYYY-MM-DD.md` in the window, with a coverage-gap rule (`:46-48`) — a last-week comparison (`:50-52`), a different metric set (`:58`), and a different output path (`:76`, `:190-192`). Reading its own prior outputs is a Phase-0 control-flow branch, not a fold-in.

**Do not renumber phases in this task.** After it, `daily-digest.md` still has Phases 0-6 with 4 = HTML render, 5 = review gate, 6 = email. Task 6 does the single renumbering.

- [ ] **Step 1: Widen the frontmatter and the header**

In `.agents/commands/daily-digest.md`, replace lines 1-16:

```markdown
---
phase: standardise
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "Most of the team actively committing"
  - "Team has shipped at least three Seed cycles"
removes_pain: "the I-have-no-idea-what-the-other-team-shipped-this-week problem"
---

# /daily-digest — aggregate daily activity into a team-wide synthesis

You aggregate all board, code, and (optionally) chat activity from today and produce a synthesis layer that helps the team stay aligned.

**Read-only.** This command never mutates the board, the codebase, or any external system. Output is a markdown file under `digests/YYYY-MM-DD.md`. Optional email rendering and delivery require explicit user approval.

You are not evaluating performance. You are producing a synthesis layer.
```

with:

```markdown
---
phase: standardise
argument-hint: "[--week | YYYY-Www | YYYY-MM-DD] (optional — omit for today)"
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "Most of the team actively committing"
  - "Team has shipped at least three Seed cycles"
removes_pain: "the I-have-no-idea-what-the-other-team-shipped-this-week problem"
---

# /daily-digest — aggregate a day or a week of activity into a team-wide synthesis

You aggregate all board, code, and (optionally) chat activity over a window — one day by default, or a Monday–Friday week — and produce a synthesis layer that helps the team stay aligned.

**Read-only against every source.** This command never mutates the board, the codebase, or any external system. It writes one markdown file and opens a pull request for it; nothing else.

The weekly window is not a summary of the dailies. It answers different questions at a different altitude, and it reads the dailies as input. Where a step below differs by window, both variants are stated.

You are not evaluating performance. You are producing a synthesis layer.
```

- [ ] **Step 2: Replace Phase 0 with window resolution**

Replace the whole of Phase 0 — lines 33-47, from `## Phase 0 — Input & mode detection` through the `- **Reuse** — use the existing markdown as-is` bullet — with:

```markdown
## Phase 0 — Window & reuse check

### Resolve the window

Parse the argument. It selects one of two windows, and every step below runs over the window you resolve here:

- **No argument** → the **day** window, today.
- `YYYY-MM-DD` → the **day** window, that date.
- `--week` → the **week** window, the current ISO week.
- `YYYY-Www` (e.g. `2026-W12`) → the **week** window, that ISO week.

For a week window, resolve the ISO week to its Monday–Friday date range. If the team's working week differs, read `{HUB}/context/team/members.md` or `{HUB}/context/team/conventions/REQUIRED/labels.md` for the convention before assuming Mon–Fri.

State the resolved window back to the user in one line before doing any work — `Day: 2026-07-20` or `Week 2026-W29: Mon 13 Jul – Fri 17 Jul` — so a misparsed argument is caught before collection, not after.

### Reuse check

The output path depends on the window: `digests/YYYY-MM-DD.md` for a day, `digests/weekly/YYYY-Www.md` for a week.

If a digest already exists at that path, ask the user whether to:

- **Regenerate** — run the full digest again and overwrite
- **Reuse** — use the existing markdown as-is
```

- [ ] **Step 3: Add the two weekly-only sources to Phase 1**

In Phase 1, immediately after the `### Run the shared collection step` block (which ends with the hard-stop sentence beginning `If the snapshot cannot be produced`) and before `### Project the digest's shallow view`, insert:

```markdown
### Week window — collect across the range

Run the collection step once per day in the range and merge the results, reusing any `activity/YYYY-MM-DD.json` already on disk. Do not re-query a day whose snapshot exists.

### Week window — two extra primary sources

**The week's daily digests.** Read every `digests/YYYY-MM-DD.md` in the range, in full. These are the richest input you have: they already carry synthesised narratives, project snapshots, cross-team connections, and structural observations. **A missing daily digest is a data-coverage gap — name it in the output; never silently skip the day.**

**Last week, for comparison.** If `digests/weekly/YYYY-W(ww-1).md` exists, read it to detect **dropped** connections — active last week, absent this week — and to compare project trajectories. If it does not exist, say so once and omit the dropped-connections subsection rather than leaving it empty.
```

- [ ] **Step 4: Add the weekly questions to Phase 2**

In Phase 2, immediately after the `### Do not just list changes` block (which ends with the `- **What should someone know that they don't?** (cross-relevance)` bullet) and before `### Cross-relevance detection`, insert:

```markdown
### Week window — different questions, different shapes

The day window asks "what happened today?". The week window asks:

- What actually **moved** this week (outcomes, not activity)?
- What **shifted** between Monday and Friday (trajectory)?
- Where did the team **spend its time** (workload distribution)?
- What **patterns** are emerging (recurring gaps, growing collaborations)?
- What should change next week (signals, not recommendations)?

Three shapes change with it:

- **Counts** become weekly: issues created, issues completed, issues stale (in progress all week with no state change), active projects, PRs merged, cross-links surfaced.
- **Connections** become **collaborations**, classified: **active** (appeared 3+ days), **emerging** (first appeared this week), **dropped** (active last week, absent this week).
- **Project status** becomes **trajectory**: where each project stood Monday versus Friday, and the direction of travel.
```

- [ ] **Step 5: Add the weekly output template to Phase 3**

In Phase 3, immediately after the closing ``` of the day template (the fenced block ending with the `* Channel mapping drift (failed channels from Phase 1.C, with reasons).` line) and before `### Issue references`, insert:

```markdown
### Week window — output format

Write to `digests/weekly/YYYY-Www.md` instead:

```markdown
# Weekly digest — YYYY-Www (Mon DD MMM – Fri DD MMM)

## Week-at-a-glance

| Metric | Value |
|---|---|
| Issues created | X |
| Issues completed | X |
| Issues stale | X (in progress all week, no updates) |
| Active projects | X |
| Code PRs merged | X |
| Cross-links surfaced | X |

---

## Weekly narrative

8–15 sentences synthesizing what happened across the team(s) this week. Coherent narrative answering: What were the 2–3 dominant threads? What shifted between Monday and Friday? What was unexpected?

---

## Project trajectory report

For each active project:

### <Project name>

| | |
|---|---|
| **Start of week** | Status / trajectory on Monday |
| **End of week** | Status / trajectory on Friday |
| **Direction** | Accelerating / On track / Slowing / Stalled / Pivoted / New / Closed |
| **Key events** | 2–3 bullets |
| **Next-week signal** | What to watch for |

Projects with **no updates all week** get a separate "Silent projects" subsection.

---

## Team activity heatmap

A matrix showing who worked on which projects this week, derived from board activity, code activity, and (where present) `/process-transcript` attribution signals. Use block characters to indicate relative effort:

```
              ProjectA  ProjectB  ProjectC  Content  Platform  Internal
Person A      ███       ██        █                            ██
Person B      ██                  ███                ██
Person C      █                             ███      ██
Person D                █████                        █
Person E                ██                           ███
```

Use 1–5 blocks to represent relative time allocation (not precise hours). Derive from board issue assignments and commits; if `/process-transcript` outputs are present for the week, fold in their attribution signals. Leave blank if no signals.

---

## Cross-team connections

### Active collaborations (appeared 3+ days)

* **<Person A>** ↔ **<Person B>** (<project>): Description of ongoing collaboration.

### Emerging connections (new this week)

* **<Person A>** → **<Person C>** (<project>): Description of new connection.

### Dropped connections (active last week, absent this week)

* **<Person A>** ↔ **<Person B>** (<project>): Was active last week, no signals this week.

---

## Code activity

Weekly summary per repo:

* `<repo>` — X commits, Y PRs merged by [contributors]. Key changes: <summary>.

---

## Personalized week-in-review

### For <Person>

* **Top contribution:** Their most significant delivery or progress this week.
* **Carried into next week:** Outstanding commitments or open items.
* **Cross-team:** Items from others that need their attention.

*(Repeat for each team member. Skip members with no signals.)*

---

## Structural observations

Roll-up of daily structural observations, deduplicated and prioritized:

* Recurring gaps (flagged on multiple days).
* Unresolved items from last week.
* New structural concerns.
* Days in the window with no daily digest (coverage gaps).

---

## Pipeline / sales / opportunity weekly view (optional)

For each active opportunity:

* **<Client>** — Status: <Active / Pending / Critical / Slow>. Change vs last week: <description>. Next action: <what + who>.
```

Every issue identifier in a weekly digest must correspond to an item actually seen during collection or named in a daily digest you read. The wider window makes invention easier and harder to spot — never guess an ID.
```

Note the nested fence: the outer fenced block containing the weekly template is opened with ```` ```markdown ```` and closed with ```` ``` ````, and the heatmap fence inside it is a plain ```` ``` ```` pair. This matches how the day template already nests its own tables. Confirm the file still renders as a single well-formed markdown document after the edit — Step 8's `gather.py --check` will not catch a fence imbalance.

- [ ] **Step 6: Delete `/weekly-digest` and repoint the three source references**

```bash
git rm .agents/commands/weekly-digest.md
```

In `.agents/commands/project-manager.md`, replace `:21`:

```markdown
- `/daily-digest`, `/weekly-digest` — *retrospective, team-wide*: what the team shipped.
```

with:

```markdown
- `/daily-digest` — *retrospective, team-wide*: what the team shipped, over a day or a week (`/daily-digest --week`).
```

In `.agents/commands/awow-add.md`, replace `:14`:

```markdown
- The command name (e.g. `daily-digest`, `coaching-review`, `weekly-digest`)
```

with:

```markdown
- The command name (e.g. `daily-digest`, `coaching-review`, `daily-checkin`)
```

In `.agents/commands/README.md`, replace `:11`:

```markdown
| `standardise` | Opt-in via `/awow-add <command>` (most of team active) | `daily-checkin`, `daily-digest`, `weekly-digest`, `project-manager` (parked) |
```

with:

```markdown
| `standardise` | Opt-in via `/awow-add <command>` (most of team active) | `daily-checkin`, `daily-digest`, `kb-mine`, `kb-synthesize` |
```

`project-manager` leaves this row because Task 3 made it `channel: vendored` — it is no longer an `/awow-add` candidate. `kb-mine` and `kb-synthesize` are both `phase: standardise` and were missing from the row already.

- [ ] **Step 7: Verify no live source still names the command**

```bash
python tools/gather.py
grep -rn 'weekly-digest' .agents/commands/ .agents/AGENTS.md context/ dist/commands/ dist/agent-skills/*/SKILL.md .claude/ .github/prompts/ ; echo "exit=$?"
```

Expected: no output and `exit=1`.

Two known hits are **deliberately out of scope for this task**, and both are named in the spec as PR 3's:

- `.agents/skills/awow-usage-coach/scripts/awow_extract.py:78` (`"weekly-digest": "standardise"`). `KNOWN_COMMANDS` is a *coverage* catalogue, not a live command index — its own comment at `:69-70` says it "can call out *coverage* (which exist, which are unused)", and it already carries two commands that do not exist (`board-skill`, `cross-team-view`). A stale entry there is data, not a dangling pointer. §4.3 assigns the file to PR 3, which moves it to the telemetry plugin.
- `.agents/skills/session-correlation/SKILL.md:11`, `:80`. §4.3 assigns this file to PR 3 for the same move. Leaving it here keeps two PRs from contending for one file, which is the rule PR 1 followed for `using-awow`.

`guides/*.html` and `meta/**` also still name it; §5.3 assigns the guides sweep to PR 4, and `meta/**` is historical record.

- [ ] **Step 8: Verify build, lint, and the sixteen-command target**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tools/validate-evals.py
ls dist/commands/ | wc -l
ls dist/commands/
```

Expected: all three pass; `16`; and the listing is exactly `artifact.md awowify.md coaching-review.md daily-checkin.md daily-digest.md design-system.md kb-mine.md kb-synthesize.md my-work.md process-retro.md process-transcript.md process-workitem.md project-plan.md refinement-prep.md setup-awow.md solution-design-flow.md`. This is §4.4's target: twenty become sixteen.

- [ ] **Step 9: Commit**

```bash
git add .agents/commands .claude/ .github/ dist/
git commit -m "Merge the weekly window into /daily-digest as a --week parameter and delete /weekly-digest outright, with no alias. The weekly altitude keeps its ISO-week resolution, its prior-dailies source, its last-week comparison, and all nine output subsections."
```

---

### Task 6: Rework `/daily-digest`'s delivery — markdown, gate, PR

**Files:**
- Modify: `.agents/commands/daily-digest.md` — Phase 3's front matter and Delivery step, Phases 4-6, and two Behavioral boundaries

**Interfaces:**
- Consumes: Task 5's Phase 0-3 structure and both output paths (`digests/YYYY-MM-DD.md`, `digests/weekly/YYYY-Www.md`).
- Produces: the final phase numbering — `Phase 0 Window & reuse check`, `Phase 1 Data collection`, `Phase 2 Synthesis`, `Phase 3 Markdown output`, `Phase 4 Review gate`, `Phase 5 Open the PR`. Task 7 consumes this numbering when it rewrites the eval suite's invariant table. Task 9 edits Phase 1's hard stop, which this task does not touch.

**Why:** §4.4 and §12. The team stopped sharing digests by email; digests now land as a markdown file for an eleventy site, delivered by PR. The existing rendering rules at `:216-223` are *email-client* constraints — *"Use **table layout** (not div-only)… All styles must be **inline** — email clients strip `<style>` blocks"* — and they actively fight the new path. `digests/TEMPLATE.html`, which Phase 4 reads, has never existed in git.

**No HTML rendering at all.** A styled standalone digest is `/artifact`'s job — it already owns house-styled HTML and reads the design system. `digests/TEMPLATE.html` is never created; if a template is wanted it is an eleventy layout living in the eleventy site, not in awow.

**The eleventy front-matter contract — spec §11 left this open; resolved here.** There is no eleventy site in this repo, and no `digests/` directory: `find . -name '*eleventy*' -o -name '.eleventy.js'` returns nothing and `ls digests` returns `No such file or directory`. The site is the **adopter's**, so awow cannot know its layout names, permalink pattern, or collection tags — and naming a `layout:` that does not exist is a hard eleventy build failure, which is worse than omitting it.

Resolution: emit a minimal, universally-valid default (`title`, `date`, `tags`, no `layout`), and infer the rest from siblings. If `digests/` already holds a digest with front matter, copy its key set — including `layout` and any permalink — exactly. This is the same infer-format-from-siblings rule §4.6 establishes for `/update-context`, it needs no new config file, and it costs nothing on the first run. `tags` uses eleventy's list form so a site gets `collections.digest` spanning both windows plus `collections.daily` / `collections.weekly` separately.

- [ ] **Step 1: Give Phase 3 its front matter**

In `.agents/commands/daily-digest.md`, find the line `Write to `digests/YYYY-MM-DD.md`:` immediately below the `## Phase 3 — Markdown output` heading, and replace that single line with:

```markdown
Write to `digests/YYYY-MM-DD.md` (day window) or `digests/weekly/YYYY-Www.md` (week window).

### Front matter

The digest is a page in the team's eleventy site, so it opens with YAML front matter. awow does not know that site's layouts or permalink scheme, so **infer them: if `digests/` already holds a digest carrying front matter, copy its key set exactly** — same keys, same order, same `layout` and permalink if present — and fill in this run's values.

If there is no sibling to copy from, emit this default and nothing more:

```yaml
---
title: "Daily digest — 2026-07-20"
date: 2026-07-20
tags: [digest, daily]
---
```

For a week window:

```yaml
---
title: "Weekly digest — 2026-W29"
date: 2026-07-17
tags: [digest, weekly]
---
```

`date` is the window's last day. **Never invent a `layout:` key.** Naming a layout the site does not have breaks its build, which is a worse failure than a page rendering unstyled. The site owner adds `layout` once, to one digest, and every later run inherits it.

Then the body:
```

- [ ] **Step 2: Replace the Delivery step**

Replace the `### Delivery` block — the three numbered lines ending `but do NOT execute any sharing without confirmation).` — with:

```markdown
### Delivery

Write the file, then go to Phase 4. Do not share, send, or publish anything from this phase.
```

- [ ] **Step 3: Replace Phases 4, 5, and 6 wholesale**

Delete everything from `## Phase 4 — HTML rendering (email mode only)` through the closing ``` of Phase 6's confirmation block — that is the old Phase 4 (HTML render), Phase 5 (browser review gate), and Phase 6 (send email) in full — and put in their place:

```markdown
## Phase 4 — Review gate

**Mandatory. Never skip.** Nothing leaves this repo until the user has read the digest.

1. Show the user the file path and a short summary: the window, the number of items synthesised, the sources and their status, and any coverage gaps.
2. Present the options verbatim:

```
Digest written to <path>.

- "ship"            — open a PR with this digest
- "edit <what>"     — change it, then come back here
- "stop"            — leave the file on disk, no PR
```

3. **Wait for an explicit answer.** On `edit`, make the change, re-summarise, and return to this prompt.
4. On `stop`, say where the file is and finish. The file staying on disk uncommitted is a valid outcome, not a failure.

---

## Phase 5 — Open the PR

Only after `ship`.

1. Create a branch off the current branch: `digest/YYYY-MM-DD` for a day window, `digest/YYYY-Www` for a week window. If the branch already exists, reuse it.
2. Commit **only** the digest file. Never sweep unrelated working-tree changes into a digest commit — check `git status` first and, if anything else is staged, unstage it and say so.
3. Commit message: `Add the daily digest for YYYY-MM-DD.` or `Add the weekly digest for YYYY-Www.`
4. Push and open the PR with `gh`. Title matches the commit message; body is the digest's narrative section, so a reviewer sees the substance in the PR itself.
5. Report the PR URL.

**When the PR cannot be opened.** If there is no git remote, or `gh` is absent or unauthenticated, do not fail silently and do not skip the commit. Commit on the branch, then tell the user exactly what is missing and the literal command to finish it themselves — for example `gh pr create --fill --head digest/2026-07-20`. A digest committed on a branch with the user told how to raise the PR is a complete run; a digest silently left unpushed is not.
```

- [ ] **Step 4: Drop the two dead behavioral boundaries**

In `## Behavioral boundaries`, delete these two lines:

```markdown
- **Never send email without explicit user approval.**
- **Never hardcode recipients.**
```

and replace the `- **Read-only.**` line above them with:

```markdown
- **Read-only against every source.** The board, the codebase, and every external system are read, never written. The only writes are the digest file and its branch.
- **Never open a PR without the Phase 4 gate.** No exceptions, no "obviously fine" runs.
- **No HTML.** This command produces markdown. A styled standalone digest is `/artifact`'s job — it owns the house style and reads the design system. Do not render HTML here, and do not create `digests/TEMPLATE.html`.
```

- [ ] **Step 5: Update the pipeline overview**

Replace the fenced pipeline block near the top of the file:

```
Phase 0 ─ Input & mode detection
Phase 1 ─ Data collection
Phase 2 ─ Synthesis
Phase 3 ─ Markdown output
Phase 4 ─ (Optional) HTML rendering   ──→ GATE (manual review)
Phase 5 ─ (Optional) Email send
```

with:

```
Phase 0 ─ Window & reuse check
Phase 1 ─ Data collection
Phase 2 ─ Synthesis
Phase 3 ─ Markdown output (with eleventy front matter)
Phase 4 ─ Review gate  ──→ GATE (mandatory)
Phase 5 ─ Open the PR
```

- [ ] **Step 6: Verify every trace of the email path is gone**

```bash
grep -nic 'email\|TEMPLATE.html\|recipient\|\.html' .agents/commands/daily-digest.md
grep -n 'email\|TEMPLATE\|recipient' .agents/commands/daily-digest.md
```

Expected: the first prints `1`; the second prints exactly one line — the `- **No HTML.**` boundary from Step 4, which mentions `digests/TEMPLATE.html` in order to forbid it. Any other hit is a fragment Steps 1-5 missed.

```bash
grep -n '^## Phase' .agents/commands/daily-digest.md
```

Expected exactly six lines, in order: `Phase 0 — Window & reuse check`, `Phase 1 — Data collection`, `Phase 2 — Synthesis`, `Phase 3 — Markdown output`, `Phase 4 — Review gate`, `Phase 5 — Open the PR`.

```bash
tail -8 .agents/commands/daily-digest.md
```

Expected: the `## Handing off` section from Task 4, still last and still intact.

- [ ] **Step 7: Verify build, lint, and the rendered payload**

```bash
python tools/gather.py \
  && python tools/gather.py --check \
  && python tools/lint-paths.py
grep -c 'Phase 5 — Open the PR' dist/commands/daily-digest.md dist/agent-skills/daily-digest/SKILL.md
```

Expected: build and lint pass; both `dist/` files report `1`.

- [ ] **Step 8: Commit**

```bash
git add .agents/commands/daily-digest.md .claude/ .github/ dist/
git commit -m "Rework /daily-digest delivery: markdown with eleventy front matter, a mandatory review gate, then a PR. The email path and its never-committed digests/TEMPLATE.html are deleted, not rebuilt — styled HTML is /artifact's job."
```

---

### Task 7: Bring `tests/daily-digest/` in line with the new delivery

**Files:**
- Modify: `tests/daily-digest/README.md` (the invariants table, the scenarios table, the fixture-conventions note)
- Modify: `tests/daily-digest/scripts/{busy-day,quiet-day,degraded-chat,unknown-actor}.txt`
- Modify: `tests/daily-digest/rubrics/busy-day.md` (Q8, Q11)
- Modify: `tests/daily-digest/checks/{busy-day,quiet-day,degraded-chat,unknown-actor}.sh`

**Interfaces:**
- Consumes: Task 6's phase numbering and the Phase 4 gate vocabulary (`ship` / `edit` / `stop`).
- Produces: a green suite under the new command shape. Task 8 adds a fifth scenario on top of this structure.

**What actually changed for these fixtures, and what did not.** All four fixtures ship `context/tooling/board.md`, so Task 9's board fallback is never exercised by them and their behaviour on that axis is unchanged — the fallback needs its own scenario, which is Task 8. What *does* change is delivery: every script's reply and comment assumes email mode and a post-delivery "share specific sections?" question that no longer exists, and every `post()` asserts `file-absent digests/$d.html` with the justification "markdown-only mode", a mode that no longer has an alternative.

Keep the `.html` assertions. Their reason is now stronger, not weaker: Task 6 forbids HTML rendering outright, so an emitted `.html` is a boundary violation rather than a mode error. Only the comment changes.

- [ ] **Step 1: Rewrite all four scripts**

Every one of `tests/daily-digest/scripts/busy-day.txt`, `quiet-day.txt`, `degraded-chat.txt`, and `unknown-actor.txt` currently holds this identical content:

```
# /daily-digest with no email arguments: markdown-only mode. The pre-seeded
# snapshot satisfies the reuse check, so the only ask-the-user point is the
# post-delivery "share specific sections?" question. Decline it.
no
```

Replace the content of each of the four with:

```
# /daily-digest with no argument: the day window, today. The pre-seeded snapshot
# satisfies the reuse check, so the only ask-the-user point is the Phase 4 review
# gate. Answer "stop" — the scratch workspace has no remote, and the digest file
# on disk is what the checks assert. A run that opens a PR here is a bug.
stop
```

- [ ] **Step 2: Update the four checks comments**

In `tests/daily-digest/checks/busy-day.sh`, replace the final line of `post()`:

```bash
  file-absent "digests/$d.html"
```

with:

```bash
  # No HTML, ever — the command forbids rendering it (Behavioral boundaries).
  file-absent "digests/$d.html"
  file-contains "digests/$d.md" 'tags:'
```

Apply the identical replacement to `checks/quiet-day.sh`, `checks/degraded-chat.sh`, and `checks/unknown-actor.sh`. The added `file-contains` asserts the eleventy front matter Task 6 introduced — the one new mechanically-checkable fact, and the cheapest place to catch a run that forgets it.

Do not add the exec bit to any of these. `validate-evals.py` requires `checks/*.sh` to be **not** executable (they are sourced, not spawned) and Step 6 will fail if that changes.

- [ ] **Step 3: Update the busy-day rubric**

In `tests/daily-digest/rubrics/busy-day.md`, replace the preamble sentence:

```markdown
Full snapshot: three board items (AWOW-101/102/103), a PR with a diff canary plus a commit, and one chat message hinting that Asha's rate-limit schema can serve Bram's throttling. Script declines the post-delivery sharing ask.
```

with:

```markdown
Full snapshot: three board items (AWOW-101/102/103), a PR with a diff canary plus a commit, and one chat message hinting that Asha's rate-limit schema can serve Bram's throttling. Script answers `stop` at the Phase 4 review gate.
```

Replace Q8:

```markdown
8. *(invariant 1)* Did the run stop at the sharing question and respect the scripted `no` — no email rendering, no sends, no board writes?
```

with:

```markdown
8. *(invariant 1)* Did the run present the Phase 4 review gate and respect the scripted `stop` — no branch created, no commit, no `gh` invocation, no board writes?
```

Replace Q11:

```markdown
11. *(invariant 7)* No `digests/<today>.html` exists (markdown-only mode).
```

with:

```markdown
11. *(invariant 7)* No `digests/<today>.html` exists, and the markdown opens with YAML front matter carrying `title`, `date`, and `tags` — and no `layout` key, since the fixture has no sibling digest to infer one from.
```

- [ ] **Step 4: Update the suite README**

In `tests/daily-digest/README.md`, replace invariant rows 1 and 7 of the table:

```markdown
| 1 | Read-only: no board/codebase/external mutation; no email machinery without recipients | header, Behavioral boundaries |
```

```markdown
| 7 | Output lands at `digests/YYYY-MM-DD.md` with the Phase 3 skeleton; no HTML outside email mode | Phase 3, Phase 4 |
```

with:

```markdown
| 1 | Read-only against sources: no board/codebase/external mutation; no branch, commit, or PR before the Phase 4 gate | header, Phase 4, Behavioral boundaries |
```

```markdown
| 7 | Output lands at `digests/YYYY-MM-DD.md` with eleventy front matter and the Phase 3 skeleton; no HTML, ever | Phase 3, Behavioral boundaries |
```

In the same file, replace the `busy-day` scenario row:

```markdown
| `busy-day` | 3 board items, 1 PR (with diff canary `QX-DIFF-CANARY-7Q`) + 1 commit, 1 chat message hinting a cross-connection | Full synthesis; diff blindness (inv 3); ref integrity (inv 5); markdown-only output (inv 7) |
```

with:

```markdown
| `busy-day` | 3 board items, 1 PR (with diff canary `QX-DIFF-CANARY-7Q`) + 1 commit, 1 chat message hinting a cross-connection | Full synthesis; diff blindness (inv 3); ref integrity (inv 5); front matter and no-HTML output (inv 7) |
```

And add one sentence to the end of the opening `**Principle.**` paragraph:

```markdown
Every scenario answers `stop` at the Phase 4 review gate: the scratch workspace has no git remote, and the assertion surface is the digest file on disk, not a PR.
```

- [ ] **Step 5: Verify the suite still validates**

```bash
python3 tools/validate-evals.py
```

Expected: `OK: 2 suite(s), 12 scenario(s), 0 finding(s)`.

```bash
for f in tests/daily-digest/checks/*.sh; do test -x "$f" && echo "BAD exec bit: $f"; done; echo "exec-bit check done"
```

Expected: only `exec-bit check done`.

- [ ] **Step 6: Commit**

```bash
git add tests/daily-digest/
git commit -m "Update the daily-digest suite for the new delivery shape: scripts answer stop at the Phase 4 gate instead of declining an email share, and every scenario now asserts eleventy front matter. The no-HTML assertions stay and get a stronger reason."
```

---

### Task 8: A scenario for the board fallback

**Files:**
- Create: `tests/daily-digest/fixtures/no-board/activity/2026-07-01.json`, `tests/daily-digest/fixtures/no-board/context/team/members.md`, `tests/daily-digest/fixtures/no-board/context/tooling/activity-collection.md`
- Create: `tests/daily-digest/setup/no-board.sh` (executable), `tests/daily-digest/scripts/no-board.txt`, `tests/daily-digest/rubrics/no-board.md`, `tests/daily-digest/checks/no-board.sh` (not executable)
- Modify: `tests/daily-digest/README.md` (scenarios table)

**Interfaces:**
- Consumes: Task 7's `stop`-at-the-gate convention.
- Produces: the only automated coverage of §4.2 in the release. Task 9 implements the behaviour this scenario asserts; run this scenario after Task 9, not before.

**Why this scenario is worth its weight.** §4.2 is the headline behaviour change of the release, and §9's human checklist — *"each of the day-one six either completes or asks once and proceeds; none hard-stops"* — is the only thing currently guarding it. That checklist is a human running live installs. One model-graded scenario, at the cost of four small files, converts the central claim from "someone will check by hand" into a suite result.

**Why the digest still produces without `board.md`.** The fixture pre-seeds `activity/<date>.json`, so the collection contract's reuse check short-circuits and no source is queried. The absent `board.md` therefore costs the run only its Data-sources *labels* — which board tool, which repos — and that is exactly what the ask-once question recovers. This is the honest shape of the fallback: absence degrades one field, it does not stop the pipeline.

- [ ] **Step 1: Build the fixture**

Copy the `quiet-day` fixture and remove its board pointer — that fixture is the smallest of the four, so the diff stays about the board and nothing else:

```bash
cp -R tests/daily-digest/fixtures/quiet-day tests/daily-digest/fixtures/no-board
rm -f tests/daily-digest/fixtures/no-board/context/tooling/board.md
ls -R tests/daily-digest/fixtures/no-board
```

Expected: `activity/2026-07-01.json`, `context/team/members.md`, `context/tooling/activity-collection.md`, and **no** `context/tooling/board.md`.

If `quiet-day` has no `context/tooling/board.md` to remove, the `rm -f` is a no-op and the fixture is already correct — verify with the `ls -R` output rather than assuming either way.

- [ ] **Step 2: Copy the setup hook**

```bash
cp tests/daily-digest/setup/quiet-day.sh tests/daily-digest/setup/no-board.sh
chmod +x tests/daily-digest/setup/no-board.sh
test -x tests/daily-digest/setup/no-board.sh && echo "executable — correct"
```

Expected: `executable — correct`. Setup hooks are spawned, so unlike `checks/*.sh` they must carry the exec bit.

- [ ] **Step 3: Write the script**

Create `tests/daily-digest/scripts/no-board.txt`:

```
# No context/tooling/board.md. The scratch workspace has no git remote, so the
# board cannot be inferred and the run must ask exactly once. Answer it, then
# answer the Phase 4 review gate. Two replies, in this order — a run that asks
# a third time, or halts instead of asking, is the bug this scenario catches.
GitHub Issues on SampleOrg/awow-sample, via the gh CLI
stop
```

- [ ] **Step 4: Write the checks**

Create `tests/daily-digest/checks/no-board.sh` (do **not** chmod it):

```bash
# Checks — no-board. The board pointer is absent and the workspace has no git
# remote: the run must ask once, record the answer, and still produce a digest.
# Mirrors rubric Q1-Q4.

pre() {
  local d; d=$(date +%F)
  file-exists "activity/$d.json"
  file-contains "activity/$d.json" 'AWOW-201'
  file-exists context/team/members.md
  file-absent context/tooling/board.md
  dir-absent digests
}

post() {
  local d; d=$(date +%F)
  file-exists "digests/$d.md"
  file-contains "digests/$d.md" 'AWOW-201'
  file-contains "digests/$d.md" 'tags:'
  file-exists .awow/board-session.md
  file-contains .awow/board-session.md 'GitHub Issues'
  # Still never HTML, and the board pointer was not invented on the user's behalf.
  file-absent "digests/$d.html"
  file-absent context/tooling/board.md
}
```

The last assertion is the one that earns the scenario. §4.2 says record the answer *for the session* and offer `/setup-awow` Step 1 to make it durable — a run that writes `context/tooling/board.md` itself has skipped the wizard that owns that file and fabricated a team-data file from one throwaway answer, which is precisely the failure §4.1.2 calls an active harm.

- [ ] **Step 5: Write the rubric**

Create `tests/daily-digest/rubrics/no-board.md`:

```markdown
# Rubric — no-board

Same one-item snapshot as `quiet-day`, with `context/tooling/board.md` removed and no git remote in the scratch workspace. Script supplies the board answer, then `stop` at the review gate.

## Behaviour during the run

1. *(invariant 1)* Did the run continue past the missing `board.md` rather than halting? A hard stop is an outright fail, whatever else the run did.
2. *(invariant 1)* Did it ask about the board **exactly once** — not zero times (silently guessing), not twice?
3. *(invariant 1)* Did it try to infer the board from the git remote before asking, and correctly fall through to asking because the scratch workspace has none?
4. *(invariant 1)* Did it offer `/setup-awow` Step 1 as the way to make the answer durable, rather than writing `context/tooling/board.md` itself?
5. *(invariant 2)* Did it reuse `activity/<today>.json` and query no live source — the absent board pointer must not trigger a live lookup?
6. *(invariant 4)* Does the Data sources table name the board the user supplied, and reflect the real status of each source without inventing counts?

## Post-run state

7. *(invariant 7)* `digests/<today>.md` exists, opens with YAML front matter, and carries the `## Data sources` table.
8. *(invariant 1)* `context/tooling/board.md` was not created. The session answer lives at `.awow/board-session.md` and nowhere else.
```

- [ ] **Step 6: Add the scenario to the suite README**

In `tests/daily-digest/README.md`, add a row to the end of the Scenarios table:

```markdown
| `no-board` | `quiet-day`'s snapshot with `context/tooling/board.md` removed, no git remote | The §4.2 fallback: ask once, do not halt, do not author `board.md` (inv 1) |
```

And append to the Fixture conventions list:

```markdown
- `no-board/` deliberately ships **no** `context/tooling/board.md`. Do not "fix" it by adding one — its absence is the fixture.
```

- [ ] **Step 7: Verify the wiring**

```bash
python3 tools/validate-evals.py
```

Expected: `OK: 2 suite(s), 13 scenario(s), 0 finding(s)` — one more scenario than before.

```bash
test -x tests/daily-digest/checks/no-board.sh && echo "BAD: checks must not be executable" || echo "checks exec bit correct"
test -x tests/daily-digest/setup/no-board.sh && echo "setup exec bit correct" || echo "BAD: setup must be executable"
git check-ignore -v tests/daily-digest/fixtures/no-board/activity/2026-07-01.json; echo "exit=$?"
```

Expected: `checks exec bit correct`, `setup exec bit correct`, then `exit=1` with no output — the `!tests/*/fixtures/**/activity/**` re-include in `.gitignore` keeps the snapshot tracked. `validate-evals.py` fails on a gitignored fixture, so a non-1 exit here is a real break.

- [ ] **Step 8: Commit**

```bash
git add tests/daily-digest/
git commit -m "Add a no-board scenario to the daily-digest suite: the fixture ships no board pointer and no remote, so the run must ask once, keep going, and never author context/tooling/board.md itself. It fails until Task 9 lands the fallback."
```

---

### Task 9: The board fallback, across eleven commands

**Files:**
- Modify (BLOCK A, the two surviving hard stops): `.agents/commands/daily-digest.md`, `.agents/commands/kb-mine.md`
- Modify (BLOCK B, the nine context-list citations): `.agents/commands/daily-checkin.md`, `my-work.md`, `process-workitem.md`, `project-plan.md`, `refinement-prep.md`, `coaching-review.md`, `process-retro.md`, `process-transcript.md`, `solution-design-flow.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: the trimmed command set from Tasks 1-6 — `daily-routine` and `project-manager` are excluded from the eleven precisely because they are gone or vendored. The ask-once rule itself already sits in `.agents/skills/using-awow/SKILL.md` from PR 1; this task makes the command bodies agree with it.
- Produces: `.awow/board-session.md` as the named cross-command session store. Task 8's `no-board` scenario asserts against it.

**Why the second paragraph is not optional:** §4.2. All the current hard stops read *"no `board.md`, **or a fatal auth failure on a source**"*. Only the first half relaxes. Dropping the auth half would trade a startup gate for a correctness bug — a digest synthesised from a half-snapshot, presented as complete.

**Why two blocks and not one.** After Task 4 deletes `daily-routine`, only two of the three original hard stops survive: `daily-digest` and `kb-mine`. Those two need both paragraphs, because only they carry an auth guard to preserve. The other nine sites never hard-stopped — they cite `board.md` in a read-this-first list — so they need the absence rule and nothing else. Two plus nine is the eleven §4.2 names.

**Where the session answer lives.** §4.2 requires a mechanism for "do not ask again"; without one an implementer builds per-invocation asking, which is not what the section means. Use `.awow/board-session.md`, extending the repo-local flag pattern `hooks/session-start:25` and `:47` already read (`.awow/no-setup-prompt`, `.awow/no-engine-prompt`). Session scoping is a `session:` line in the file: a note whose `session:` does not match the current session is stale and ignored, so the answer does not silently outlive the session that gave it.

**BLOCK A** — for `daily-digest` and `kb-mine`:

```markdown
**An absent board pointer is a question, not a stop.** If `{HUB}/context/tooling/board.md` is missing, infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess a board from a GitLab, Bitbucket, or Azure DevOps remote; those map to several products. With no remote, or with `gh` absent or unauthenticated, ask the user once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line, and read it instead of asking again — ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make the answer durable; never write `context/tooling/board.md` yourself.

This relaxation covers an absent pointer only. **A fatal auth failure on a data source still stops the run** — surface it and do not synthesise from a half-snapshot.
```

**BLOCK B** — for the other nine:

```markdown
**An absent `board.md` is a question, not a stop.** Infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess from a GitLab, Bitbucket, or Azure DevOps remote; ask. With no remote, or with `gh` absent or unauthenticated, ask once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line and read it rather than asking twice; ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make it durable; never write `context/tooling/board.md` yourself.
```

- [ ] **Step 1: Enumerate the eleven sites and confirm each anchor**

```bash
for f in daily-digest kb-mine daily-checkin my-work process-workitem project-plan \
         refinement-prep coaching-review process-retro process-transcript solution-design-flow; do
  printf '%-22s ' "$f"
  grep -c 'board\.md' ".agents/commands/$f.md"
done
```

Expected: every line reports at least `1`. `daily-checkin` reports `3`, `daily-digest` `2`, `process-retro` `2`. A `0` anywhere means an earlier task moved something unexpectedly — stop and report.

- [ ] **Step 2: BLOCK A into `daily-digest`**

In `.agents/commands/daily-digest.md`, in Phase 1, replace the hard stop:

```markdown
If the snapshot cannot be produced (no `{HUB}/context/tooling/board.md`, or a fatal auth failure on a source), stop and surface it — do not synthesise from a half-snapshot.
```

with BLOCK A verbatim, then this sentence on its own line after it:

```markdown
If the snapshot still cannot be produced for any other reason, stop and surface it.
```

- [ ] **Step 3: BLOCK A into `kb-mine`**

In `.agents/commands/kb-mine.md`, replace the hard stop:

```markdown
If the snapshot cannot be produced (no `{HUB}/context/tooling/board.md`, or a fatal auth
failure on a source), stop and surface it — do not mine a half-snapshot.
```

with BLOCK A verbatim, except that its final clause reads `do not mine from a half-snapshot` rather than `do not synthesise from a half-snapshot`, followed on its own line by:

```markdown
If the snapshot still cannot be produced for any other reason, stop and surface it.
```

- [ ] **Step 4: BLOCK B into the nine citation sites**

Each of these cites `board.md` in a list of files to read. Insert BLOCK B as a paragraph immediately **after** the list containing that citation, in each of the nine files. Exact anchor per file — insert after the line quoted:

- `.agents/commands/daily-checkin.md`, after `:20` — the paragraph ending `Read those before proposing anything, and when in doubt, propose less.`
- `.agents/commands/my-work.md`, after `:33` — `Query the board (surface per `{HUB}/context/tooling/board.md`) for items assigned to that person across all states. Pull enough to triage: title, state, priority, due date, last-update time, parent, and whether the item is blocked or in review.`
- `.agents/commands/process-workitem.md`, after `:30` — the paragraph beginning `Resolve the ID via the team's board surface`
- `.agents/commands/project-plan.md`, after `:46` — the paragraph beginning `Read the design artefact and its decomposed work items`
- `.agents/commands/refinement-prep.md`, after `:50` — the list item `- `{HUB}/context/tooling/board.md` — sizing rules per board family`
- `.agents/commands/coaching-review.md`, after `:66` — the line `Absence improves nothing; it does not block the pipeline. Proceed.`
- `.agents/commands/process-retro.md`, after `:78` — the list item `- A reachable agent-activity / token-spend log (optional) — enables cost analysis. Don't fabricate; if it's not there, omit the section.`
- `.agents/commands/process-transcript.md`, after `:70` — the line `Do **not** gate on context — proceed with whatever is available. The context improves accuracy; its absence does not block the pipeline.`
- `.agents/commands/solution-design-flow.md`, after `:56` — the line `If a knowledge-base subfolder is empty, note it but proceed. Absence improves nothing; it does not block the pipeline.`

In each case leave a blank line before and after the inserted paragraph. Four of these files (`coaching-review`, `process-retro`, `process-transcript`, `solution-design-flow`) already say absence does not block the pipeline — BLOCK B does not contradict that, it says what to do *instead* of proceeding blind, which is the half those four never specified.

- [ ] **Step 5: Ignore the session note**

`.awow/` is not currently ignored, even though `hooks/session-start` already writes `.awow/no-setup-prompt` and `.awow/no-engine-prompt` into it. The board note carries a machine-local session id and a team's board URL, and this repo is public. In `.gitignore`, immediately after the `# Distribution targets (per-machine config)` block ending `tools/.distribute-targets`, add:

```
# Per-session agent state: setup/engine nudge opt-outs and the board answer the
# §4.2 fallback records. Machine-local, session-scoped, never a durable record —
# the durable board pointer is context/tooling/board.md, written by /setup-awow.
.awow/
```

Then confirm no tracked file is caught:

```bash
git ls-files | grep '^\.awow/' ; echo "exit=$?"
python3 tools/validate-evals.py
```

Expected: no output and `exit=1`; then `OK: 2 suite(s), 13 scenario(s), 0 finding(s)` — `validate-evals.py` fails on a gitignored fixture file, so this proves no fixture is under `.awow/`.

- [ ] **Step 6: Verify all eleven carry the rule and both guards survive**

```bash
for f in daily-digest kb-mine daily-checkin my-work process-workitem project-plan \
         refinement-prep coaching-review process-retro process-transcript solution-design-flow; do
  printf '%-22s ' "$f"
  grep -qF '.awow/board-session.md' ".agents/commands/$f.md" && printf 'fallback ' || printf 'MISSING! '
  grep -qF 'never write `context/tooling/board.md` yourself' ".agents/commands/$f.md" && echo 'no-author-guard' || echo 'MISSING no-author-guard'
done
```

Expected: eleven lines, each `fallback no-author-guard`.

```bash
grep -c 'fatal auth failure' .agents/commands/daily-digest.md .agents/commands/kb-mine.md
```

Expected: `1` for each. The auth guard survives in both — this is the half §4.2 says must not relax.

```bash
grep -rn 'stop and surface it — do not synthesise from a half-snapshot\|stop and surface it — do not mine a half-snapshot' .agents/commands/ ; echo "exit=$?"
```

Expected: no output and `exit=1`. The old unconditional hard stops are gone.

- [ ] **Step 7: Verify build, lint, and every suite**

```bash
python tools/gather.py \
  && python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tools/validate-evals.py \
  && bash tests/harness/run-harness-tests.sh all
```

Expected: all pass. `.awow/board-session.md` is not a `context/`, `tools/`, or `proposals/` path, so `BARE` at `lint-paths.py:11` does not match it.

- [ ] **Step 8: Commit**

```bash
git add .agents/commands .claude/ .github/ dist/ .gitignore
git commit -m "Replace the absent-board.md hard stop with the ask-once fallback across eleven commands, recording the answer at .awow/board-session.md for the session. The fatal-auth-failure guard is preserved in both commands that carry one."
```

---

### Task 10: Regenerate `tools/awow.lock.json`

**Files:**
- Modify: `.claude-plugin/plugin.json` (version `0.5.0` → `0.6.0`)
- Modify: `tools/awow.lock.json` (regenerated)

**Interfaces:**
- Consumes: the final file tree from Tasks 1-9. **This task must run last of the code tasks** — the lockfile is a hash of the tree, so any later edit invalidates it.
- Produces: nothing consumed downstream. `tests/awow-lock/test_awow_lock.py` builds its own throwaway repos and never reads this file, so it is unaffected either way.

**Why the version bump belongs here, and why `0.6.0`.** §8 says `0.6.0` minimum but does not assign the bump to a PR. `meta/plans/2026-07-12-wi2-neutral-token-sweep.md:19` states the repo's rule: *"Every payload-visible change bumps `.claude-plugin/plugin.json` version"*. PR 2 is the payload-visible change — four commands leave `dist/commands/`. Bumping here also makes the lockfile self-consistent: `cmd_backfill` reads the version from `.claude-plugin/plugin.json` via `_read_version` (`awow_lock.py:189-201`), so a lock regenerated against a `0.5.0` manifest would record a version that no longer describes the tree. PR 3's second plugin ships at the same `0.6.0` — §4.3 says `awow-telemetry` versions in lockstep for this release, and a second minor bump inside one unreleased release would be noise.

`.github/plugin/plugin.json` stays at `0.1.0`. It is the Copilot manifest on its own version track, `_read_version` only falls through to it when `.claude-plugin/plugin.json` is absent, and nothing in this PR changes it.

**Why the lock cannot simply be re-backfilled in place.** `cmd_backfill` at `awow_lock.py:348-349` reuses the *existing* lock's file list when one is present (`rels = list(lock["files"])`) and takes the version from the existing lock first (`:340-343`). Run against the current file, it would keep `awow_version: 0.2.0` and never learn about files added since. Deleted files do drop out — `:353` filters on `.exists()` — but that is only half the job. The lock must be removed first so `backfill` takes the `_iter_starter_files` branch and the `_read_version` branch.

- [ ] **Step 1: Record the current state**

```bash
python3 -c "
import json; d=json.load(open('tools/awow.lock.json'))
print('version:', d['awow_version']); print('files:', len(d['files']))
for k in ('.agents/commands/cross-team-view.md','.agents/commands/daily-routine.md','.agents/commands/weekly-digest.md','.agents/commands/test-setup-awow.md'):
    print(' ', k, 'listed' if k in d['files'] else 'absent')
"
```

Expected: `version: 0.2.0`, `files: 153`, then `cross-team-view.md listed`, `daily-routine.md listed`, `weekly-digest.md listed`, `test-setup-awow.md absent` — the last is absent because `ALWAYS_EXCLUDE` held it until Task 1 removed that entry.

- [ ] **Step 2: Bump the plugin version**

In `.claude-plugin/plugin.json`, change:

```json
  "version": "0.5.0",
```

to:

```json
  "version": "0.6.0",
```

- [ ] **Step 3: Regenerate from scratch**

```bash
rm tools/awow.lock.json
python tools/awow_lock.py backfill
```

Expected: a single line, `awow.lock.json baseline: <N> files at version 0.6.0 (<commit>)`. `<N>` will differ from 153 — Tasks 1, 4, and 5 removed three command files, and the enumeration branch picks up any starter file added since the lock was last written.

- [ ] **Step 4: Verify the three stale entries are gone and the version is right**

```bash
python3 -c "
import json; d=json.load(open('tools/awow.lock.json'))
assert d['awow_version']=='0.6.0', d['awow_version']
for k in ('.agents/commands/cross-team-view.md','.agents/commands/daily-routine.md','.agents/commands/weekly-digest.md','.agents/commands/test-setup-awow.md','.agents/commands/project-manager.md','.agents/commands/update-awow.md'):
    print(f'{k:48} {\"listed\" if k in d[\"files\"] else \"absent\"}')
print('files:', len(d['files']), 'mode:', d['mode'])
"
```

Expected: `cross-team-view.md absent`, `daily-routine.md absent`, `weekly-digest.md absent`, `test-setup-awow.md absent`, `project-manager.md listed`, `update-awow.md listed`, then the file count and `mode: {'board': 'all', 'solo': False}`.

`project-manager` and `update-awow` stay **listed** and that is correct: `channel: vendored` excludes a command from the *payload*, not from the *starter-owned tree* a vendored adopter receives. Those two are exactly the commands a vendored install still wants.

- [ ] **Step 5: Verify the lock is self-consistent and the engine still works**

```bash
python tools/awow_lock.py status
python3 tests/awow-lock/test_awow_lock.py
```

Expected: `status` reports `awow version: 0.6.0 (<commit>)` and lists no locally-modified starter files — a freshly-backfilled lock hashes the tree as it stands, so any drift here means a file changed between Steps 3 and 5. Then the unittest suite passes; it builds its own throwaway repos at versions `0.1.0` / `0.2.0` and never reads the real lockfile, so it is insensitive to this change.

- [ ] **Step 6: Verify the whole build one more time**

```bash
python tools/gather.py --check && python tools/lint-paths.py
```

Expected: both pass. Neither reads the lockfile; this confirms Step 2's manifest edit did not disturb the payload plan.

- [ ] **Step 7: Commit**

```bash
git add .claude-plugin/plugin.json tools/awow.lock.json
git commit -m "Bump the plugin to 0.6.0 and regenerate the lockfile from scratch, dropping the stale cross-team-view, daily-routine, and weekly-digest entries. A vendored adopter mid-upgrade sees those three as removed-upstream, so /update-awow now names them explicitly."
```

---

### Task 11: Full-suite verification

**Files:** none modified.

**Interfaces:**
- Consumes: everything above.
- Produces: the evidence that PR 2 is complete.

- [ ] **Step 1: Run every check CI runs, plus the four suite-level ones**

```bash
python tools/gather.py --check \
  && python tools/lint-paths.py \
  && python3 tests/gather-tokens/test_tokens.py \
  && python3 tests/payload-classification/test_classification.py \
  && python3 tools/validate-evals.py \
  && python3 tests/awow-lock/test_awow_lock.py \
  && bash tests/harness/run-harness-tests.sh all
```

Expected: every one passes. `validate-evals.py` reports `OK: 2 suite(s), 13 scenario(s), 0 finding(s)`.

- [ ] **Step 2: Confirm the surface is exactly sixteen, and which sixteen**

```bash
ls dist/commands/ | wc -l
ls dist/.github/prompts/ | wc -l
ls dist/agent-skills/ | grep -cE '^(daily-routine|weekly-digest|update-awow|project-manager)$'
```

Expected: `16`, `16`, and `0`. All three payload surfaces agree, because `is_vendored_channel` at `gather.py:424` is the single filter behind all of them.

- [ ] **Step 3: Confirm no shipped prompt names a deleted command**

```bash
grep -rn 'daily-routine\|weekly-digest\|test-setup-awow' dist/commands/ dist/context/ dist/.github/ ; echo "exit=$?"
```

Expected: no output and `exit=1`. `dist/agent-skills/awow-usage-coach/scripts/awow_extract.py` is deliberately excluded from this grep — see Task 5 Step 7 for why that entry is coverage data and belongs to PR 3.

- [ ] **Step 4: Confirm the fallback reached the payload**

```bash
grep -c 'board-session.md' dist/commands/daily-digest.md dist/commands/my-work.md dist/commands/process-workitem.md
grep -c 'fatal auth failure' dist/commands/daily-digest.md dist/commands/kb-mine.md
```

Expected: `1` from every one of the five. The rendered payload carries both halves of §4.2 — the relaxation and the guard.

- [ ] **Step 5: Confirm the email path is gone from the payload**

```bash
grep -rn 'TEMPLATE.html\|Never hardcode recipients\|email clients strip' dist/ ; echo "exit=$?"
```

Expected: no output and `exit=1`.

- [ ] **Step 6: Run the daily-digest suite**

```bash
# Model-graded — this is the one step that needs an agent, not a script.
```

Run `/test-awow daily-digest` and confirm all five scenarios return `pass`. `no-board` is the new one and the one that matters: it fails on any build before Task 9. If a scenario returns `indeterminate`, report it as such — do not re-run until it passes.

- [ ] **Step 7: Report**

Summarise: commands removed and by which mechanism, the eleven commands carrying the fallback, the new eval scenario, the version bump, and anything deferred to PR 3 or PR 4. Do not open a PR and do not push — both need explicit approval.

---

## Self-Review

**Spec coverage.** §4.4 delete `test-setup-awow` → Task 1. §4.4 `channel: vendored` ×2 → Tasks 2, 3. §4.4 `daily-routine` merge → Task 4. §4.4 `weekly-digest` merge and outright deletion → Task 5. §4.4 delivery rework → Task 6. §8 "tests affected: `tests/daily-digest/`" → Tasks 7, 8. §4.2 board fallback across eleven → Task 9. §4.4 lockfile and the mid-upgrade statement → Task 10, with the statement itself written into `/update-awow` at Task 2 Step 3 (the command a vendored adopter actually reads). §8 version → Task 10.

**Ordering.** §10 mandates trim before fallback so step 1 does not edit files step 3 deletes. Tasks 1-6 trim, Task 9 applies the fallback, and the eleven-command list excludes `daily-routine` (deleted, Task 4) and `project-manager` (vendored, Task 3) exactly because of that ordering. §4.4 also mandates window-parameter-then-delivery on `daily-digest` so phase renumbering happens once: Task 5 leaves Phases 0-6 intact and Task 6 does the single renumbering. Task 10 runs after every file edit because the lockfile hashes the tree.

**Three things the spec has wrong, verified against the code:**

1. **"Remove generated stubs and update the two `meta/proposals/` references" (§4.4, `:187`) undercounts.** There are **three** live `meta/proposals/` references — `eval-baseline-and-prompt-cleanup.md:40`, `pi-codex-harness-support.md:72`, `README.md:24` — plus a fourth live reference the spec misses entirely, **outside** `meta/proposals/`: `tests/setup-awow/README.md:15` reads *"(`/test-setup-awow` remains as a deprecated alias.)"*, which becomes false on deletion. Task 1 Steps 2 and 3 handle all four. A further eighteen hits across `meta/proposals/setup-awow-regression-tests.md`, `meta-workspace-and-fixture-decoupling.md`, `meta/plans/`, and three lines of `eval-baseline-and-prompt-cleanup.md` are historical records and are deliberately left.

2. **§11's third open question is unanswerable as posed.** It says the eleventy front-matter contract *"needs one look at the eleventy site before PR 2 writes Phase 3."* There is no eleventy site in this repo — no `.eleventy.js`, no `eleventy` string anywhere outside `docs/superpowers/`, and no `digests/` directory. The site belongs to the adopter, so awow cannot know its layouts or permalinks, and emitting a `layout:` that does not resolve is a hard eleventy build failure. Task 6 resolves it: a minimal always-valid default (`title`, `date`, `tags`, deliberately no `layout`) plus infer-from-siblings, which is the rule §4.6 already establishes for `/update-context`. Reasoning is written into the task rather than deferred.

3. **PR 1's plan carries a false claim about this PR.** `2026-07-20-pr1-payload-addressability.md:1000` says *"If `test_awow_lock.py` fails, the lockfile is stale — that is PR 2's regeneration."* It cannot fail for that reason: `test_awow_lock.py` builds two throwaway git repos in `tempfile.TemporaryDirectory()` (`:69-95`) and never reads `tools/awow.lock.json`. A failure there is a real regression in `awow_lock.py`, not a stale lockfile, and treating it as expected would mask a genuine break. Task 10 Step 5 states the correct relationship.

**One spec claim that is defensible but imprecise.** §4.2 says `board.md` is *"cited by fourteen command files."* Fifteen files under `.agents/commands/` contain the string. The fifteenth is `update-awow.md:24`, where `board.md` appears bare inside a list of paths the command *never rewrites* — not a citation in the sense that matters. Fourteen is right on the intended reading, and `update-awow` leaves the payload in Task 2 regardless.

**Two decisions the spec left open, resolved here with reasoning:**

- **Which PR bumps the version.** §8 states `0.6.0` minimum but assigns it to no PR. Resolved: PR 2, in Task 10. `meta/plans/2026-07-12-wi2-neutral-token-sweep.md:19` records the repo rule — *"Every payload-visible change bumps `.claude-plugin/plugin.json` version"* — and PR 2 is the payload-visible change. It is also mechanically necessary: `cmd_backfill` reads the version from that manifest via `_read_version` (`awow_lock.py:189-201`), so regenerating the lock against a `0.5.0` manifest would record a version that no longer describes the tree. `.github/plugin/plugin.json` stays at `0.1.0` — separate track, only consulted when `.claude-plugin/plugin.json` is absent.

- **Whether PR 2 fixes `awow_extract.py:78` and `session-correlation/SKILL.md`.** Both name `weekly-digest` and both dangle the moment Task 5 lands, but §4.3 assigns both files to PR 3. Resolved: leave them, and Task 5 Step 7 records why. `KNOWN_COMMANDS` is a coverage catalogue by its own comment at `awow_extract.py:69-70` and already carries two commands that do not exist (`board-skill`, `cross-team-view`), so a stale entry is data rather than a broken pointer; `session-correlation/SKILL.md` moves to the telemetry plugin in PR 3, and having two PRs contend for one file is the failure PR 1 avoided for `using-awow`.

**Scope added beyond the eight given items, and why.** Task 8 (the `no-board` eval scenario) is not in the brief. §4.2 is the release's headline behaviour change and §9 guards it only with a human checklist of live installs; four small files convert that into a suite result, and the fixture is a copy of `quiet-day` minus one file. Task 9 Step 5 adds `.awow/` to `.gitignore` — not in the brief either, but the fallback writes a board URL and a machine-local session id into a directory this public repo currently tracks, and `hooks/session-start` has been writing there already.

**Type and vocabulary consistency.** `channel:` takes exactly `vendored`, `bootstrap`, or absent, spelled that way in Tasks 1, 2, 3 and in `gather.py:427` / `lint-paths.py:38`. Phase names after Task 6 are `Phase 0 — Window & reuse check`, `Phase 1 — Data collection`, `Phase 2 — Synthesis`, `Phase 3 — Markdown output`, `Phase 4 — Review gate`, `Phase 5 — Open the PR`, and Tasks 7 and 8 use those exact strings. The gate vocabulary is `ship` / `edit` / `stop`, spelled identically in Task 6 Step 3, all five scripts, and both rubrics. The session note is `.awow/board-session.md` everywhere — Task 8's checks, both blocks in Task 9, and the verification grep in Task 9 Step 6. Window argument forms are `--week`, `YYYY-Www`, `YYYY-MM-DD`, or absent, spelled the same in the frontmatter `argument-hint`, Phase 0, and Task 5 Step 1. Output paths are `digests/YYYY-MM-DD.md` and `digests/weekly/YYYY-Www.md` throughout.

**Placeholder scan.** Two temptations resolved rather than deferred. The eleventy front matter (above) was going to be a "confirm with the site owner" note — that is a TBD wearing a hedge, so Task 6 states the default and the inference rule instead. The version bump was going to read "bump if PR 3 has not already" — a conditional that makes the lockfile's recorded version depend on merge order, so Task 10 fixes it at `0.6.0` and says why. No step reads "similar to Task N"; Task 7 Step 2 and Task 9 Step 4 both apply one text to several files and quote the text in full at the point of use. Every command step states its literal expected output, including the two greps whose pass condition is a non-zero exit.

**Task boundaries.** Eleven tasks, each ending in a commit a reviewer could reject on its own terms. Tasks 2 and 3 are both one-line channel changes and could be one commit, but the arguments differ — `update-awow` is *actively corrupting* in plugin-land, `project-manager` is *parked and unused* — and a reviewer could reasonably accept one and reject the other. Tasks 7 and 8 are split for the same reason: Task 7 is forced by Task 6 and is not optional, while Task 8 adds coverage that a reviewer could defer. Task 11 adds no code; it exists because the seven-check verification run is what proves the PR, and folding it into Task 10 would let it be skipped.
