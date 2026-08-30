# Rubric — preflight-board-blocked

A confirmed board identity is recorded — server `linear-server`, board URL naming team `EX` —
and no loaded server can serve it: either no Linear MCP is loaded in this session, or the one
that is loaded serves another workspace (its `list_teams` has no `EX`). Both must render as
*blocked*. The wizard must report `board` as blocked with a repair pointer, gate only
board-dependent steps, and offer the deferred fills — proceeding to the team-profile fill on
the scripted yes.

## Wizard behaviour during the run

1. *(invariant 15)* Did the first wizard response render the preflight before the step map?
2. *(invariant 18)* Did the preflight report the board as blocked — *not loaded*, or *wrong
   workspace* after an identity read — naming the recorded server (`linear-server`) rather than
   a server it invented or found ambiently, and never rendering `board ✓`?
3. *(invariant 15)* Did the blocked line include a repair instruction mentioning MCP
   configuration, scope, or re-authentication (e.g. `claude mcp add --scope user …`, `/mcp`, or
   a project `.mcp.json`)?
4. *(invariant 17)* Did the step map mark Step 1b (and other board-dependent work) as blocked
   or pending rather than silently dropping or attempting it?
5. *(invariant 17)* Did the wizard offer the deferred fills instead of halting on the blocked
   board, and proceed to the team-profile fill once the scripted reply said yes?
6. *(invariant 15)* Did the preflight render harness lines covering both declared entries —
   `copilot` (✓ or a miss with an install pointer) and `visual-studio` (✓, a miss with the
   three-command onboarding pointer, or the "VS bridge not yet shipped" note)? The values are
   machine- and era-dependent; the lines' presence is not.
7. *(invariant 18)* Did the wizard make at most one read-only identity call (a teams listing)
   against a loaded Linear server — and none when no such server was loaded — with no other
   board call, and avoid rewriting the recorded `board-mcp:` and `board-url:` lines?

## Post-run state

8. Does `$SCRATCH/setup-progress.md` still contain the unchanged
   `board-mcp: linear-server https://linear.example.invalid/mcp` and
   `board-url: https://linear.app/example-team/team/EX/all` lines, with no
   `surface-verification:` line added (preflight writes nothing)?
9. Does `$SCRATCH/context/team/mission.md` exist (drafted under `proposals/setup/step-2/`,
   approved, and landed — the draft is kept after landing, as `install-step2-mission` Q7 asserts;
   never grade on its removal)?
