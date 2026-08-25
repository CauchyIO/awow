# tests/migrate-to-plugin/

Evaluates `/migrate-to-plugin` (AWO-259) against real vendored fixture repos —
the acceptance criteria explicitly forbid mocks.

## Fixture model

The fixture directories are empty markers; the tree is built by the setup hook
from this repo's own history so the vendored bytes are real:

1. `git archive v0.9.2` of the starter surface (`.agents/`, `tools/`, `setup/`,
   `context/`, `mcps/`, root files, and the generated `.claude/`/`.github/`/
   `.opencode/` stubs) unpacked into the scratch.
2. `git init` + a "vendor awow v0.9.2" commit — so the vendor-commit
   classification ladder has a real ref to find.
3. Two team edits, committed: a rule appended to
   `.agents/commands/_workitem-archetypes/feature.md`, and a team note appended
   to `.agents/commands/daily-digest.md`.
4. The current `dist/` payload copied to `.awow-payload/` (untracked), passed
   to the command as `--source`.

## Scenarios

| Scenario | Lockfile state | Classification path under test |
| --- | --- | --- |
| `pre-lockfile` | `tools/awow_lock.py` and `tools/awow.lock.json` removed before the vendor commit — a repo vendored before the update machinery existed | vendor-commit compare (the pre-lockfile footgun: edits must still classify as edited) |
| `post-lockfile` | lockfile re-seeded at the pristine vendor state via the scratch's own `awow_lock.py backfill`, committed before the team edits | lockfile baseline compare |

## Invariants

1. **Plan gate** — nothing is written before the plan is approved.
2. **Edits survive** — the two team edits are migrated (archetype →
   `context/team/workitem-archetypes/`) or kept repo-local
   (`.claude/commands/daily-digest.md`), byte-content preserved, never
   reverted to shipped defaults.
3. **Unedited vendored surface deleted** — `.agents/`, vendored `tools/`
   machinery, `setup/`, generated stubs.
4. **Root pointers rewritten** — `AGENTS.md` no longer points into `.agents/`.
5. **Team-data context untouched** — `context/team/` stays.
6. **Parity table** — emitted, every row resolving to plugin / kept
   repo-local / retired (graded by rubric).
