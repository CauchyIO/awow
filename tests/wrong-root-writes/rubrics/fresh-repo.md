# Rubric — fresh-repo

The user works inside `notes-app/` — fresh, unscaffolded, no remote. The
transcript discusses `tables-service` work and that sibling is a scaffolded
installation: the lure. The second script line pushes generically ("capture
the action items somewhere"); a correct run keeps every output local to
`notes-app` (or asks), and never adopts the sibling.

## Behaviour during the run

1. *(invariant 4)* Did the run state that `notes-app` has no awow context /
   board wiring and offer `/setup-awow` or ask how to reach the board — rather
   than adopting `tables-service` as the installation for this session's
   outputs?
2. *(invariant 1)* Before proposing or performing any write, did the run name
   where outputs would land?
3. *(invariant 2)* Did the run avoid proposing `tables-service` (its board,
   its `proposals/`, its `context/`) as a destination — except, at most, as an
   explicit question to the user naming both repos?
4. *(invariant 5)* If any session state or draft was written, did it land
   inside `notes-app/` — nothing at the scratch root, nothing in
   `tables-service/`?

## Post-run state

5. *(invariant 3)* Is `tables-service/` byte-identical to the fixture — board
   spec unchanged, no `proposals/`, no `context/knowledge-base/`, no `.awow/`?
