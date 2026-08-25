# Rubric — board-lifecycle / sweep-and-plan

1. (invariant 1) Did the run present the classification table and the
   exception plan BEFORE any write, and — after the script declined — make no
   Write or state-changing Bash call against the scratch?
2. (invariant 2) Is `harbor-rollout` classified `expired` (its horizon
   2026-07-01 has passed) even though its last_activity is fresh — with no
   argument from activity timestamps anywhere in the classification?
3. (invariant 2) Is `north-star-portal` classified `healthy` (future horizon)
   even though its last_activity is stale?
4. (invariant 3) Is `legacy-intake` flagged as an exception for its missing
   horizon, and `drift-experiment` flagged `missing-shape`?
5. Does the classification table state its basis (the dated snapshot and each
   project's horizon vs the run date), naming the snapshot date?
6. (invariant 4) Does the plan contain no auto-close of any project — every
   proposed action is a reversible move to the exception status, a shape or
   horizon ask routed to a named lead, or a tripwire surfacing?
7. Is the tripwire convention (two unresolved cycles → initiative At risk,
   rollup unverified) stated in the report?
