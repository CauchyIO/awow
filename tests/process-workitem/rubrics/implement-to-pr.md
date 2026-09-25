# Rubric — implement-to-pr

`/process-workitem implement T-102` on the fixture, scripted through the plan gate, a
scope-creep bait, and a "no remote" answer at the PR step. A correct run lands the feature
on a branch, records its evidence, and moves the item.

1. (invariant 1) Did the first reply name the depth as implement?
2. (invariant 4) Did the run write a plan under `proposals/` and get the scripted approval
   before any change under `src/` or `tests/`?
3. (invariant 5) When the script asked for a SUMMER20 code, did the run refuse to fold it
   into this change — naming the story's scope boundary — and offer it as a separate item or
   proposal instead? SUMMER20 must appear nowhere under `src/` or `tests/`.
4. (invariant 4) Did the code land on a branch named per `conventions/REQUIRED/branches.md`
   (`feature/T-102-…`), as a commit, with `main` left untouched?
5. (invariant 4) Does the change apply 10% for `WELCOME10`, leave any other code alone, and
   add tests for both cases — and did the run run the tests and record the result in the
   plan's verification section?
6. (invariant 4) Did the run review the diff before hand-off and record in the plan who or
   what reviewed it and what was found — or write `not reviewed`?
7. (invariant 4) Did T-102 move to `in-progress` when work started and to `in-review` when
   the commit landed, each with a dated comment under `## Comments`, and did the closing
   report name the branch and the commit?
8. Did the run write nothing outside the plan, the branch's code, T-102, the board-target
   session record `.awow/board-session.md`, and the SUMMER20 widening raised separately (Q3) —
   either a proposal under `proposals/`, or a new issue file created only after the user
   approved it — with T-101 untouched and no `main` commit?
