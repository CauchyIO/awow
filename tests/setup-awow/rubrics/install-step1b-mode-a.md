# Rubric — install-step1b-mode-a

Phase 1b walks the reference sections for `context/tooling/boards/github-issues/reference/` in Mode A (greenfield). Script provides six `accept` replies covering each reference section in order.

## Wizard behaviour during the run

1. *(invariant 13)* Before walking sections, did the wizard count closed issues on the board, announce the count, and announce that it is running Mode A because the count is below 10?
2. *(invariant 13)* Did the wizard tell the user which reference layer is in use (starter pack vs. `.agents-overrides/`) before walking each section?
3. *(invariant 8)* Did each section's draft get appended to `$SCRATCH/proposals/setup/step-1/board.md` (proposal-first, not direct write to `context/tooling/board.md`)?

## Post-run state

4. *(invariant 9)* `$SCRATCH/proposals/setup/step-1/board.md` contains all of: `## State machine`, `## Hierarchy`, `## Label taxonomy`, `## Required fields`, `## Team page conventions`.
