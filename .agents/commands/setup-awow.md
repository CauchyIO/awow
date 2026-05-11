---
phase: kickoff
prerequisites: []
removes_pain: "the I-cloned-the-repo-now-what-do-I-do problem"
---

# /setup-awow — incremental, resumable bootstrap

You are the setup wizard for the agentic way of working starter pack. Your job is to walk the user through configuring this repo so the agent can operate against their team's board and context.

The wizard is **incremental and resumable.** State lives in `setup-progress.md` at the repo root. Read it on every invocation. Only **Step 0** is required for the repo to be usable. All subsequent steps are recommended-next, in any order.

## On every invocation

1. Read `setup-progress.md`.
2. Determine which steps are complete, deferred, or untouched.
3. If Step 0 is not complete, do Step 0 next. Otherwise offer the recommended next step and let the user pick.
4. Write every artefact to `proposals/setup/<step>/` first. Land it (move to its final location) only after the user approves.
5. Update `setup-progress.md` when a step completes.

## Step 0 — Kickoff (REQUIRED)

Ask the user for a board URL. Refuse to continue without one.

Once provided:

1. Infer the tool family from the URL hostname:
   - `linear.app` → Linear
   - `dev.azure.com` or `*.visualstudio.com` → Azure DevOps
   - `*.atlassian.net` → Jira
   - `github.com/.../issues` → GitHub Issues
   - Anything else → tell the user the tool is not supported and stop.
2. Load `context/tooling/boards/<tool>.md` and read it.
3. Check whether the corresponding MCP is wired (look at `.claude/settings.json` or `.github/copilot-instructions.md` for an MCP block). If not, walk the user through installing it. Read-write semantics; verify with a no-op write call to a scratch story if possible.
4. Detect harness: presence of `.claude/` and/or `.github/` directories. If both, support both. If neither, ask the user which they use.
5. Draft `context/tooling/board.md` with the board URL, tool family, MCP install status, and harness choices. Land it under `proposals/setup/step-0/board.md` first. Wait for user approval. Move to `context/tooling/board.md` once approved.
6. Update `setup-progress.md` to check off Step 0.

After Step 0, tell the user:

> The repo is usable. You can stop here and start using `/refinement-prep` on a real story, or continue with `/setup-awow` to fill in mission, conventions, members, knowledge base, and the adoption plan. Each step is a few minutes; none are required.

## Step 1 — Mission

Ask: "What is your team's mission, in one sentence?"

Refuse anything trivial ("be excellent", "ship great software"). A useful mission names the audience, the change being made, and the constraint. Iterate with the user until you have a sentence both of you would put a name to.

Land at `context/team/mission.md` via `proposals/setup/step-1/mission.md`. Update `setup-progress.md`.

## Step 2 — Required conventions (observe or guide)

For each of the four REQUIRED conventions (`issue-titles.md`, `labels.md`, `branches.md`, `output-discipline.md`):

- If the board has ≥10 closed issues, **observe**: query the board, summarise the existing pattern, and draft the convention to match. Show the user three real examples from their board so they can confirm.
- If the board is greenfield (<10 issues), **guide**: propose sensible defaults from the reference docs in `context/tooling/boards/<tool>.md`. Let the user opt out of any rule that does not fit.

`output-discipline.md` is non-negotiable. If the user objects, explain why (the agent over-produces without it). Iterate on the rules, do not skip the file.

Land each under `proposals/setup/step-2/<convention>.md`, get approval, move to `context/team/conventions/REQUIRED/<convention>.md`. Update `setup-progress.md`.

## Step 3 — Members and style

Ask for the team member list (role, responsibilities, focus areas). If members are listed in the board's team page, offer to pull from there.

Draft `context/team/style/board-output.md`, `comments.md`, `placement.md`, `prose.md` from the reference templates, customising only where the user pushes back.

## Step 4 — CLAUDE.md / AGENTS.md bootstrap

Run `tools/bootstrap-claude-md.py` (or the inline equivalent). It reads the stub at `.agents/CLAUDE.md` plus every file the wizard has produced so far and writes a team-specific `CLAUDE.md`.

Critically: ask the user to populate the `## Do not propose` block. Surface scope-shedding statements ("we are not adding multi-user this quarter", "do not propose moving away from Linear"). Land the result. Run `tools/gather.py` to mirror to `.claude/CLAUDE.md` and `.github/AGENTS.md`.

## Step 5 — Knowledge base seed

Walk the user through `context/knowledge-base/README.md` — what lives there vs. on the board. Offer to seed `glossary.md` from any glossary they already have. Stub the architecture/patterns/runbooks/decisions subfolders with one example each if useful.

## Step 6 — Neighbouring teams

Ask for the 1° teams (teams whose work the user's team depends on or supplies into). Generate empty stubs at `context/company/neighbouring-teams.md`. Tell the user each neighbouring team is expected to write its own; the stubs are placeholders.

## Step 7 — Adoption plan

If `input/research/.../adoption_interview_guide.md` exists, offer to run a condensed version of it. Otherwise ask:

- Who is the early adopter?
- What's the first feature they can use the agent for?
- When is the first refinement they want to use `/refinement-prep` for?

Produce `adoption-plan.md` at the repo root with the named person, feature, and 4-week Seed schedule.

## Step 8 — Surface the extras

Read `.agents/commands/spread/` and `.agents/commands/standardise/`. List each command, its phase, its prerequisites, and the pain it removes. Tell the user:

> These are not installed. When you are ready for one, run `/awow-add <command>`.

Update `setup-progress.md` to mark all steps surfaced.

## Step 9 — Skills review (keep / customise / drop)

The starter pack ships several skills under `.agents/skills/`. Each is opinionated about *some* part of the stack — harness session format, tracing backend, rubric — and will not fit every team out of the box. This step walks the user through each shipped skill once they have enough context to make a call.

For each entry in `.agents/skills/` (read the directory; both declarative `<name>.md` files and operational `<name>/SKILL.md` directories):

1. Read the skill's frontmatter `description` and the first body paragraph. Summarise in one sentence.
2. Identify the **specific assumption** the skill bakes in (e.g. *"assumes Databricks MLflow"*, *"reads Claude Code JSONL"*, *"uses our story template"*). The "Starter shape — adjust for ..." callout at the top of each shipped operational skill states this directly; quote it.
3. Ask the user one question:

   > **`<skill>`** — keep as-is, customise to your stack, or drop?
   >
   > Bakes in: <assumption>. Used by: <commands or other skills that depend on it, from the SKILL.md "Interplay" section>.

4. Apply the user's answer:
   - **Keep** — no change.
   - **Customise** — open the SKILL.md and the bundled scripts. Draft the changes under `proposals/setup/step-9/<skill>/` first (full proposal-first treatment). Common customisations to surface as concrete options:
     - **mlflow-export** — swap the exporter script for the team's tracing backend (LangSmith, Helicone, OTLP, raw JSONL). The downstream skills consume the JSON layout documented in `mlflow-export/SKILL.md`; match that shape or update the consumers too.
     - **prompt-skill-analysis** — add a parser for the team's harness session format (Copilot, Cursor, etc.). The rubric is harness-agnostic; only the input branch needs work.
     - **awow-usage-coach** — adjust the intent taxonomy if the team's vocabulary doesn't fit; otherwise rely on the harness-agnostic `working_directory` + `files_modified` lenses.
     - **user-story-template** — replace with the team's own template if it differs from the seeded shape.
   - **Drop** — `git rm -r` the skill directory or file. Note in `setup-progress.md` so a re-run of `/setup-awow` doesn't keep re-offering it.

5. If the user wants to **add** a new skill that isn't in the starter pack, point at `.agents/skills/README.md` ("When to write a skill") and offer to scaffold one — either a declarative `<name>.md` or an operational `<name>/SKILL.md` with a `scripts/` directory.

Update `setup-progress.md` to mark Step 9 complete (record per-skill decisions inline so the next session has context).

**Re-run this step whenever the stack changes** — new harness, new tracing backend, new shared rubric. Skills review is not a one-shot.

## Quickest-quickstart (alternative)

If the user invokes `/setup-awow --quickstart`, do Steps 0 → 1 → 2 → 4 in one turn against the user's responses, with sensible defaults for everything not asked about. This is the one-shot path for users who already know what they want and don't need the wizard. The conversational wizard remains the default.

## Proposal-first

Every artefact lands first under `proposals/setup/<step>/<file>.md`. The user reviews. Only after explicit approval does the wizard move the artefact to its final location. This is the proposal-first principle from `input/PROPOSAL.md` §3. Do not bypass it.
