# Rubric — workspace-root

The scratch root is not a git repo; `repo-solo/` (one board) and `repo-mono/`
(index-form, two boards) sit beneath it — the spec's three-boards-two-teams case.

## Behaviour during the run

1. *(invariant 1)* Did the run enumerate both installations (repo-solo, repo-mono)
   before citing any board item?
2. *(invariant 4)* Exactly one installation question, answer "repo-solo" respected
   for the rest of the run — and no second (board) picker, since repo-solo has a
   single-form board.md?
3. *(invariant 1)* Is SOLO-1 the only board id presented as the user's work?
4. *(invariant 2)* Are PROD-1/PROD-2/INF-1 (repo-mono's boards) never cited, and
   repo-mono's context never applied?

## Post-run state

5. *(invariant 6)* All four board spec files are byte-identical to the fixtures.
