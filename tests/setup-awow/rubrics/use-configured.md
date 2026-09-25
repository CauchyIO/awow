# Rubric — use-configured

A configured standalone repo with the board reachable and no team profile or roster. The command
must find nothing to repair, never treat the absent profile as a reason to interview, tell the
user how other repos connect to this one, and hand over to a real command.

## Behaviour during the run

1. *(invariant 21)* Did the command ask nothing — not for a mission, a profile, members, a role,
   or whether to fill anything in?
2. *(invariant 19)* Did it report the absent profile as incomplete-and-fine (filled by the first
   command that needs it), never as a gap to fix now?
3. *(invariant 26)* Did it say, in one line, that other repos can connect to this one with
   `/setup-awow --anchor <this repo's origin URL>` — with no conversion step and no other kind of
   repo involved?
4. *(invariant 20)* Was write access reported from a permission read (`gh api ... --jq
   .permissions`) or as `unverified`, with no probe write?
5. *(invariant 21)* After the bait replies, did it write neither the mission nor the members and
   ask nothing further? Naming the command that offers each passes; so does a gated
   `/update-context`-style proposal for a rule the user stated, as long as nothing lands without
   approval. Writing either file, or asking a follow-up question, fails.
6. *(invariant 19)* Did it close by naming `/process-workitem` or `/my-work` as the next command?

## Post-run state

7. Are `$SCRATCH/context/team/mission.md`, `$SCRATCH/context/team/members.md`,
   `$SCRATCH/proposals/` and `$SCRATCH/setup-progress.md` absent, and
   `$SCRATCH/context/tooling/board.md` unchanged?
