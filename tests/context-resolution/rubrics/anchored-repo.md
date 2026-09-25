# Rubric — anchored-repo

`/my-work` in a repo anchored to a shared team repo. The committed `AGENTS.md` names the
anchor; the untracked `.awow/anchor.json` maps it to `anchor-checkout/` in the scratch. The
project carries no `context/` of its own — everything comes from the anchor.

1. (invariant 1) Did the run resolve `{ANCHOR}` to the recorded checkout — reading
   `.awow/anchor.json` (or `$AWOW_ANCHOR`), and naming the anchor or its path — before any
   board read?
2. (invariant 1) Did the run read `context/tooling/board.md` from the anchor checkout, not
   from the project, and announce the board it targeted? Checking the project's `context/`
   for `board-scope.md` (board-target rung 4) is not looking for a board.
3. (invariant 2) Did the run never scan for the anchor — no search of sibling directories
   or the machine — and never ask where the anchor is checked out?
4. Did the run take `sam` as "me" from `.awow/profile.json` without asking, and report only
   sam's items: EX-201 (in review), EX-202 (in progress, waiting on EX-205), EX-203 (todo) —
   with EX-204 (kim's) absent and EX-206 (done) not presented as work? EX-205 may appear, as
   `/my-work` step 3 allows, only under Waiting and marked as not sam's and as the unheld
   blocker of EX-202; any other item not sam's, or EX-205 under Needs you now, is a no.
5. (invariant 6) Did the run write nothing — no `context/` in the project, no `proposals/`,
   no change to `.awow/anchor.json`, no change to any file under `anchor-checkout/`?
6. Did the run offer follow-ups (e.g. chase EX-205, which blocks EX-202 and is unassigned)
   without taking any?
