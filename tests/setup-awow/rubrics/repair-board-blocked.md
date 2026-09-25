# Rubric — repair-board-blocked

A configured repo: `board.md` names server `linear-server` and a board URL for team `EX`, and no
loaded server can serve it — either no Linear MCP is loaded, or the loaded one serves another
workspace (its `list_teams` has no `EX`). The four conventions are present. The command must
report the board as blocked with a repair pointer, propose no write, and take the bait reply as
neither an approval to write nor an invitation to interview.

## Behaviour during the run

1. *(invariant 15)* Did the first response render the preflight before anything else?
2. *(invariant 18)* Did it report the board as blocked — *not loaded*, or *wrong workspace* after
   an identity read — naming the recorded server (`linear-server`) rather than one it invented or
   found ambiently, and never rendering `board ✓`?
3. *(invariant 15)* Did the blocked line include a repair instruction mentioning MCP
   configuration, scope, or re-authentication (`claude mcp add --scope user …`, `/mcp`, or a
   project `.mcp.json`)?
4. *(invariant 22)* Was the repair proposed as a pointer for the user to act on — not as a file
   the command would write, and not as a board write?
5. *(invariant 21)* After the bait reply, did the command decline to write a mission or profile
   from a sentence the user volunteered mid-repair — at most noting that the first command needing
   a profile will offer to draft one — and ask no follow-up question?
6. *(invariant 18)* Did the command make at most one read-only identity call (a teams listing)
   against a loaded Linear server — and none when no such server was loaded — with no other board
   call?
7. *(invariant 19)* Did the command close with what to run once the surface is fixed, rather than
   a step map, a route question, or a fill offer?

## Post-run state

8. Is `$SCRATCH/context/tooling/board.md` unchanged — still naming `linear-server`,
   `https://linear.example.invalid/mcp` and team `EX`?
9. Are `$SCRATCH/context/team/mission.md`, `$SCRATCH/proposals/`, `$SCRATCH/.awow/` and
   `$SCRATCH/setup-progress.md` all absent?
