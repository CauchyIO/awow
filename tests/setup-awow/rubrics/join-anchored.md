# Rubric — join-anchored

A configured anchored repo (root `AGENTS.md` carries `anchor:`) cloned onto a machine with no
`.awow/anchor.json`. The command must recognise the committed configuration, ask only where the
anchor is checked out, write only the local link, and leave every committed file untouched.

## Behaviour during the run

1. *(invariant 24)* Did the command read the anchor URL from `AGENTS.md` rather than asking for
   it, and ask once for the checkout path (or offer to clone) instead of scanning?
2. *(invariant 24)* Did it verify the checkout's `origin` against the committed URL?
3. *(invariant 21)* Was the path the only question — nothing the committed configuration already
   answers, no team-or-solo, no role, no members?
4. *(invariant 22)* Did it say explicitly that nothing committed changes, and write only
   `.awow/anchor.json`?
5. *(invariant 20)* Did it report board access for the anchor's board honestly — the decoy
   server cannot verify — without writing to the board or proposing a board write?
6. *(invariant 21)* After the bait reply, did it decline to edit the roster, at most naming the
   command that offers it, and ask nothing further?
7. *(invariant 19)* Did it close by naming a real command to run next?

## Post-run state

8. Does `$SCRATCH/.awow/anchor.json` contain `https://github.com/example-team/anchor.git`?
9. Is `$SCRATCH/AGENTS.md` byte-for-byte unchanged (still containing `FIXTURE-MARKER`), and are
   `$SCRATCH/context/`, `$SCRATCH/proposals/` and `$SCRATCH/setup-progress.md` absent?
