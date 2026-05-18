# Rubric — dogfood-step1a-cli

Phase 1a wires the `gh` CLI surface for dogfood's GitHub Projects board. Script supplies: `current only`, the board URL, and `approve`.

## Wizard behaviour during the run

1. *(invariant 1)* First wizard response lists every step 0 → 9 with status markers; Step 0 marked ✓, Step 1 marked ⧗.
2. *(invariant 4)* Harness self-detected (e.g. "I'm running in Claude Code") rather than inferred from directory listing.
3. *(invariant 5)* Wizard checked for an existing board surface — read `$SCRATCH/.claude/settings.json` / `.mcp.json` / `.vscode/mcp.json` and/or ran `gh auth status` — before asking for a URL.
4. *(invariant 7)* When the URL `https://github.com/orgs/CauchyIO/projects/3` was provided, the wizard inferred GitHub Projects (not refused as unsupported).
5. *(invariant 11)* Wizard recorded the surface as `surface: gh-cli` in its board.md draft.
6. *(invariant 8)* Wizard drafted board.md under `$SCRATCH/proposals/setup/step-1/board.md` before moving it to `$SCRATCH/context/tooling/board.md`.

## Post-run state

7. *(invariant 9)* `$SCRATCH/context/tooling/board.md` exists and contains the substrings: `CauchyIO`, `gh-cli`, `https://github.com/orgs/CauchyIO/projects/3`.
8. *(invariant 8)* `$SCRATCH/proposals/setup/step-1/board.md` also exists (the draft was kept, not deleted, after landing).
