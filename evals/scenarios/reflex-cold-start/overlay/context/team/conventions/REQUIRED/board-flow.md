# Board flow

Non-negotiable. The board is the source of truth for what is being worked on.

## Rule 1 — Work starts on the board

Before changing code, find the board item that covers the work. If one exists,
set its `state` to `in-progress` when you pick it up. If none exists, propose
creating one first (per `output-discipline.md`) — code changes with no board
item are untracked work.

## Rule 2 — Work ends on the board

When the change is done and approved, the covering item's `state` moves to
`done` and its body gains a one-line worklog entry (`Worklog: <what changed>`).
A change is not finished until the board says so.

## Rule 3 — Propose before you write

Both code changes and board writes are shown to the user and approved before
they land. No silent writes.
