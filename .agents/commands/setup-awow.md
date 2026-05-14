---
phase: kickoff
prerequisites: []
removes_pain: "the I-cloned-the-repo-now-what-do-I-do problem"
---

# /setup-awow — incremental, resumable bootstrap

You are the setup wizard for the agentic way of working starter pack. Your job is to walk the user through configuring this repo so the agent can operate against their team's board and context.

The wizard is **incremental and resumable.** State lives in `setup-progress.md` at the repo root. Read it on every invocation. Only **Step 0** is required for the repo to be usable. All subsequent steps are recommended-next, in any order.

## Prerequisite — shell-level install

Before this command runs, the user should have executed `./setup/install.sh` (macOS / Linux) or `.\setup\install.ps1` (Windows / PowerShell) from the repo root. That installer wires up Python via `uv`, creates `.venv`, and runs the initial `tools/gather.py` so the harness can discover this very command.

On invocation, sanity-check the prerequisite: `.venv/` exists at the repo root, and the harness surfaces (`.claude/commands/`, `.github/prompts/`) contain pointer stubs. If either is missing, tell the user to run the installer first and stop — do not try to recover by running gather yourself, because the user may simply not have `uv` available yet, and the installer's error message is the right place to learn that.

## On every invocation

1. Read `setup-progress.md`.
2. Determine which steps are complete, deferred, or untouched.
3. If Step 0 is not complete, do Step 0 next. Otherwise offer the recommended next step and let the user pick.
4. Write every artefact to `proposals/setup/<step>/` first. Land it (move to its final location) only after the user approves.
5. Update `setup-progress.md` when a step completes.

## Step 0 — Kickoff (REQUIRED)

The outcome of Step 0 is a **wired-up board MCP** plus a recorded `context/tooling/board.md`. The board URL is collected along the way, but it is not the headline — the MCP is. Detect first, ask second.

1. **Establish harness.** The starter pack ships both `.claude/` and `.github/` directories, so their presence is not a signal — do **not** infer "both harnesses in use" from directory listing alone. The real signal is which harness you (the model) are currently running inside:
   - If you are Claude Code, the user's current harness is Claude Code.
   - If you are GitHub Copilot, the user's current harness is Copilot.

   Tell the user: "I can see I'm running in `<current harness>`. Does your team also use `<the other one>`, or is `<current>` the only harness to wire up?" Accept one of: *current only*, *both*. Record the choice; this drives which install snippets you surface in step 4.

2. **Detect existing board MCP.** Look for an MCP server entry whose name or URL references a supported board tool (`linear`, `jira`, `azure`, `github`) in:
   - `.claude/settings.json` and `.claude/settings.local.json`
   - `.mcp.json` at the repo root
   - `.github/copilot-instructions.md` (MCP block) and `.vscode/mcp.json`

   If you find one:
   - Read the workspace / team identifier from the config.
   - Verify read access with a single MCP call (e.g. `list_issues` or equivalent).
   - Tell the user what you found and ask them to confirm or paste the canonical board URL (used for `context/tooling/board.md` and so the wizard can surface team-page links later). Then skip to step 5.

3. **No MCP wired yet — ask for the board URL.** Tell the user you need the URL for two reasons: (a) to know which MCP to install, (b) to extract the workspace / team identifier that the MCP itself requires for config. Refuse to continue without one. Infer the tool family from the URL hostname:
   - `linear.app` → Linear
   - `dev.azure.com` or `*.visualstudio.com` → Azure DevOps
   - `*.atlassian.net` → Jira
   - `github.com/.../issues` → GitHub Issues
   - Anything else → tell the user the tool is not supported and stop.

4. **Install and verify the MCP.** Load `context/tooling/boards/<tool>.md` and read its `## MCP` section. That section is structured as: **Source docs** link, **Install — Claude Code** snippet, **Install — Copilot** snippet, **Verify** checklist. The two harnesses get different config (CLI command vs. `.vscode/mcp.json` JSON), so:
   - Pick the install snippet that matches the harness recorded in step 1. If the user confirmed they use both, surface both — they will need to wire each.
   - Surface the **Source docs** URL first and tell the user it is authoritative: the snippet in the reference is a summary and may have drifted from upstream.
   - Print the exact install command (or JSON snippet) for the user to run / paste. Configure it using the workspace / team identifier extracted from the URL where applicable.
   - Verify read access with a single MCP call (e.g. `list_issues` or equivalent).
   - Verify write access with a **no-op** write against a scratch issue (e.g. set the description to its current value). If write access is not granted yet, surface that as a blocker — the agent cannot do its job read-only.
   - If the user cannot complete the install in this session (token in another browser, IT ticket, etc.), record the MCP as `pending` in `setup-progress.md` and continue with the rest of Step 0 so the repo is at least partially usable.

5. **Record.** Draft `context/tooling/board.md` with: tool family, board URL, MCP server name, workspace / team identifier, MCP verification status (`read-ok`, `write-ok`, or `pending`), harness choices. Land it under `proposals/setup/step-0/board.md` first. Wait for user approval. Move to `context/tooling/board.md` once approved.

6. Update `setup-progress.md` to check off Step 0 (note any `pending` MCP so the next invocation re-offers the install).

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
