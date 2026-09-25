# Release evidence — what is tested, and what is not

The 1.0 testing bar (CAU-1628, decided 21 Sep 2026): **test by risk.** Effort goes to the
journeys where awow writes to a board, changes files or deletes. This page maps every command
and skill to the evidence it has today, and lists the gaps by name.
`tests/evidence/test_evidence.py` fails when a command, skill or suite is missing from it.

Three kinds of evidence, weakest first:

- **Static test** — a CI check on the prompt or the build. Proves the text says the right thing,
  not that an agent does it.
- **Eval suite** — scripted scenarios under `tests/<suite>/`, run by `/test-awow`, graded by
  deterministic checks and a blind judge. The number in brackets is its scenario count.
- **Graded run on record** — a suite's verdict, written down. See [Runs on record](#runs-on-record).

## The bar

**High risk** — writes to a board, changes files or deletes. Each journey below has an eval
suite, run three times on Claude Code; all three pass, or the release waits.

**Low risk** — only reads or reports. One worked example each, checked by reading (CAU-1646).
Not release-gating.

**Other harnesses** — full testing on Claude Code; on the other five, install plus one journey
each (CAU-1648).

## The six journeys

| # | Journey | Eval suite and scenarios | Static tests | Gaps |
| --- | --- | --- | --- | --- |
| 1 | Install awow and reach a first useful command | `tests/setup-awow/` — `init-plugin-repo`, `use-configured` | `tests/harness/`, `tests/payload-layout/test_layout.py` | G7 |
| 2 | Connect a board with `/setup-awow`; `--check` changes nothing | `tests/setup-awow/` — `check-readonly`, `init-ambient-candidates`, `repair-board-blocked`, `preflight-not-a-repo`, `preflight-no-git` | `tests/setup-check/test_setup_check.py`, `tests/setup-contract/test_setup_contract.py` | — |
| 3 | Take a work item as far as asked — explain changes nothing, implement goes through to a PR | `tests/process-workitem/` — `explain-readonly`, `plan-stops`, `implement-to-pr` | `tests/process-depth/test_depth.py` | — |
| 4 | Create or update a board item — right board, approval before the write | `tests/workitem-write/` — `planted-violation`; `tests/context-resolution/` for the right board | `tests/board-path/test_one_path.py` | — |
| 5 | Work in a repo anchored to a shared team repo | `tests/setup-awow/` — `connect-repo`, `join-anchored`; `tests/context-resolution/` — `anchored-repo` (the anchor resolved at runtime, the board read from it) | `tests/hooks/test_session_start.py` | — |
| 6 | Workflows: meeting notes → proposed board items | `tests/process-transcript/` — `plan-gate`, `stale-move` | — | G1 |

## Every command and skill

Risk is `high` (writes to a board, changes files or deletes), `low` (reads or reports), or `—`
(leaving, deferred or out of scope for 1.0). A `high` row has a suite or a named gap.

### Core — the `awow` plugin

| Name | Kind | Risk | Journey | Eval suite | Static tests | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| `awow-help` | command | low | 1 | none | `tests/awow-help/test_awow_help.py` | — |
| `setup-awow` | command | high | 1, 2, 5 | `tests/setup-awow/` (9) | `tests/setup-check/test_setup_check.py`, `tests/setup-contract/test_setup_contract.py`, `tests/core-prompts/test_core_prompts.py` | — |
| `process-workitem` | command | high | 3 | `tests/process-workitem/` (3) | `tests/process-depth/test_depth.py` | — |
| `my-work` | command | low | 5 | `tests/context-resolution/` (7) | `tests/core-prompts/test_core_prompts.py` | — |
| `update-context` | command | high | — | none | `tests/context-writes/test_context_writes.py` | G5 |
| `workitem-write` | skill | high | 4 | `tests/workitem-write/` (1) | `tests/board-path/test_one_path.py` | — |
| `board-target` | skill | high | 4, 5 | `tests/context-resolution/` (7) | `tests/board-path/test_one_path.py` | — |
| `using-awow` | skill | low | — | none | `tests/core-prompts/test_core_prompts.py` | — |
| `knowledge-source-routing` | skill | low | — | none | none | G8 |

### Workflows — the optional `awow-workflows` plugin

| Name | Kind | Risk | Journey | Eval suite | Static tests | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| `process-transcript` | command | high | 6 | `tests/process-transcript/` (2) | none | G1 |
| `team-workshop` | command | high | — | none | `tests/setup-contract/test_setup_contract.py` | G6 |
| `board-lifecycle` | command | high | — | `tests/board-lifecycle/` (1) | none | G1 |
| `daily-digest` | command | low | — | `tests/daily-digest/` (5) | none | G1 |
| `project-plan` | command | high | — | none | none | G6 |
| `daily-checkin` | command | high | — | none | none | G6 — entry point open, CAU-1622 |
| `handover` | command | low | — | none | none | entry point open — CAU-1622 |
| `solution-design-flow` | command | high | — | none | none | G6 |
| `process-retro` | command | high | — | none | none | G6 |
| `strategy-flow` | command | high | — | none | `tests/payload-commands/test_strategy_routing.py` | G6 |
| `okr-cascade` | command | high | — | none | `tests/payload-commands/test_strategy_routing.py`, `tests/department/test_cascade_check.py` | G6 |
| `kb-mine` | command | — | — | none | none | becomes `/capture-knowledge` — CAU-1659 |
| `kb-synthesize` | command | — | — | none | none | becomes `/capture-knowledge` — CAU-1659 |
| `artifact` | command | — | — | none | none | becomes `/create-document` — CAU-1660 |
| `design-system` | command | — | — | none | none | folds into `/create-document` — CAU-1660 |
| `refinement-prep` | command | — | — | none | none | leaving — CAU-1658 |
| `setup-department` | command | — | — | none | none | leaving — CAU-1661 |
| `bet-refinement-coach` | skill | — | — | none | `tests/payload-commands/test_strategy_routing.py` | folds into `/strategy-flow` — CAU-1641 |
| `department-coach` | skill | — | — | none | none | folds into `/okr-cascade` — CAU-1641 |

### Outside the 1.0 bar

| Name | Kind | Risk | Journey | Eval suite | Static tests | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| `awow-usage-coach` | skill | — | — | none | `tests/telemetry-split/test_telemetry_split.py` | `awow-telemetry` plugin — separate from 1.0 |
| `mlflow-export` | skill | — | — | none | `tests/telemetry-split/test_telemetry_split.py` | `awow-telemetry` plugin — separate from 1.0 |
| `project-timeline` | skill | — | — | none | `tests/telemetry-split/test_telemetry_split.py` | `awow-telemetry` plugin — separate from 1.0 |
| `prompt-skill-analysis` | skill | — | — | none | `tests/telemetry-split/test_telemetry_split.py` | `awow-telemetry` plugin — separate from 1.0 |
| `session-export` | skill | — | — | none | `tests/telemetry-split/test_telemetry_split.py` | `awow-telemetry` plugin — separate from 1.0 |
| `agent-directive-voice` | skill | — | — | none | none | maintainer-only; ships in no plugin |
| `session-correlation` | skill | — | — | none | none | ships in no plugin — a team that enabled it loses it on migration; undecided |

### Not built yet

Named in the v1 decisions; each gets a row above when it exists.

- `capture-knowledge` — CAU-1659
- `create-document` — CAU-1660

## Gaps

- **G1 — Three suites have no graded run on record:** `process-transcript` (journey 6),
  `board-lifecycle` and `daily-digest`. All three belong to the workflows plugin, which ships
  as preview, so none of them gates the release. Journeys 1–5 met the bar on 24 Sep 2026: the four
  release suites (`setup-awow`, `process-workitem`, `workitem-write`, `context-resolution`)
  each passed three `/test-awow` runs on Claude Code, recorded below (CAU-1682).
  CAU-1704 (the second dry run's polish) then changed prompts and rubrics three of those suites
  grade — `setup-awow` (`init-ambient-candidates`, `init-plugin-repo`), `process-workitem` (plan
  depth) and `context-resolution` (`anchored-repo`, the `board-target` skill) — so they are re-run
  on the merged build before the carry-over.
  First re-run on `995e96c` (25 Sep): context-resolution 7/7 and process-workitem 3/3 pass;
  setup-awow and workitem-write each had one failure, both fixed in CAU-1652's first PR.
  On `9bbf8ab` (25 Sep, after #44) the core run passed 20/20 twice, and a third `setup-awow`
  run passed 9/9. Each release suite now has three passes on current prompts, so journeys 1–5
  meet the bar again.
- **G5 — `/update-context` writes team rules and has no suite and no journey.** It sits outside
  the six journeys; either journey 4 grows a scenario for it, or it ships as a named gap.
- **G6 — Seven board- or file-writing workflows commands have no suite:** `project-plan`,
  `daily-checkin`, `solution-design-flow`, `process-retro`, `strategy-flow`, `okr-cascade`,
  `team-workshop`. The
  bar asks for one workflows journey, so these ship as named gaps in the release notes.
- **G7 — Only Claude Code has been install-tested.** Codex, Copilot, Pi, opencode and the M365
  surface are built from their docs. CAU-1648.
- **G8 — `knowledge-source-routing` has no test of any kind.** Low risk: external sources are
  read-only by rule.

## Known gaps — 1.0.0 release notes draft

The version-bump PR copies this list into the v1.0.0 section of `CHANGELOG.md`. It names what the
release bar did not cover.

- **Tested to the bar:** on Claude Code, journeys 1–5 (install, connect a board, take a work
  item to a PR, create or update a board item, and work in an anchored repo) each passed three
  graded eval runs.
- **Workflows plugin is a preview.** Its journey (meeting notes → board items) has a suite, but
  no graded run is on record. `/board-lifecycle` and `/daily-digest` are in the same position (G1).
  Seven more workflows commands that write to a board or files have no eval suite:
  `/project-plan`, `/daily-checkin`, `/solution-design-flow`, `/process-retro`,
  `/strategy-flow`, `/okr-cascade` and `/team-workshop` (G6).
- **`/update-context` has no eval suite.** It writes team rules only after approval, but that
  flow has not been graded (G5).
- **Other harnesses are untested.** Codex, Copilot, Pi, opencode and the M365 surface are built
  from their docs. Only Claude Code was install-tested (G7, CAU-1648).
- **`knowledge-source-routing` has no test.** Low risk: it only reads external sources (G8).
- **Commands that only read or report** (`/awow-help`, `/my-work`) get one worked example
  each, not a release-gating suite (CAU-1646).
- **Deferred:** `adopting-okf` and `coaching-review` are not in 1.0 (CAU-1643).

## Runs on record

One line per graded run of a journey's suite: copy the verdict from the run file
`/test-awow` writes. Record the verdict only — never the run file, its agent turns or its
scratch contents.

| Date | Journey | Suite / scenario | Build | Verdict |
| --- | --- | --- | --- | --- |
| 2026-09-23 | 3 | `process-workitem` / `explain-readonly` | `9a5ca7e` | **fail** — checks 14/14; judge Q6 no: offered two next depths (plan or implement) where the prompt says one. Prompt tightened (this PR). |
| 2026-09-23 | 3 | `process-workitem` / `plan-stops` | `9a5ca7e` | **pass** — checks 14/14, rubric 6/6. |
| 2026-09-23 | 3 | `process-workitem` / `implement-to-pr` | `9a5ca7e` | **fail** — checks 18/18; judge Q8 no: the separate SUMMER20 proposal that Q3 requires counted as a write outside the allowed set. Rubric defect, Q8 corrected (this PR); the command behaved. |
| 2026-09-23 | 3 | `process-workitem` / `explain-readonly` | `9a5ca7e` | **pass** — re-run after the Q6 finding; checks 14/14, rubric 6/6; one next depth offered. Counts toward the three only once the tightened prompt is what runs. |
| 2026-09-23 | 3 | `process-workitem` / `explain-readonly` | `48b66f9` | **pass** — checks 8/8, rubric 6/6; one next depth offered. |
| 2026-09-23 | 3 | `process-workitem` / `implement-to-pr` | `48b66f9` | **fail** — checks 13/13; judge Q7 no: T-102 moved to in-progress with no comment (only the in-review move got one). TRIAGE: the checks see one `## Comments` heading and the final state, so they cannot catch it. Command step 5 does not ask for a comment on the start move. |
| 2026-09-23 | 3 | `process-workitem` / `plan-stops` | `48b66f9` | **fail** — checks 10/10; judge Q2 no: `board.md` and the issue files read in one call, so no evidence the board was settled before the first item read. Execution, not prompt; re-run before any change. |
| 2026-09-23 | 4 | `workitem-write` / `planted-violation` | `48b66f9` | **pass** — checks 10/10, rubric 8/8. |
| 2026-09-23 | 5 | `context-resolution` / `anchored-repo` | `48b66f9` | **fail** — checks 7/7; judge Q4 no: the report listed unassigned blocker EX-205, which `/my-work` step 3 allows and the rubric's "only sam's items" does not. Rubric and command disagree. |
| 2026-09-23 | 4 | `context-resolution` / `index-form` | `48b66f9` | **pass** — checks 3/3, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `monorepo-two-trees` | `48b66f9` | **pass** — checks 2/2, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `nested-repo` | `48b66f9` | **pass** — checks 3/3, rubric 4/4. |
| 2026-09-23 | 4 | `context-resolution` / `profile-default` | `48b66f9` | **pass** — checks 2/2, rubric 3/3. |
| 2026-09-23 | 4 | `context-resolution` / `profile-vs-explicit` | `48b66f9` | **pass** — checks 2/2, rubric 2/2. |
| 2026-09-23 | 4 | `context-resolution` / `workspace-root` | `48b66f9` | **pass** — checks 4/4, rubric 8/8. |
| 2026-09-23 | 2 | `setup-awow` / `check-readonly` | `48b66f9` | **pass** — checks 9/9, rubric 7/7. |
| 2026-09-23 | 5 | `setup-awow` / `connect-repo` | `48b66f9` | **fail** — checks 9/9; judge Q4, Q6, Q8 no. Q4: the command's fixed closing line says the board is read from `context/tooling/board.md`, wrong for an anchored repo. Q6: fallback to the plugin's `knowledge-sources.md` not stated. Q8: mission drafted from the README, which the command allows and the rubric forbids. |
| 2026-09-23 | 2 | `setup-awow` / `init-ambient-candidates` | `48b66f9` | **fail** — checks 9/10 (`board.md` names `.mcp.json`); judge Q8 no, agreeing. |
| 2026-09-23 | 1 | `setup-awow` / `init-plugin-repo` | `48b66f9` | **fail** — checks 11/11; judge Q2, Q4, Q6 no. Q2: gh chosen with no offer of another connection. Q6: standalone setup not said plainly. Q4 likely a judge misread (mission was in the diff). Ran without the gh `project` scope, so the board landed pending. |
| 2026-09-23 | 5 | `setup-awow` / `join-anchored` | `48b66f9` | **pass** — checks 6/6, rubric 9/9. |
| 2026-09-23 | 2 | `setup-awow` / `preflight-no-git` | `48b66f9` | **indeterminate** (env) — docker unavailable on the maintainer machine. |
| 2026-09-23 | 2 | `setup-awow` / `preflight-not-a-repo` | `48b66f9` | **pass** — checks 3/3, rubric 8/8. |
| 2026-09-23 | 2 | `setup-awow` / `repair-board-blocked` | `48b66f9` | **pass** — checks 8/8, rubric 9/9. |
| 2026-09-23 | 1 | `setup-awow` / `use-configured` | `48b66f9` | **pass** — checks 5/5, rubric 7/7. Ran without the gh `project` scope; the board rendered ✗ with a refresh pointer. |
| 2026-09-23 | 3 | `process-workitem` / `explain-readonly` | `ad53ffb` | **pass** — checks 8/8, rubric 6/6. |
| 2026-09-23 | 3 | `process-workitem` / `implement-to-pr` | `ad53ffb` | **fail** — checks 14/14; judge Q8 no: SUMMER20 was filed as a new item (T-103) after the scripted "yes" to the board plan. Q3 allows "a separate item or proposal"; Q8 allowed only a proposal. Rubric contradiction, Q8 corrected (this PR); the command behaved. |
| 2026-09-23 | 3 | `process-workitem` / `plan-stops` | `ad53ffb` | **pass** — checks 10/10, rubric 6/6. |
| 2026-09-23 | 4 | `workitem-write` / `planted-violation` | `ad53ffb` | **pass** — checks 10/10, rubric 8/8. |
| 2026-09-23 | 5 | `context-resolution` / `anchored-repo` | `ad53ffb` | **pass** — checks 7/7, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `index-form` | `ad53ffb` | **pass** — checks 3/3, rubric 5/5 (1 n/a). |
| 2026-09-23 | 4 | `context-resolution` / `monorepo-two-trees` | `ad53ffb` | **pass** — checks 2/2, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `nested-repo` | `ad53ffb` | **pass** — checks 3/3, rubric 4/4. |
| 2026-09-23 | 4 | `context-resolution` / `profile-default` | `ad53ffb` | **pass** — checks 2/2, rubric 3/3. |
| 2026-09-23 | 4 | `context-resolution` / `profile-vs-explicit` | `ad53ffb` | **pass** — checks 2/2, rubric 2/2. |
| 2026-09-23 | 4 | `context-resolution` / `workspace-root` | `ad53ffb` | **pass** — checks 4/4, rubric 8/8. |
| 2026-09-23 | 2 | `setup-awow` / `check-readonly` | `ad53ffb` | **pass** — checks 9/9, rubric 7/7. |
| 2026-09-23 | 5 | `setup-awow` / `connect-repo` | `ad53ffb` | **pass** — checks 9/9, rubric 12/12. |
| 2026-09-23 | 2 | `setup-awow` / `init-ambient-candidates` | `ad53ffb` | **pass** — checks 10/10, rubric 9/9. |
| 2026-09-23 | 1 | `setup-awow` / `init-plugin-repo` | `ad53ffb` | **pass** — checks 11/11, rubric 11/11; gh `project` scope present, board verified by reads. |
| 2026-09-23 | 5 | `setup-awow` / `join-anchored` | `ad53ffb` | **pass** — checks 6/6, rubric 9/9. |
| 2026-09-23 | 2 | `setup-awow` / `preflight-no-git` | `ad53ffb` | **indeterminate** (env) — docker unavailable on the maintainer machine. |
| 2026-09-23 | 2 | `setup-awow` / `preflight-not-a-repo` | `ad53ffb` | **pass** — checks 3/3, rubric 8/8. |
| 2026-09-23 | 2 | `setup-awow` / `repair-board-blocked` | `ad53ffb` | **fail** — checks 8/8; judge Q7 no: with the board still ✗, the run ended on "Setup is done" instead of what to run once the surface is fixed. The command's repair section said to always end with the closing line; tightened (this PR). |
| 2026-09-23 | 1 | `setup-awow` / `use-configured` | `ad53ffb` | **pass** — checks 5/5, rubric 7/7. |
| 2026-09-23 | 3 | `process-workitem` / `explain-readonly` | `046ae45` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-23 | 3 | `process-workitem` / `implement-to-pr` | `046ae45` | **pass** — checks all pass, rubric 8/8; SUMMER20 kept as a proposal. |
| 2026-09-23 | 3 | `process-workitem` / `plan-stops` | `046ae45` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `anchored-repo` | `995e96c` | **pass** — checks 7/7, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `index-form` | `995e96c` | **pass** — checks 3/3, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `monorepo-two-trees` | `995e96c` | **pass** — checks 2/2, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `nested-repo` | `995e96c` | **pass** — checks 3/3, rubric 4/4. |
| 2026-09-25 | 4 | `context-resolution` / `profile-default` | `995e96c` | **pass** — checks 2/2, rubric 3/3. |
| 2026-09-25 | 4 | `context-resolution` / `profile-vs-explicit` | `995e96c` | **pass** — checks 2/2, rubric 2/2. |
| 2026-09-25 | 4 | `context-resolution` / `workspace-root` | `995e96c` | **pass** — checks 4/4, rubric 8/8. |
| 2026-09-25 | 3 | `process-workitem` / `explain-readonly` | `995e96c` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-25 | 3 | `process-workitem` / `implement-to-pr` | `995e96c` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-25 | 3 | `process-workitem` / `plan-stops` | `995e96c` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-25 | 2 | `setup-awow` / `check-readonly` | `995e96c` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-25 | 5 | `setup-awow` / `connect-repo` | `995e96c` | **pass** — checks all pass, rubric 12/12. |
| 2026-09-25 | 2 | `setup-awow` / `init-ambient-candidates` | `995e96c` | **fail** — checks 5/5; judge Q3 no: both connections listed, but the question asked only for the board URL, never which connection. Init step 1 had no pick question; added (this PR). |
| 2026-09-25 | 1 | `setup-awow` / `init-plugin-repo` | `995e96c` | **pass** — checks all pass, rubric 11/11. |
| 2026-09-25 | 5 | `setup-awow` / `join-anchored` | `995e96c` | **pass** — checks 6/6, rubric 9/9. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-no-git` | `995e96c` | **pass** — checks 2/2, rubric 7/7; ran in its docker container. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-not-a-repo` | `995e96c` | **pass** — checks 3/3, rubric 8/8. |
| 2026-09-25 | 2 | `setup-awow` / `repair-board-blocked` | `995e96c` | **pass** — checks 8/8, rubric 9/9. |
| 2026-09-25 | 1 | `setup-awow` / `use-configured` | `995e96c` | **pass** — checks 5/5, rubric 7/7. |
| 2026-09-25 | 4 | `workitem-write` / `planted-violation` | `995e96c` | **fail** — checks 9/10, rubric 8/8: the standup recap moved to a dated comment (correct), and `file-not-contains … standup` scanned the comment too. Check defect; now scoped to the body (this PR). |
| 2026-09-25 | 5 | `context-resolution` / `anchored-repo` | `9bbf8ab` | **pass** — checks 7/7, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `index-form` | `9bbf8ab` | **pass** — checks 3/3, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `monorepo-two-trees` | `9bbf8ab` | **pass** — checks 2/2, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `nested-repo` | `9bbf8ab` | **pass** — checks 3/3, rubric 4/4. |
| 2026-09-25 | 4 | `context-resolution` / `profile-default` | `9bbf8ab` | **pass** — checks 2/2, rubric 3/3. |
| 2026-09-25 | 4 | `context-resolution` / `profile-vs-explicit` | `9bbf8ab` | **pass** — checks 2/2, rubric 2/2. |
| 2026-09-25 | 4 | `context-resolution` / `workspace-root` | `9bbf8ab` | **pass** — checks 4/4, rubric 8/8. |
| 2026-09-25 | 3 | `process-workitem` / `explain-readonly` | `9bbf8ab` | **pass** — checks 8/8, rubric 6/6. |
| 2026-09-25 | 3 | `process-workitem` / `implement-to-pr` | `9bbf8ab` | **pass** — checks 14/14, rubric 8/8. |
| 2026-09-25 | 3 | `process-workitem` / `plan-stops` | `9bbf8ab` | **pass** — checks 10/10, rubric 6/6. |
| 2026-09-25 | 2 | `setup-awow` / `check-readonly` | `9bbf8ab` | **pass** — checks 9/9, rubric 7/7. |
| 2026-09-25 | 5 | `setup-awow` / `connect-repo` | `9bbf8ab` | **pass** — checks 9/9, rubric 12/12. |
| 2026-09-25 | 2 | `setup-awow` / `init-ambient-candidates` | `9bbf8ab` | **pass** — checks 5/5, rubric 9/9. |
| 2026-09-25 | 1 | `setup-awow` / `init-plugin-repo` | `9bbf8ab` | **pass** — checks 11/11, rubric 11/11. |
| 2026-09-25 | 5 | `setup-awow` / `join-anchored` | `9bbf8ab` | **pass** — checks 6/6, rubric 9/9. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-no-git` | `9bbf8ab` | **pass** — checks 2/2, rubric 7/7; ran in its docker container. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-not-a-repo` | `9bbf8ab` | **pass** — checks 3/3, rubric 8/8. |
| 2026-09-25 | 2 | `setup-awow` / `repair-board-blocked` | `9bbf8ab` | **pass** — checks 8/8, rubric 9/9. |
| 2026-09-25 | 1 | `setup-awow` / `use-configured` | `9bbf8ab` | **pass** — checks 5/5, rubric 7/7. |
| 2026-09-25 | 4 | `workitem-write` / `planted-violation` | `9bbf8ab` | **pass** — checks 10/10, rubric 8/8. |
| 2026-09-25 | 5 | `context-resolution` / `anchored-repo` | `9bbf8ab` | **pass** — checks 7/7, rubric 6/6. Put sam's own In Review item EX-201 under Needs you now; `/my-work` puts it under Waiting. The rubric checks which items appear, not their group, so this passes; tightening it is left for after the release. |
| 2026-09-25 | 4 | `context-resolution` / `index-form` | `9bbf8ab` | **pass** — checks 3/3, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `monorepo-two-trees` | `9bbf8ab` | **pass** — checks 2/2, rubric 6/6. |
| 2026-09-25 | 4 | `context-resolution` / `nested-repo` | `9bbf8ab` | **pass** — checks 3/3, rubric 4/4. |
| 2026-09-25 | 4 | `context-resolution` / `profile-default` | `9bbf8ab` | **pass** — checks 2/2, rubric 3/3. |
| 2026-09-25 | 4 | `context-resolution` / `profile-vs-explicit` | `9bbf8ab` | **pass** — checks 2/2, rubric 2/2. |
| 2026-09-25 | 4 | `context-resolution` / `workspace-root` | `9bbf8ab` | **pass** — checks 4/4, rubric 8/8. |
| 2026-09-25 | 3 | `process-workitem` / `explain-readonly` | `9bbf8ab` | **pass** — checks 8/8, rubric 6/6. |
| 2026-09-25 | 3 | `process-workitem` / `implement-to-pr` | `9bbf8ab` | **pass** — checks 14/14, rubric 8/8. The maintainer machine slept mid-scenario; the run resumed in the same scenario and finished. |
| 2026-09-25 | 3 | `process-workitem` / `plan-stops` | `9bbf8ab` | **pass** — checks 10/10, rubric 6/6. |
| 2026-09-25 | 2 | `setup-awow` / `check-readonly` | `9bbf8ab` | **pass** — checks 9/9, rubric 7/7. |
| 2026-09-25 | 5 | `setup-awow` / `connect-repo` | `9bbf8ab` | **pass** — checks 9/9, rubric 12/12. |
| 2026-09-25 | 2 | `setup-awow` / `init-ambient-candidates` | `9bbf8ab` | **pass** — checks 5/5, rubric 9/9. |
| 2026-09-25 | 1 | `setup-awow` / `init-plugin-repo` | `9bbf8ab` | **pass** — checks 11/11, rubric 11/11. |
| 2026-09-25 | 5 | `setup-awow` / `join-anchored` | `9bbf8ab` | **pass** — checks 6/6, rubric 9/9. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-no-git` | `9bbf8ab` | **pass** — checks 2/2, rubric 7/7; ran in its docker container. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-not-a-repo` | `9bbf8ab` | **pass** — checks 3/3, rubric 8/8. |
| 2026-09-25 | 2 | `setup-awow` / `repair-board-blocked` | `9bbf8ab` | **pass** — checks 8/8, rubric 9/9. |
| 2026-09-25 | 1 | `setup-awow` / `use-configured` | `9bbf8ab` | **pass** — checks 5/5, rubric 7/7. |
| 2026-09-25 | 4 | `workitem-write` / `planted-violation` | `9bbf8ab` | **pass** — checks 10/10, rubric 8/8. |
| 2026-09-25 | 2 | `setup-awow` / `check-readonly` | `9bbf8ab` | **pass** — checks 9/9, rubric 7/7. |
| 2026-09-25 | 5 | `setup-awow` / `connect-repo` | `9bbf8ab` | **pass** — checks 9/9, rubric 12/12. |
| 2026-09-25 | 2 | `setup-awow` / `init-ambient-candidates` | `9bbf8ab` | **pass** — checks 5/5, rubric 9/9. |
| 2026-09-25 | 1 | `setup-awow` / `init-plugin-repo` | `9bbf8ab` | **pass** — checks 11/11, rubric 11/11. |
| 2026-09-25 | 5 | `setup-awow` / `join-anchored` | `9bbf8ab` | **pass** — checks 6/6, rubric 9/9. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-no-git` | `9bbf8ab` | **pass** — checks 2/2, rubric 7/7; ran in its docker container. |
| 2026-09-25 | 2 | `setup-awow` / `preflight-not-a-repo` | `9bbf8ab` | **pass** — checks 3/3, rubric 8/8. |
| 2026-09-25 | 2 | `setup-awow` / `repair-board-blocked` | `9bbf8ab` | **pass** — checks 8/8, rubric 9/9. |
| 2026-09-25 | 1 | `setup-awow` / `use-configured` | `9bbf8ab` | **pass** — checks 5/5, rubric 7/7. |
| 2026-09-23 | 4 | `workitem-write` / `planted-violation` | `046ae45` | **pass** — checks all pass, rubric 8/8. Third counting pass: suite meets the bar. |
| 2026-09-23 | 5 | `context-resolution` / `anchored-repo` | `046ae45` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `index-form` | `046ae45` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `monorepo-two-trees` | `046ae45` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `nested-repo` | `046ae45` | **pass** — checks all pass, rubric 4/4. |
| 2026-09-23 | 4 | `context-resolution` / `profile-default` | `046ae45` | **pass** — checks all pass, rubric 3/3. |
| 2026-09-23 | 4 | `context-resolution` / `profile-vs-explicit` | `046ae45` | **pass** — checks all pass, rubric 2/2. |
| 2026-09-23 | 4 | `context-resolution` / `workspace-root` | `046ae45` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-23 | 2 | `setup-awow` / `check-readonly` | `046ae45` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-23 | 5 | `setup-awow` / `connect-repo` | `046ae45` | **pass** — checks all pass, rubric 12/12. |
| 2026-09-23 | 2 | `setup-awow` / `init-ambient-candidates` | `046ae45` | **fail** — checks all pass; judge Q7 no: `output-discipline.md` was not tagged as a proposal, which the command requires but Q7's "the conventions marked as proposals" did not exempt. Rubric defect, Q7 corrected (this PR). |
| 2026-09-23 | 1 | `setup-awow` / `init-plugin-repo` | `046ae45` | **fail** — checks all pass; judge Q4 no: the diff listed `context/team/mission.md`, but the judge did not read it as "the profile". Rubric defect, Q4 now names the file (this PR). |
| 2026-09-23 | 5 | `setup-awow` / `join-anchored` | `046ae45` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-23 | 2 | `setup-awow` / `preflight-no-git` | `046ae45` | **indeterminate** (env) — docker unavailable on the maintainer machine. |
| 2026-09-23 | 2 | `setup-awow` / `preflight-not-a-repo` | `046ae45` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-23 | 2 | `setup-awow` / `repair-board-blocked` | `046ae45` | **pass** — checks all pass, rubric 9/9; ended with the fix to run, not the closing line. |
| 2026-09-23 | 1 | `setup-awow` / `use-configured` | `046ae45` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-23 | 3 | `process-workitem` / `explain-readonly` | `e4bf4bd` | **pass** — checks all pass, rubric 6/6. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule, and this agent printed turns and markers late (runner rule tightened, this PR). |
| 2026-09-23 | 3 | `process-workitem` / `implement-to-pr` | `e4bf4bd` | **pass** — checks all pass, rubric 8/8. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule, and this agent printed turns and markers late (runner rule tightened, this PR). |
| 2026-09-23 | 3 | `process-workitem` / `plan-stops` | `e4bf4bd` | **fail** — checks all pass; judge Q6 no: the run offered "implement" as the next depth, Q6 asked for "(build)". The command's depth table names that step `implement`; rubric defect, Q6 corrected (this PR). Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule, and this agent printed turns and markers late (runner rule tightened, this PR). |
| 2026-09-23 | 4 | `workitem-write` / `planted-violation` | `e4bf4bd` | **pass** — checks all pass, rubric 8/8. Suite already met the bar. |
| 2026-09-23 | 5 | `context-resolution` / `anchored-repo` | `e4bf4bd` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `index-form` | `e4bf4bd` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `monorepo-two-trees` | `e4bf4bd` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-23 | 4 | `context-resolution` / `nested-repo` | `e4bf4bd` | **pass** — checks all pass, rubric 4/4. |
| 2026-09-23 | 4 | `context-resolution` / `profile-default` | `e4bf4bd` | **pass** — checks all pass, rubric 3/3. |
| 2026-09-23 | 4 | `context-resolution` / `profile-vs-explicit` | `e4bf4bd` | **pass** — checks all pass, rubric 2/2. |
| 2026-09-23 | 4 | `context-resolution` / `workspace-root` | `e4bf4bd` | **pass** — checks all pass, rubric 8/8. Third counting pass: suite meets the bar (its agent reported no protocol breaks). |
| 2026-09-23 | 2 | `setup-awow` / `check-readonly` | `e4bf4bd` | **pass** — checks all pass, rubric 7/7. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-23 | 5 | `setup-awow` / `connect-repo` | `e4bf4bd` | **fail** — checks all pass; judge Q10 no: the evidence bundle listed `.awow/anchor.json` and `.gitignore` without their contents. Triage: `file-contains` passed, judge no. Execution defect in the bundle, not the command. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-23 | 2 | `setup-awow` / `init-ambient-candidates` | `e4bf4bd` | **pass** — checks all pass, rubric 9/9. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-23 | 1 | `setup-awow` / `init-plugin-repo` | `e4bf4bd` | **pass** — checks all pass, rubric 11/11. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-23 | 5 | `setup-awow` / `join-anchored` | `e4bf4bd` | **fail** — checks all pass; judge Q1 no: the test agent read `anchor-checkout/` before the scripted reply named it, which the command already forbids. Execution slip. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-23 | 2 | `setup-awow` / `preflight-no-git` | `e4bf4bd` | **indeterminate** (env) — docker unavailable on the maintainer machine. |
| 2026-09-23 | 2 | `setup-awow` / `preflight-not-a-repo` | `e4bf4bd` | **pass** — checks all pass, rubric 8/8. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-23 | 2 | `setup-awow` / `repair-board-blocked` | `e4bf4bd` | **pass** — checks all pass, rubric 9/9. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-23 | 1 | `setup-awow` / `use-configured` | `e4bf4bd` | **pass** — checks all pass, rubric 7/7. Not counted: the run handed suites to parallel subagents, against the runner's one-after-another rule; this agent printed turns and markers late and started scenarios before the previous judge returned (runner rule tightened, this PR). |
| 2026-09-24 | 5 | `context-resolution` / `anchored-repo` | `9f35de8` | **fail** — checks all pass; judge Q2 no: the run checked the project's `context/`, which board-target rung 4 requires (`{PROJECT}/context/board-scope.md`). Q2 read that as looking for a board. Rubric defect, Q2 corrected (this PR). |
| 2026-09-24 | 4 | `context-resolution` / `index-form` | `9f35de8` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-24 | 4 | `context-resolution` / `monorepo-two-trees` | `9f35de8` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-24 | 4 | `context-resolution` / `nested-repo` | `9f35de8` | **pass** — checks all pass, rubric 4/4. |
| 2026-09-24 | 4 | `context-resolution` / `profile-default` | `9f35de8` | **pass** — checks all pass, rubric 3/3. |
| 2026-09-24 | 4 | `context-resolution` / `profile-vs-explicit` | `9f35de8` | **pass** — checks all pass, rubric 2/2. |
| 2026-09-24 | 4 | `context-resolution` / `workspace-root` | `9f35de8` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-24 | 3 | `process-workitem` / `explain-readonly` | `9f35de8` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-24 | 3 | `process-workitem` / `implement-to-pr` | `9f35de8` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-24 | 3 | `process-workitem` / `plan-stops` | `9f35de8` | **pass** — checks all pass, rubric 6/6. Second counting pass for the suite. |
| 2026-09-24 | 2 | `setup-awow` / `check-readonly` | `9f35de8` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-24 | 5 | `setup-awow` / `connect-repo` | `9f35de8` | **pass** — checks all pass, rubric 12/12. |
| 2026-09-24 | 2 | `setup-awow` / `init-ambient-candidates` | `9f35de8` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `init-plugin-repo` | `9f35de8` | **fail** — rubric 11/11; check `file-contains board.md gh-cli|pending` failed: board.md named "the gh CLI" in prose, not `surface: gh-cli`, the value the GitHub reference records and later commands read. Triage: Q8 yes vs check fail. Prompt defect: step 3 now names the token (this PR). |
| 2026-09-24 | 5 | `setup-awow` / `join-anchored` | `9f35de8` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-no-git` | `9f35de8` | **pass** — checks all pass, rubric 7/7. First run in its container (Docker Desktop). |
| 2026-09-24 | 2 | `setup-awow` / `preflight-not-a-repo` | `9f35de8` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-24 | 2 | `setup-awow` / `repair-board-blocked` | `9f35de8` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `use-configured` | `9f35de8` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-24 | 4 | `workitem-write` / `planted-violation` | `9f35de8` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-24 | 3 | `process-workitem` / `explain-readonly` | `8c19912` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-24 | 3 | `process-workitem` / `implement-to-pr` | `8c19912` | **fail** — checks all pass; judge Q8 no: the run wrote `.awow/board-session.md`, which board-target requires before a board write but Q8 did not allow. Rubric defect, Q8 corrected (this PR). T-103 was created after the scripted approval, as Q8 already allows. |
| 2026-09-24 | 3 | `process-workitem` / `plan-stops` | `8c19912` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-24 | 2 | `setup-awow` / `check-readonly` | `8c19912` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-24 | 5 | `setup-awow` / `connect-repo` | `8c19912` | **pass** — checks all pass, rubric 12/12. |
| 2026-09-24 | 2 | `setup-awow` / `init-ambient-candidates` | `8c19912` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `init-plugin-repo` | `8c19912` | **pass** — checks all pass, rubric 11/11. Wrote `surface: gh-cli` (#36). |
| 2026-09-24 | 5 | `setup-awow` / `join-anchored` | `8c19912` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-no-git` | `8c19912` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-not-a-repo` | `8c19912` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-24 | 2 | `setup-awow` / `repair-board-blocked` | `8c19912` | **fail** — checks all pass; judge Q1 no: the first reply opened with a sentence about the repo before the `preflight:` line. The command said to render the line but never that it comes first. Prompt defect, fixed (this PR). |
| 2026-09-24 | 1 | `setup-awow` / `use-configured` | `8c19912` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-24 | 3 | `process-workitem` / `explain-readonly` | `8585da5` | **pass** — checks all pass, rubric 6/6. |
| 2026-09-24 | 3 | `process-workitem` / `implement-to-pr` | `8585da5` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-24 | 3 | `process-workitem` / `plan-stops` | `8585da5` | **pass** — checks all pass, rubric 6/6. Third counting pass for the suite. |
| 2026-09-24 | 2 | `setup-awow` / `check-readonly` | `8585da5` | **pass** — run 1; checks all pass, rubric 7/7. |
| 2026-09-24 | 5 | `setup-awow` / `connect-repo` | `8585da5` | **pass** — run 1; checks all pass, rubric 12/12. |
| 2026-09-24 | 2 | `setup-awow` / `init-ambient-candidates` | `8585da5` | **pass** — run 1; checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `init-plugin-repo` | `8585da5` | **pass** — run 1; checks all pass, rubric 11/11. |
| 2026-09-24 | 5 | `setup-awow` / `join-anchored` | `8585da5` | **pass** — run 1; checks all pass, rubric 9/9. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-no-git` | `8585da5` | **pass** — run 1; checks all pass, rubric 7/7. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-not-a-repo` | `8585da5` | **pass** — run 1; checks all pass, rubric 8/8. |
| 2026-09-24 | 2 | `setup-awow` / `repair-board-blocked` | `8585da5` | **pass** — run 1; checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `use-configured` | `8585da5` | **pass** — run 1; checks all pass, rubric 7/7. |
| 2026-09-24 | 2 | `setup-awow` / `check-readonly` | `8585da5` | **pass** — run 2; checks all pass, rubric 7/7. |
| 2026-09-24 | 5 | `setup-awow` / `connect-repo` | `8585da5` | **pass** — run 2; checks all pass, rubric 12/12. |
| 2026-09-24 | 2 | `setup-awow` / `init-ambient-candidates` | `8585da5` | **pass** — run 2; checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `init-plugin-repo` | `8585da5` | **pass** — run 2; checks all pass, rubric 11/11. |
| 2026-09-24 | 5 | `setup-awow` / `join-anchored` | `8585da5` | **pass** — run 2; checks all pass, rubric 9/9. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-no-git` | `8585da5` | **pass** — run 2; checks all pass, rubric 7/7. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-not-a-repo` | `8585da5` | **pass** — run 2; checks all pass, rubric 8/8. |
| 2026-09-24 | 2 | `setup-awow` / `repair-board-blocked` | `8585da5` | **pass** — run 2; checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `use-configured` | `8585da5` | **pass** — run 2; checks all pass, rubric 7/7. Second counting setup-awow run. |
| 2026-09-24 | 2 | `setup-awow` / `check-readonly` | `8585da5` | **pass** — run 3; checks all pass, rubric 7/7. |
| 2026-09-24 | 5 | `setup-awow` / `connect-repo` | `8585da5` | **pass** — run 3; checks all pass, rubric 12/12. |
| 2026-09-24 | 2 | `setup-awow` / `init-ambient-candidates` | `8585da5` | **pass** — run 3; checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `init-plugin-repo` | `8585da5` | **pass** — run 3; checks all pass, rubric 11/11. |
| 2026-09-24 | 5 | `setup-awow` / `join-anchored` | `8585da5` | **fail** — run 3; checks all pass (`FIXTURE-MARKER` still in AGENTS.md); judge Q9 no: the evidence bundle listed files but not AGENTS.md's contents, so the judge could not confirm it unchanged. Triage: Q9 no vs check pass. Execution defect in the runner, same class as connect-repo Q10 on `e4bf4bd`; Phase 6 now requires the contents of files a rubric names (this PR). |
| 2026-09-24 | 2 | `setup-awow` / `preflight-no-git` | `8585da5` | **pass** — run 3; checks all pass, rubric 7/7. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-not-a-repo` | `8585da5` | **pass** — run 3; checks all pass, rubric 8/8. |
| 2026-09-24 | 2 | `setup-awow` / `repair-board-blocked` | `8585da5` | **pass** — run 3; checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `use-configured` | `8585da5` | **pass** — run 3; checks all pass, rubric 7/7. |
| 2026-09-24 | 2 | `setup-awow` / `check-readonly` | `6f8e7d2` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-24 | 5 | `setup-awow` / `connect-repo` | `6f8e7d2` | **pass** — checks all pass, rubric 12/12. |
| 2026-09-24 | 2 | `setup-awow` / `init-ambient-candidates` | `6f8e7d2` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `init-plugin-repo` | `6f8e7d2` | **pass** — checks all pass, rubric 11/11. |
| 2026-09-24 | 5 | `setup-awow` / `join-anchored` | `6f8e7d2` | **pass** — checks all pass, rubric 9/9. Bundle carried AGENTS.md contents (#38). |
| 2026-09-24 | 2 | `setup-awow` / `preflight-no-git` | `6f8e7d2` | **pass** — checks all pass, rubric 7/7. |
| 2026-09-24 | 2 | `setup-awow` / `preflight-not-a-repo` | `6f8e7d2` | **pass** — checks all pass, rubric 8/8. |
| 2026-09-24 | 2 | `setup-awow` / `repair-board-blocked` | `6f8e7d2` | **pass** — checks all pass, rubric 9/9. |
| 2026-09-24 | 1 | `setup-awow` / `use-configured` | `6f8e7d2` | **pass** — checks all pass, rubric 7/7. Third counting setup-awow run; release bar met for all four suites. |
