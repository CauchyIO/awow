# Setup progress — dogfood workspace

State file for `/setup-awow` running against the `dogfood/` workspace (awow applied to itself, team = Cauchyio).

Note: while the wizard prompt at `.agents/commands/setup-awow.md` references paths relative to the repo root, this dogfood run lands artefacts under `dogfood/` instead (e.g. `dogfood/context/team/mission.md`, `dogfood/proposals/setup/step-2/`). The wizard is being driven by hand for this run; a `--root` argument may follow.

## Status

- [x] **Step 0 — Installer (REQUIRED).** Inherited from the parent repo: `.venv/` is at the repo root, and the pointer stubs in `.claude/commands/` and `.github/prompts/` are populated. Dogfood does not need its own installer run.
- [x] **Step 1 — Kickoff (REQUIRED).** Board: GitHub Projects on `CauchyIO/awow`, canonical project `Dogfood` (#3 at <https://github.com/orgs/CauchyIO/projects/3>). Read/write surface: `gh` CLI (MCP deliberately skipped to avoid PAT friction; see board.md). Read-ok, write-ok (no-op `gh project edit` set the short description). Inflation control: `dogfood` label on all walkthrough-generated issues + `tools/reset-adopter-state.py` extended to bulk-close them.
- [x] Step 2 — Mission. Landed at `dogfood/context/team/mission.md`. Single sentence: "Cauchy helps engineering teams make their plan as trustworthy as their code, by maintaining the agentic way of working as a living starter pack that adopters can actually read, run, and customise."
- [x] Step 3 — Required conventions. All four landed at `dogfood/context/team/conventions/REQUIRED/`. awow-specific tweaks: `dogfood` label codified; GitHub-repo-scoped (not workspace) label rule; PR/commit notes added to output-discipline; `prompt/{slug}` branch pattern for board-less prompt iteration.
- [x] Step 4 — Members and style. `members.md` populated for solo team (Casper, `@hetspookjee`) with a Growth section. Style files landed under `dogfood/context/team/style/`: added "no em-dashes on board" rule, awow-specific notes per file, dropped the parked-Q24 reference in placement.md.
- [x] Step 5 — `CLAUDE.md` / `AGENTS.md` bootstrap. `dogfood/.agents/CLAUDE.md` hand-written (the worked example of what the broken `tools/bootstrap-claude-md.py` skeleton *should* produce). Stub's Do-not-propose defaults kept verbatim. Two backlog findings captured in `dogfood/backlog.md` instead of as GitHub issues: (a) drop the Python script and let the wizard do aggregation in-prompt; (b) soften Step 5's "populate Do-not-propose" wording.
- [x] Step 6 — Knowledge base seed. ADR `0001-gh-cli-vs-mcp.md`, pattern `dogfood-label-inflation-control.md`, and a populated `glossary.md` landed under `dogfood/context/knowledge-base/`. `architecture/` and `runbooks/` subfolders exist but are unseeded — fill organically.
- [x] Step 7 — Neighbouring teams. `dogfood/context/company/neighbouring-teams.md` written: Cauchy consulting (the rest of Cauchy, active on Boskalis) as the real bidirectional neighbour, plus platform-supplier stubs for Anthropic and GitHub. Adopter teams reserved as a "future neighbours" placeholder.
- [x] Step 8 — Extras surfaced. All seven spread/standardise commands listed with phase, prereqs, and pain removed. Dogfood-specific take: spread commands are stubs (v0.2); `/claudetracing-setup` flagged as a real candidate once v0.3 lands; `/cross-team-view` and `/programme-board-projection` are N/A while Cauchyio is a single team; `/daily-digest` and `/weekly-digest` are implemented but parked — solo committer makes the synthesis thin until dogfood adopters appear.
- [ ] Step 9 — Skills review (keep / customise / drop each shipped skill; record per-skill decisions below)

## Last session

- 2026-05-14 — Set up `dogfood/` workspace; restored top-level template stubs. Step 2 mission landed. Step 1 redone against GitHub Projects (Linear → GitHub for this repo): refreshed `gh` token with `read:project,project`; created `CauchyIO/projects/3` ("Dogfood"); no-op write verified; abandoned untitled projects #1/#2 deleted by user. Reset script extended with `dogfood`-label bulk-close. Step 3 landed: four REQUIRED conventions in `dogfood/context/team/conventions/REQUIRED/`. Step 4 landed: members.md (solo, Casper) plus four style files under `dogfood/context/team/style/`. Step 5 landed: hand-written `dogfood/.agents/CLAUDE.md`; two findings tracked locally in `dogfood/backlog.md` (no board issues filed). Steps 0–7 complete; the old Step 8 (adoption plan) has been removed from the wizard entirely — `.agents/commands/setup-awow.md`, `SETUP.md`, top-level `setup-progress.md`, README.md, the skills READMEs/SKILLs, the test rubric, and the regression-tests proposal were all updated and re-mirrored via `tools/gather.py`. Wizard is now 10 steps (0–9). The "extras surfaced" step is now Step 8 and is the recommended next.

## Notes

`/awow-reset` deliberately does **not** touch this folder. The reset script's `TRACKED_OVERWRITTEN` and `UNTRACKED_CREATED` lists scope to the top-level template surface only.
