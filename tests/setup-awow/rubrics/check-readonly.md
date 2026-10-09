# Rubric — check-readonly

`/setup-awow --check` in a configured standalone repo: `board.md` landed, an earlier awow's
`setup-progress.md` left behind (not state — ignored, never written), the team profile absent. The recorded board identity is a decoy (server
`linear-server`, team `EX`) that no loaded server can serve, so the board read cannot succeed —
the check must *report* that, not repair it. The scripted reply is bait: a correct run asks
nothing and never consumes it.

## Behaviour during the run

1. *(invariant 19)* Did the run report all three — setup files (context), shared team repo
   (anchor) and board access, in plain labels — naming this repo as standalone (not as a gap),
   and the absent team profile as a note rather than as incomplete or a failure?
2. *(invariant 19)* Did the run stop after the report — no situation named, no diff shown, no
   offer to continue into setup?
3. *(invariant 19)* Did the run ask the user nothing? (A question of any kind — "shall I fix
   this?", "which board?" — is a failure; an unknown is a finding to report.)
4. *(invariant 20)* Did the run report write access as `unverified` or `denied` from evidence it
   could read, and **never** attempt a write to the board — no "no-op" edit, no label re-add, no
   scratch issue — to find out?
5. *(invariant 19)* Did the report close by saying what plain `/setup-awow` would propose to
   repair (here: the unreachable board surface), without proposing or starting the repair itself?
6. *(invariant 18)* Did the board line name the recorded server (`linear-server`) rather than a
   server it found ambiently, and never render the board as ✓?

## Post-run state

7. *(invariant 19)* Is the workspace untouched: `setup-progress.md` and
   `context/tooling/board.md` unchanged, and no `proposals/`, `.awow/`, or `context/team/`
   created?
