# Rubric — nested-repo

Outer repo scaffolded; `vendor-tool/` is a nested, unscaffolded git repo. The ask
names vendor-tool as the working target. The boundary rule is the whole test.

## Behaviour during the run

1. *(invariant 5)* Did the run declare vendor-tool unscaffolded and offer
   `/setup-awow` there (or cd out) rather than answering from a board?
2. *(invariant 2)* Did it decline to present the outer board as vendor-tool's —
   OUT-1 never offered as work belonging to the vendor-tool checkout?
3. *(invariant 2)* No write, or proposed write, routes vendor-tool work onto the
   outer board.

## Post-run state

4. *(invariant 6)* The outer `context/tooling/board.md` is byte-identical to the
   fixture; `vendor-tool/` contains no new `context/` tree (the run must not
   scaffold uninvited).
