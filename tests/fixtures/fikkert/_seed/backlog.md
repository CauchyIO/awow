# Meta workspace backlog

Findings from running `/setup-awow` against `meta/` that should feed back into the awow template. Captured here, not on the public board, until they're ready to be worked.

Each entry: what to do, why (what surfaced it), where the change lives.

---

## Drop `tools/bootstrap-claude-md.py`; have the wizard do the aggregation in-prompt

- **What:** delete the v0.1 skeleton at `tools/bootstrap-claude-md.py` and rewrite `/setup-awow` Step 5 so the agent reads the team-context files and writes `CLAUDE.md` directly, rather than shelling out to a Python script.
- **Why:** the tool's whole job was to concatenate `mission.md`, `members.md`, `conventions/REQUIRED/*.md`, `style/*.md`, and `tooling/board.md` with section headers. The agent can do that in-session without a hardwired script — and avoiding hardcoded scripts keeps awow legible. Surfaced 2026-05-14 when this dogfood walkthrough reached Step 5 and the tool turned out to be `NotImplementedError`; the user pushed back against generating Python to fill the gap.
- **Where:** `tools/bootstrap-claude-md.py` (delete), `.agents/commands/setup-awow.md` Step 5 (rewrite), re-mirror via `tools/gather.py`.

## `cross-team-view` — deleted stub; rebuild only against real demand

- **What:** the `phase: standardise` stub `.agents/commands/cross-team-view.md` ("v0.3 ships the working version") was deleted 2026-07-03. If neighbouring-team visibility becomes a real ask, design it fresh from `context/company/neighbouring-teams.md` + the digest lenses rather than reviving the placeholder.
- **Why:** documented-but-unimplemented commands inflate the catalogue and mislead `/awow-add` users; the maintainer has never needed it and the single-team instance makes it N/A. Adopter-evidence rationale: `meta/proposals/eval-baseline-and-prompt-cleanup.md` §6. The `guide-standardise-reporting.html` guide still describes the *altitude* as planned — that framing stays honest without a stub file.
- **Where:** new command file + `/awow-add` wiring, when demand exists.

## `board-skill` — never landed; pain is covered elsewhere

- **What:** the drafted-but-never-committed `board-skill` stub ("commits-and-issues-never-link", v0.2) should not land as a command. Its pain is already covered by the board-linkage convention in `.agents/AGENTS.md` plus the opt-in `session-correlation` skill.
- **Why:** re-justify before reintroducing — same catalogue-inflation rationale as `cross-team-view`. Rationale: `meta/proposals/eval-baseline-and-prompt-cleanup.md` §6.
- **Where:** nothing to delete on `main`; this entry records the decision.

## Soften `/setup-awow` Step 5 — keep Do-not-propose defaults when they fit

- **What:** rephrase Step 5's "ask the user to populate the `## Do not propose` block" to "augment or keep the stub's defaults, depending on whether the team has specific scope-shedding to add".
- **Why:** the stub at `.agents/CLAUDE.md` ships with four reasonable defaults (don't restructure tree, don't add top-level folders, don't switch board/harness/trace, don't implement parked features). For teams who don't have team-specific scope-shedding statements yet, the defaults are sufficient. Forcing "populate" implies replacement — which led to a confused conversation about which "proposals" the agent was about to make (it wasn't planning any; the block lists things it should *not* propose). Surfaced 2026-05-14.
- **Where:** `.agents/commands/setup-awow.md` Step 5 wording.
