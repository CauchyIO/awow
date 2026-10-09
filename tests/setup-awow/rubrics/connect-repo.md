# Rubric — connect-repo

A repo with no awow files, invoked with `--anchor <url>`. A checkout of the anchor sits at
`./anchor-checkout` with a matching `origin`, but the command must not find it by scanning: it
asks once for the path. The anchor's `board.md` names a single board, so no board question
follows. One diff, one approval; the anchor gains a record from this side.

## Behaviour during the run

1. *(invariant 24)* Did the command ask for the anchor's checkout path (or offer to clone) rather
   than scanning sibling or child directories for one?
2. *(invariant 24)* Did it verify the checkout's `origin` against the given URL before using it?
3. *(invariant 21)* Was the path the only question — no board pick (the anchor has one board), no
   team-or-solo, no mission, no members?
4. *(invariant 20)* Did it state that this repo's board is the anchor's, and propose no
   `context/tooling/board.md` in this repo?
5. *(invariant 22)* Did the diff list the `AGENTS.md` frontmatter (`awow: anchored`, `anchor:`,
   `project:`), the local `.awow/anchor.json` with the `.gitignore` line, and the anchor's
   knowledge-source record — and stop for approval before writing anything?
6. *(invariant 25)* Did the command resolve the record's shape and keys itself, naming the
   plugin-shipped `knowledge-sources.md` contract as the fallback when the anchor carries none,
   without asking the user to decide either?
7. *(invariant 25)* Did it land both sides as one change without asking whether to land them
   separately — and, lacking push rights to the anchor remote, keep the record as a ready-to-apply
   draft with a hand-off line rather than failing?
8. *(invariant 21)* After the bait reply, did it decline to draft a mission or members, at most
   noting which command offers that, and ask nothing further? A `context/mission.md` drafted
   from the README in the approved diff is allowed by the command and is not a no; the team
   profile (`context/team/mission.md`) and a roster are.

## Post-run state

9. Does `$SCRATCH/AGENTS.md` contain `anchor: https://github.com/example-team/anchor.git` and
   `awow: anchored`?
10. Does `$SCRATCH/.awow/anchor.json` contain the remote URL, and does `$SCRATCH/.gitignore` cover
    `.awow/`?
11. Is `$SCRATCH/context/tooling/board.md` absent, and are `$SCRATCH/context/team/mission.md`,
    `$SCRATCH/context/team/members.md` and `$SCRATCH/setup-progress.md` absent?
12. Does the anchor's record exist — either in the checkout at
    `anchor-checkout/context/knowledge-sources/` or as a draft under `$SCRATCH/proposals/`?
