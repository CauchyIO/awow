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
