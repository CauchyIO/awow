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
