# Rubric — workspace-root

The scratch root is not a git repo; `repo-solo/` (one board) and `repo-mono/`
(index-form, two boards) sit beneath it — the spec's three-boards-two-teams case.
A closing cross-check names PROD-1 by ticket id, testing that an explicit
reference resolves the right installation and board in one step.

## Behaviour during the run

1. *(invariant 1)* Did the run enumerate both installations (repo-solo, repo-mono)
   before citing any board item?
2. *(invariant 4)* Exactly one installation question, answer "repo-solo" respected
   for the rest of the run — and no second (board) picker, since repo-solo has a
   single-form board.md?
3. *(invariant 1)* Is SOLO-1 the only board id presented as the user's work?
4. *(invariant 2)* Are PROD-1/PROD-2/INF-1 (repo-mono's boards) never cited, and
   repo-mono's context never applied?
5. *(invariant 3)* Did the PROD-1 cross-check resolve to repo-mono's product board
   in one step — no installation picker, no board picker — with a one-line
   targeting announcement (e.g. `targeting board: product`)?
6. *(invariant 4)* Did the run treat that resolution as invocation-scoped — the
   repo-solo pin unchanged, no switch of the "your work" framing to repo-mono?
7. *(invariant 5)* Did the run treat both repos as scaffolded (no /setup-awow
   offer)?

## Post-run state

8. *(invariant 6)* All four board spec files are byte-identical to the fixtures.
