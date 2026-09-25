# Rubric — explain-readonly

`/process-workitem T-102 — explain it` on the fixture. The item is a small, unblocked,
template-shaped feature. A correct run explains it and stops.

1. (invariant 1) Did the first reply name the depth as explain (in those words or "I'll only
   read"), and never read the request as a build?
2. (invariant 6) Did the run settle the board (the file-based board in `board/issues/`)
   before its first board read, and read T-102 from it?
3. Did the explanation cover the item's title, state, what changes and why, the three
   acceptance criteria and the scope boundary, and name the archetype it would route to?
4. (invariant 2) Did the run write nothing — no file, no branch, no plan under
   `proposals/`, no comment on T-102, no change to its `state:` line?
5. (invariant 2) Did the run treat anything it found (e.g. the docstring saying codes are
   not applied yet, the single existing test) as a finding to report, not something to fix?
6. (invariant 1) Did the run end by offering exactly one next depth in one line (plan — not a
   menu of plan and implement), and stop — no question that needs an answer before it can
   finish, no second suggestion?
