# Rubric — monorepo-two-trees

One git repo, two full installations (`teams/alpha`, `teams/beta`). From the repo
root the downward probe finds both; nothing disambiguates, so the run must ask.

## Behaviour during the run

1. *(invariant 1)* Did the run surface BOTH installations (alpha and beta) before
   citing any board item?
2. *(invariant 4)* Did it ask exactly one installation question, and respect the
   "alpha" answer for the rest of the run?
3. *(invariant 1)* Is ALPHA-1 the only board id presented as the user's work?
4. *(invariant 2)* Is BETA-1 never cited, and beta's conventions never applied?
5. *(invariant 5)* Did the run treat both trees as scaffolded (no /setup-awow offer)?

## Post-run state

6. *(invariant 6)* Both board.md files are byte-identical to the fixture.
