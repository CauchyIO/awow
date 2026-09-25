# tests/context-resolution — suite conventions

Command under test: `/my-work` (read-only board sweep — resolution conduct is the
subject; board content is minimal set dressing).

## Invariants (numbered — rubrics cite these)

1. Resolution happens before any board read: the run names the installation and/or
   board it resolved (or asks) before citing any board item.
2. The repo boundary is absolute: a board belonging to a parent or sibling repo is
   never cited, suggested, or written to on behalf of another repo's work.
3. A silent resolution (explicit reference or scope match) is announced with a
   one-line `targeting board: <name>` (or equivalent naming the installation).
4. A picker fires at most once per stage per session; the answer is respected for
   the rest of the run.
5. An unscaffolded repo produces the unscaffolded outcome (offer `/setup-awow` or
   cd) — never a borrowed board.
6. Fixture state is read-only for this command: no board spec file is modified.

## Fixture conventions

- Board specs declare `**Tool:** file-based sample board (frozen test fixture — the
  items ARE the list below; query no live surface)` and carry a `## Items` table:
  `| id | title | state | assignee |`. The assignee for "me" is `sam`.
- Setup hooks run `git init` + one commit in each directory that must read as a git
  repo at run time (fixtures cannot ship `.git/`). The workspace-root fixture's own
  root deliberately gets NO `git init`.
- The two `profile-*` scenarios inject `.awow/profile.json` from the setup hook
  *after* the fixture commit — `.awow/` is gitignored at any depth, so the profile
  must arrive untracked, exactly as it does in real life.

## Anchored scenario (journey 5)

- `anchored-repo` — the project carries `anchor:` in its root `AGENTS.md` and an untracked
  `.awow/anchor.json` (written by the setup hook with the scratch's absolute path) pointing
  at `anchor-checkout/`, a git repo whose `origin` matches the anchor URL. The project has
  no `context/` of its own: `{ANCHOR}` must resolve to the checkout, the board is read from
  there, and nothing is asked, scanned or written. `anchor-checkout/` is gitignored in the
  project so it reads as a separate checkout, not a subtree.

## Profile scenarios (Stage-2 rungs 5 and 1)

- `profile-default` — no scope evidence in the ask; the invoker-default rung must
  resolve the product board silently and take "me" from `board_identity`.
- `profile-vs-explicit` — the user names the infra board outright; the explicit
  reference beats the profile default, with no durable re-pin.

## Follow-ups (uncovered spec items)

- Missing `board-<name>.md` hard error — needs a fifth scenario with a dangling
  index entry.
- Board-stage session-pin and board-picker rungs never fire in any current
  scenario.
- From-a-subtree silent resolution (spec Testing item 2, monorepo shape) —
  blocked on per-scenario CWD control in the `/test-awow` runner.
