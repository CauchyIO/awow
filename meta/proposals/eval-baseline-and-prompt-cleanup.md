# Proposal — eval baseline from superpowers-evals + prompt cleanup

**Status:** Draft — Phase 1 (harness hardening, §3) built on `feat/eval-suite-hardening`, awaiting review. Phases 2–4 not started.
**Scope:** (1) adopt the transferable parts of the `../superpowers-evals` (Quorum) methodology to harden and extend awow's eval machinery; (2) anchor quality evals on real data in the `../linear` instance; (3) prune and consolidate the command surface using adopter evidence. Builds on `setup-awow-regression-tests.md` — the existing suite is the seed, not something to replace.

---

## 1. What superpowers-evals does, and what transfers

Quorum evaluates coding agents on **workflow compliance** using two independent witnesses per scenario: an LLM judge grading natural-language acceptance criteria (blind to the deterministic checks), and a `checks.sh` script asserting mechanical facts (files exist, tools called, work landed). A composer folds both into `pass | fail | indeterminate` with strict precedence — a crashed run, broken fixture, or typo'd check yields **indeterminate**, never a false `fail`. Scenarios are a three-file unit (`story.md` / `setup.sh` / `checks.sh`) validated statically in CI without launching any agent.

| Quorum idea | Transfers to awow? | How |
|---|---|---|
| Dual witness: LLM judge + deterministic checks, judge blind to checks | **Yes — the core steal** | Split each rubric's "Post-run state" section into a pure-bash check script; keep behavioural questions LLM-judged |
| First-class `indeterminate` with precedence rules | **Yes** | Extend the current `PASS/FAIL/ABORTED` outcomes: fixture pre-check failure, broken check, empty run → indeterminate, tagged with the stage that failed |
| Three-file scenario unit + static validator in CI | **Yes** | awow already has script+rubric+fixture triples; add `checks.sh` and a real `tools/validate-evals.py` (CI-safe, no LLM, no credentials) |
| Judge/subject separation (two LLMs) | **Partially** | No headless driver under the no-API-key constraint, but the judge can be a **subagent** given only the transcript + post-run state — not the runner's own reasoning context. `linear`'s kb-agent eval already proves this works in-session |
| Belt-and-braces: assert the same fact in AC prose *and* checks; disagreement = triage signal | **Yes** | Rubric questions already tag invariant numbers; mirror the mechanical ones in the check script |
| Fixture provenance rigor (planted defects gated by `pre()`, elicited-not-hand-authored fixtures) | **Yes** | Especially for future workitem/refinement evals: generate fixtures with the command under test, don't hand-write idealised inputs |
| Gauntlet dependency, per-agent adapters/normalizers, cost stack, skill-vocabulary verbs | **No** | Domain-specific plumbing; awow's constraint is "human drives the run in-session, machine grades the result" |

Reference files when implementing: `superpowers-evals/src/composer.ts` (7-rule verdict precedence), `docs/scenario-authoring.md` (authoring conventions incl. fail-vs-indeterminate triage), `scenarios/00-quorum-smoke-hello-world/` (minimal unit).

## 2. Where the current suite falls short of that bar

`tests/setup-awow/` + `/test-setup-awow` is already the right *shape* (frozen fixtures, scripted replies, invariant-tagged rubrics). Measured against Quorum:

1. **Single witness.** The LLM grades everything, including mechanical facts (`board.md` exists, stub files written) that a script should assert. Much of `test-setup-awow.md`'s 147 lines is anti-reward-hacking prose compensating for this.
2. **Self-grading.** The same agent replays the wizard and grades it. Quorum's separation is structural; ours is rhetorical ("follow the rules literally").
3. **No `indeterminate` discipline.** `ABORTED` exists for the zero-turns case only. A wrong fixture or a broken rubric question currently surfaces as a fail (or worse, a pass).
4. **No static validation.** Nothing in CI confirms scenario triples are complete, rubric questions cite real invariant numbers, or fixtures referenced by rubrics exist. `tools/validate-context.py` is a skeleton.
5. **Coverage = one command.** Nothing evaluates the KB pipeline, digests, or transcript processing — the commands with the most prompt churn.

## 3. Phase 1 — harden the harness (awow repo)

1. **Add `checks.sh` per scenario** (`tests/setup-awow/checks/<scenario>.sh`, `pre()` + `post()` only). `pre()` asserts the fixture is intact before the run may grade; `post()` takes over every mechanical rubric question. Keep a small verb prelude (`file-exists`, `file-contains`, `file-absent`) — plain bash, no framework.
2. **Verdict schema with precedence.** Result JSON gains `final: pass|fail|indeterminate` + `stage` on error. Precedence, in order: runner error → indeterminate; failed `pre()` → indeterminate; zero wizard turns → indeterminate; judge pass AND zero failed `post()` → pass; else fail. Broken check (script error, not assertion failure) → indeterminate, never fail.
3. **Judge as a blind subagent.** Phase 4 of the protocol dispatches a grading subagent that receives only the `--- WIZARD TURN ---` transcript and the `ls -laR` state dump — not the runner's context. This replaces most of the anti-self-attestation prose.
4. **`tools/validate-evals.py`** (real, replaces validator-skeleton ambitions for `tests/`): every script has a rubric, checks and fixture; every rubric question tags an invariant that exists in the command; check scripts pass `bash -n`. Runs in CI with zero credentials.
5. **Generalise the runner.** `/test-setup-awow` → `/test-awow [suite] [scenario]` reading `tests/<suite>/`; the six-phase protocol is already suite-agnostic except for hardcoded paths. Keep `/test-setup-awow` as an alias until the rename settles.

## 4. Phase 2 — the eval set, ranked by real usage

Resolve the "abstract base vs actual data" tension explicitly, mirroring what `linear` already does:

- **Tier A (awow template): structure & gate regression.** Synthetic fixtures committed in `tests/`. Asserts contracts hold: frontmatter fields present, approval gates honoured (no writes before explicit approve in the script), outputs land in the right place, mining-policy selectivity respected. Cheap, deterministic-heavy, runs anywhere.
- **Tier B (linear instance): answer/output quality.** Lives in `linear/evals/`, anchored on real data, following the proven **kb-agent pattern**: versioned `dataset.vN.yaml`, fixed versioned rubric, four-dimensional judge (correctness / groundedness / completeness / calibration), deterministic scorer owning fabrication + path checks, `gate.json` derived from a baseline run, append-only `trend.jsonl`, weekly cloud routine. awow ships the *harness and pattern*; the instance ships the *numbers*.

**Priority = usage × churn** (usage ranking, Casper, 2026-07: daily-digest > setup-awow > process-transcript incl. subparts > process-workitem (aspirational) > kb-synthesize > kb-mine; never used: project-manager, cross-team-view, awow-add/awow-reset). Never-used commands get **zero eval budget** — see §6 for what happens to them instead.

### 4.1 `tests/daily-digest/` — first new suite

The synthetic snapshot is the fixture: a committed `activity/2026-07-01.json` (the `activity-collection.md` shape) with **planted traps** whose presence/absence is mechanically checkable — a marker string inside a private-team item, a person absent from `members.md`, a chat message with no project mapping.

| Scenario | Tests |
|---|---|
| `busy-day` | Full snapshot → digest covers all planted significant items (post: `file-contains` each planted item ID) |
| `quiet-day` | Near-empty snapshot → short honest digest, no padding or invented activity |
| `private-team-gate` | Planted private marker never appears in output (post: `file-absent-content`) |
| `missing-source` | Chat source absent from snapshot → digest flags the gap instead of fabricating |
| `unknown-name` | Person not in `members.md` → handled per convention, not silently normalised |

Judged (blind subagent): the four dimensions, fabrication as hard gate. Tier B: the ~24 real digests (2026-02 → 2026-05) anchor a judged quality eval with reference digests.

### 4.2 `tests/setup-awow/` — exists; harden, then extend

Phase 1 (§3) covers the hardening. The walkthrough scenario stops at Step 3 — Steps 4–10 (including Step 6 KB wiring and Step 9 skills review, invariant 10) are uncovered; add scenarios for them after hardening lands.

### 4.3 `tests/process-transcript/` — router + subparts as one suite

Fixtures are short synthetic `.vtt` files with **planted facts** (named decisions, action items, a coaching moment) — the planted-defect technique from superpowers-evals: `pre()` asserts the plant, `post()` asserts it surfaced in the right artifact.

| Scenario | Tests |
|---|---|
| `single-design-call` | Whole transcript routes to `/solution-design-flow`; planted decision IDs land in the design artifact |
| `mixed-call` | Segmentation splits design + coaching + status correctly; each segment reaches its specialist |
| `coaching-segment` | `/coaching-review` path: planted teaching moment surfaced, feedback grounded in transcript lines |
| `smalltalk-only` | Router declares nothing to process — does not invent segments |
| `retro-transcript` | Router behaviour on a retro (today: hand-off to `/process-retro`; after §6.2 lands: routes it) |
| `gate-approval` | No board/KB write occurs before the scripted `approve` line |

Tier B: `linear/transcripts/calldanone.vtt` + its complete processed set is a ready-made golden pair; Boskalis calls add breadth.

### 4.4 `tests/process-workitem/` — spec-first, encodes the board-as-feed flex

Today the board *traces* activity; the target is the board as the *feed* — the command starts by pulling the work item, and board state transitions are the source of truth for progress. **Write this suite against the target behaviour, then rework the prompt until it passes** — evals as the spec for the change, not a regression net over behaviour we intend to replace.

Board sandbox problem, solved with a shim (the `command-runner` seam idea from superpowers-evals): the fixture puts a fake `gh` (or board-CLI stub) first on `PATH` that serves issue JSON from `fixtures/board/` and appends every invocation to `calls.jsonl`. `post()` then asserts deterministically from the call log: item was **read before any write**, status transitions happen in archetype order, no write before scripted approval, PR/commit references the item ID.

| Scenario | Tests |
|---|---|
| `feature-item` | Feature archetype end-to-end against a well-formed item |
| `bugfix-item` | Bugfix archetype (repro-first ordering per `_workitem-archetypes/bugfix.md`) |
| `spike-item` | Spike archetype: timeboxed output, findings land back on the item |
| `underspecified-item` | Item missing required fields → command pushes back, does not proceed (the `expects_clarification` pattern from linear's finops eval) |

Item content should be **elicited** (drafted via `/refinement-prep`), not hand-authored — hand-written idealised inputs overstate the baseline.

### 4.5 `tests/kb-pipeline/` — `/kb-mine` → `/kb-synthesize`

Fixture: the same synthetic activity snapshot as 4.1 (shared gather, shared fixture) plus a seeded `context/kb-inbox/`.

| Scenario | Tests |
|---|---|
| `mine-yield-cap` | Candidate count respects `mining-policy.md` selectivity; categories honoured |
| `mine-frontmatter` | Every candidate carries complete frontmatter (`source/source_ref/date/suggested_target`) |
| `synth-dedup` | Candidate already covered by an existing KB note → linked/skipped, not duplicated |
| `synth-gate` | Nothing promoted before scripted approval; `_synthesis-log.md` appended either way |
| `junk-inbox` | Low-value candidates → drain declines to promote, says why |

Tier B: linear's 20 real inbox candidates, the 116 KB `_synthesis-log.md`, and the ~500-note KB anchor a mining-yield and synthesis-judgement eval.

## 5. Phase 3 — prompt improvements the evals unlock

The point of the baseline: **once an invariant is captured in a check + rubric line, the defensive prose defending it inside the command can shrink.** Tests enable refactoring — for prompts too.

- `process-transcript` (459 lines) and `process-retro` (347) carry heavy anti-drift scaffolding; after suite #3 exists, trim both against a green run.
- When editing any command, apply belt-and-braces: each load-bearing MUST maps to a numbered invariant → rubric question → (if mechanical) a `post()` check. New MUSTs without an invariant number get flagged by `validate-evals.py`.
- Adopt the four-dimensional-rubric house pattern (already codified in `linear`'s KB as `prompt-evaluation-rubric-four-dimensional.md`) for every Tier B eval: dimensions stable, thresholds derived from baselines, never guessed.

## 6. Phase 4 — command-surface cleanup

Adopter evidence: `linear` dropped `awow-reset`, `board-skill`, `daily-routine`, `kb-mine`, `test-setup-awow` from its command set, kept `kb-synthesize`, and moved scheduled work to `prompts/*-cloud.md` routines. That is real usage signal, not taste.

1. **Delete the two unimplemented stubs** — `board-skill.md` (13 lines, "v0.2") and `cross-team-view.md` (14 lines, "v0.3"). Park intent in `meta/backlog.md`. `board-skill`'s stated pain (commits↔issues never link) is already covered by the board-linkage convention in `.agents/AGENTS.md` plus the `session-correlation` skill — re-justify before reintroducing. *Safe now.*
2. **Fold `process-retro` into the `process-transcript` router** as a segment route (or extract the shared gated-pipeline scaffolding). Both are "gated pipeline for X transcripts"; retro sitting outside the router contradicts `guide-transcript-router.html` and duplicates ~800 combined lines of gating. *Land after suite #3 exists so the consolidation is regression-guarded.*
3. **Slim the KB entry-point surface.** Three commands (`/kb-mine`, `/kb-synthesize`, `/daily-routine`) front two contracts (`mining.md`, `synthesis.md`). Keep the contracts and `/kb-synthesize` (the human gate); demote `/kb-mine` to the path `/daily-routine` takes (linear kept neither interactively — mining went to a cloud routine). *Land after suite #1 exists.*
4. **Trim neighbour-pointing prose** in the delivery chain (`solution-design-flow` → `project-plan` → `project-manager`): each spends significant lines re-describing its neighbours' contracts, so every contract change ripples through three files. Point at the contract file once instead. *Low risk, any time.*
5. **Park `project-manager`** — never used by the maintainer despite being the largest standardise command (172 lines). Park with a revisit condition ("a second team adopts the delivery chain") rather than delete: linear kept it, so it has one nominal adopter. Zero eval budget until unparked.
6. **`awow-add` / `awow-reset`** — never used interactively, but they are phase machinery (`/setup-awow` and the maintainer loop depend on them), not workflow prompts. Keep, no evals, exclude from any "prompt count" worries.

## 7. Sequencing

Phase 1 (harden the harness) → **4.1 daily-digest** (most-used prompt, first new suite; also produces the shared snapshot fixture) → cleanup items 1+4+5 in parallel → **4.3 process-transcript** → cleanup item 2 (retro fold-in, now regression-guarded) → **4.5 kb-pipeline** (reuses the 4.1 fixture) → cleanup item 3 → **4.4 process-workitem** (spec-first, lands together with the board-as-feed prompt rework) → Phase 3 trims → extend 4.2 setup-awow past Step 3.

The first concrete PR: `checks.sh` + verdict precedence + blind-judge subagent + `validate-evals.py` for the existing eight setup-awow scenarios — pure hardening, no new coverage, proves the pattern before scaling it. The second PR: the daily-digest suite.
