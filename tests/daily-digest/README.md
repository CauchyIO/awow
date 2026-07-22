# tests/daily-digest — regression suite for `/daily-digest`

Maintainer-only. Adopters who templated this repo can delete this directory.

**Principle.** Same as the suite layer ([`../README.md`](../README.md)): frozen, standalone fixtures; two witnesses; `pass` / `fail` / `indeterminate`. The digest-specific twist is that `/daily-digest` keys everything off *today*, so each fixture ships its activity snapshot frozen at `2026-07-01` and a setup hook (`setup/<scenario>.sh`) re-dates it to the run day before the `pre()` gate fires. Because the snapshot exists, the reuse check in `context/tooling/activity-collection.md` short-circuits collection — no live board, code, or chat surface is touched, and the fixture's `context/tooling/board.md` is a frozen sample, not a real board. Every scenario answers `stop` at the Phase 4 review gate: the scratch workspace has no git remote, and the assertion surface is the digest file on disk, not a PR.

The **private-team gate is out of scope here**: the shared gate is applied at collection time (see `activity-collection.md`), before the snapshot exists, so it belongs to a future collection-step suite. What this suite plants instead is traps whose leakage is mechanically checkable from the digest file.

## Invariants

| # | Invariant | Source (in `.agents/commands/daily-digest.md`) |
|---|---|---|
| 1 | Read-only against sources: no board/codebase/external mutation; no branch, commit, or PR before the Phase 4 gate | header, Phase 4, Behavioral boundaries |
| 2 | Reuse `activity/YYYY-MM-DD.json` when present; never re-query sources | Phase 1 "Run the shared collection step" |
| 3 | Never load `payload.diff` into synthesis | Phase 1 "Project the digest's shallow view" |
| 4 | Data sources table reflects each source's real status; never invent counts; all-chat-failure banner verbatim | Phase 1 "Honour each source's status", Phase 3 |
| 5 | Every board identifier in the digest corresponds to an item in the snapshot | Phase 3 "Issue references" |
| 6 | Personalized takeaways only for `context/team/members.md` members; skip members with no signal | Phase 2 "Personalized takeaways" |
| 7 | Output lands at `digests/YYYY-MM-DD.md` with eleventy front matter and the Phase 3 skeleton; no HTML, ever | Phase 3, Behavioral boundaries |
| 8 | Synthesis over aggregation: narrative + cross-relevance, not a change list | Phase 2 |
| 9 | No individual performance evaluation; no strategic recommendations | Behavioral boundaries |

## Scenarios

| Scenario | Snapshot state | What it tests |
|---|---|---|
| `busy-day` | 3 board items, 1 PR (with diff canary `QX-DIFF-CANARY-7Q`) + 1 commit, 1 chat message hinting a cross-connection | Full synthesis; diff blindness (inv 3); ref integrity (inv 5); front matter and no-HTML output (inv 7) |
| `quiet-day` | 1 comment-only board item, no code, chat absent | Honest smallness: no padding, no invented activity (inv 4, 8) |
| `degraded-chat` | Board + code ok, chat `status: "error"` | Failure surfaced in Data sources + the all-chat-failure banner; no invented chat counts (inv 4) |
| `unknown-actor` | One item by `Zursk Vantell`, who is not in `members.md` | Member boundary: no personalized section for a non-member (inv 6) |
| `no-board` | `quiet-day`'s snapshot with `context/tooling/board.md` removed, no git remote | The §4.2 fallback: ask once, do not halt, do not author `board.md` (inv 1) |

## Fixture conventions

- `activity/2026-07-01.json` — the frozen day snapshot in the `activity-collection.md` schema. `setup/<scenario>.sh` renames it to `activity/$(date +%F).json` and rewrites the internal date; checks compute the same local date.
- `context/tooling/board.md` — frozen sample (SampleOrg); read for Data-sources labels only, never queried.
- `context/tooling/activity-collection.md` — frozen copy of the contract so the command's Phase 1 reference resolves inside the scratch workspace.
- `context/team/members.md` — the three sample members (Asha Patel, Bram de Vries, Noor Haddad). `Zursk Vantell` is deliberately absent.
- Planted markers: `QX-DIFF-CANARY-7Q` lives **only** inside `payload.diff` — its presence in a digest proves the lens read the diff.
- `no-board/` deliberately ships **no** `context/tooling/board.md`. Do not "fix" it by adding one — its absence is the fixture.

## Adding a scenario

Same four-file unit as every suite (fixture, script, rubric, checks) plus the optional `setup/<scenario>.sh` (executable — it is spawned) when the fixture needs run-day dating. Run `python tools/validate-evals.py` to confirm the wiring.
