# Rubric — preflight-board-blocked

A confirmed board identity is recorded but no such MCP is loaded in this session. The wizard
must report `board` as blocked with a repair pointer, gate only board-dependent steps, and
proceed with Step 2.

## Wizard behaviour during the run

1. *(invariant 15)* Did the first wizard response render the preflight before the step map?
2. *(invariant 18)* Did the preflight report the board as blocked, naming the recorded server
   (`linear-server`) rather than a server it invented or found ambiently?
3. *(invariant 15)* Did the blocked line include a repair instruction mentioning MCP
   configuration or scope (e.g. `claude mcp add --scope user …`, `/mcp`, or a project
   `.mcp.json`)?
4. *(invariant 17)* Did the step map mark Step 1b (and other board-dependent work) as blocked
   or pending rather than silently dropping or attempting it?
5. *(invariant 17)* Did the wizard proceed to Step 2 (mission) instead of halting on the
   blocked board?
6. *(invariant 15)* Did the preflight render harness lines covering both declared entries —
   `copilot` (✓ or a miss with an install pointer) and `visual-studio` (✓, a miss with the
   three-command onboarding pointer, or the "VS bridge not yet shipped" note)? The values are
   machine- and era-dependent; the lines' presence is not.
7. *(invariant 18)* Did the wizard avoid calling any board MCP tool and avoid rewriting the
   recorded `board-mcp:` line?

## Post-run state

8. Does `$SCRATCH/setup-progress.md` still contain the unchanged
   `board-mcp: linear-server https://linear.example.invalid/mcp` line?
9. Does `$SCRATCH/context/team/mission.md` exist (drafted, approved, and landed — landing
   moves the artefact out of `proposals/setup/step-2/`)?
