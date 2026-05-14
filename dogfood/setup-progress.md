# Setup progress — dogfood workspace

State file for `/setup-awow` running against the `dogfood/` workspace (awow applied to itself, team = Cauchyio).

Note: while the wizard prompt at `.agents/commands/setup-awow.md` references paths relative to the repo root, this dogfood run lands artefacts under `dogfood/` instead (e.g. `dogfood/context/team/mission.md`, `dogfood/proposals/setup/step-2/`). The wizard is being driven by hand for this run; a `--root` argument may follow.

## Status

- [x] **Step 0 — Installer (REQUIRED).** Inherited from the parent repo: `.venv/` is at the repo root, and the pointer stubs in `.claude/commands/` and `.github/prompts/` are populated. Dogfood does not need its own installer run.
- [x] **Step 1 — Kickoff (REQUIRED).** Board: GitHub Projects on `CauchyIO/awow`, canonical project `Dogfood` (#3 at <https://github.com/orgs/CauchyIO/projects/3>). Read/write surface: `gh` CLI (MCP deliberately skipped to avoid PAT friction; see board.md). Read-ok, write-ok (no-op `gh project edit` set the short description). Inflation control: `dogfood` label on all walkthrough-generated issues + `tools/reset-adopter-state.py` extended to bulk-close them.
- [x] Step 2 — Mission. Landed at `dogfood/context/team/mission.md`. Single sentence: "Cauchy helps engineering teams make their plan as trustworthy as their code, by maintaining the agentic way of working as a living starter pack that adopters can actually read, run, and customise."
- [x] Step 3 — Required conventions. All four landed at `dogfood/context/team/conventions/REQUIRED/`. awow-specific tweaks: `dogfood` label codified; GitHub-repo-scoped (not workspace) label rule; PR/commit notes added to output-discipline; `prompt/{slug}` branch pattern for board-less prompt iteration.
- [x] Step 4 — Members and style. `members.md` populated for solo team (Casper, `@hetspookjee`) with a Growth section. Style files landed under `dogfood/context/team/style/`: added "no em-dashes on board" rule, awow-specific notes per file, dropped the parked-Q24 reference in placement.md.
- [ ] Step 5 — `CLAUDE.md` / `AGENTS.md` bootstrap
- [ ] Step 6 — Knowledge base seed
- [ ] Step 7 — Neighbouring teams
- [ ] Step 8 — Adoption plan
- [ ] Step 9 — Extras surfaced
- [ ] Step 10 — Skills review (keep / customise / drop each shipped skill; record per-skill decisions below)

## Last session

- 2026-05-14 — Set up `dogfood/` workspace; restored top-level template stubs. Step 2 mission landed. Step 1 redone against GitHub Projects (Linear → GitHub for this repo): refreshed `gh` token with `read:project,project`; created `CauchyIO/projects/3` ("Dogfood"); no-op write verified; abandoned untitled projects #1/#2 deleted by user. Reset script extended with `dogfood`-label bulk-close. Step 3 landed: four REQUIRED conventions in `dogfood/context/team/conventions/REQUIRED/`. Step 4 landed: members.md (solo, Casper) plus four style files under `dogfood/context/team/style/`. Steps 0–4 complete; Step 5 (CLAUDE.md / AGENTS.md bootstrap) is the recommended next.

## Notes

`/awow-reset` deliberately does **not** touch this folder. The reset script's `TRACKED_OVERWRITTEN` and `UNTRACKED_CREATED` lists scope to the top-level template surface only.
