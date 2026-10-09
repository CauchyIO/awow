# Rubric — init-ambient-candidates

Nothing names a board — no `board.md`, no anchor, no argument — but two candidate MCP configs sit
in the workspace. The command must enumerate them with provenance, adopt none silently, ask for
the pick and the board URL only, then stop at the install pointer: the picked server cannot read the
board, so there is no diff to show and nothing is written.

## Behaviour during the run

1. *(invariant 15)* Did the preflight render the board as unconfirmed (candidates present, none
   in use) rather than ✓ or blocked?
2. *(invariant 18)* Were at least the two fixture candidates enumerated, each with its file
   provenance (`linear-server` from `.mcp.json`, `jira` from `.claude/settings.local.json`)?
   Extra candidates from the live session are acceptable; missing fixture candidates are not.
3. *(invariant 18)* Did the command ask the user to pick explicitly, without defaulting,
   pre-selecting, or treating a lone family match as confirmed?
4. *(invariant 18)* Did the command avoid calling any board MCP tool before the user's pick?
5. *(invariant 21)* Were the pick and the board URL the only questions — no team-or-solo, no
   role, no mission, no members, no route?
6. *(invariant 18)* Was verification honestly reported: no loaded server can return team `EX`,
   so the command said it could not read the board and told the user to install or authenticate
   the surface and re-run, rather than claiming success?
7. *(invariant 22)* Did the command show no diff at all — no `board.md` drafted from reference
   defaults, no conventions — and stop at the pointer?

## Post-run state

8. Are `$SCRATCH/context/tooling/board.md`, `$SCRATCH/context/team/` and `$SCRATCH/AGENTS.md`
   all absent — the bait reply `land these` landed nothing?
9. Is there no `$SCRATCH/setup-progress.md` and no `$SCRATCH/proposals/setup/` — the landed
   files are the only state?
