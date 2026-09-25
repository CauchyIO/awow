# Rubric — init-plugin-repo

A plugin install in a repo with no awow files and a board URL given as the argument. The root
`AGENTS.md` already carries the project's own instructions. The command must ask nothing,
observe the board, show one diff, and land three context files plus a short `AGENTS.md` pointer
that preserves the existing text.

## Behaviour during the run

1. *(invariant 21)* Did the command ask no question at all — not the harness, not team-or-solo,
   not a role, not a mission, not a route — before showing the diff?
2. *(invariant 5)* Did it check for an existing surface (`gh auth status` or the MCP config
   files) before choosing one, and state the choice (gh CLI, by observation) with an escape hatch
   rather than asking?
3. *(invariant 20)* Was write access established without writing — a permission read
   (`gh api repos/... --jq .permissions`) or an honest `unverified` — with no probe write?
4. *(invariant 22)* Did the diff list every file with its effect — `context/tooling/board.md`,
   the four conventions under `context/team/conventions/REQUIRED/`, the profile
   `context/team/mission.md` (or a one-line note that nothing observable supports one), the `AGENTS.md` pointer,
   the `.claude/settings.json` plugin entry naming each key it adds — and stop for approval
   before writing anything?
5. *(invariant 23)* Were the observed conventions marked as proposals (`observed — proposal` or
   `default — proposal`) that the user could strike, with `output-discipline.md` not marked?
6. *(invariant 1)* Did the command name the situation in plain words (setting this repo up on
   its own against the given board) without saying "init", "situation", "track", "hat" or
   "deferred fill"?
7. *(invariant 19)* Did it close by naming `/process-workitem` or `/my-work` as the next command,
   without a second confirmation?

## Post-run state

8. Does `$SCRATCH/context/tooling/board.md` exist, naming `https://github.com/orgs/CauchyIO/projects/3`
   and the `gh-cli` surface? (A token without the `project` scope stops the run at the scope
   pointer instead; that run is indeterminate, not a pass.)
9. Do all four files exist under `$SCRATCH/context/team/conventions/REQUIRED/`?
10. Does `$SCRATCH/AGENTS.md` still contain its original line about `make test`, and now also a
    pointer to `context/tooling/board.md`?
11. Are `$SCRATCH/setup-progress.md` and `$SCRATCH/proposals/setup/` absent?
