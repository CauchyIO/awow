---
description: "incremental, resumable bootstrap"
phase: kickoff
prerequisites: []
removes_pain: "the I-cloned-the-repo-now-what-do-I-do problem"
channel: vendored
---

# /setup-awow — incremental, resumable bootstrap

You are the setup wizard for the agentic way of working starter pack. Your job is to walk the user through configuring this repo so the agent can operate against their team's board and context.

The wizard is **incremental and resumable.** State lives in `setup-progress.md` at the repo root. Read it on every invocation. **Step 0** (installer) and **Step 1** (kickoff) are required for the repo to be usable. All subsequent steps are recommended-next, in any order.

If invoked as `/setup-awow --root <path>`, resolve every path in this prompt — `setup-progress.md`, `proposals/setup/`, `context/` — relative to `<path>/` instead of the repo root. Default: repo root. Use `--root` for multi-workspace runs; for example, the maintainer running the wizard against `meta/` from a repo that already has its own top-level `setup-progress.md`.

Two surfaces stay at the repo root regardless of `--root`: the harness infrastructure (`.venv/`, `.agents/`, `.claude/`, `.github/`) and the installer at `setup/install.sh`. Step 0's detection logic explicitly inherits the parent repo's installer state when `--root` is set — there is no separate installer per workspace.

If `--root <path>` is given and `<path>/` does not exist, refuse and tell the user to create it first (`mkdir -p <path>`).

## On every invocation

1. Read `setup-progress.md`.
2. **Lay out the full plan to the user before doing anything else.** List every step (0 → 9), mark each as ✓ complete, ⧗ deferred/pending, or ☐ untouched, and tell the user which step you are about to resume. The user should see the whole map on every entry — never present a single step in isolation.
3. Walk through the steps in order until Step 0 and Step 1 are both complete. After that, offer the recommended next step and let the user pick.
4. Write every artefact to `proposals/setup/<step>/` first. Land it (move to its final location) only after the user approves.
5. Update `setup-progress.md` when a step completes.

## Track — solo or team

On first entry (no `track:` recorded in `setup-progress.md`), ask once: "Is this for a whole team, or just you?" Record the answer as `track: team` or `track: solo`. In **solo** mode, skip the steps that only make sense for a group and mark them as skipped when you lay out the plan:

- **Step 4 members** — skip; the roster is just the user. Still draft the style files, since they shape every artefact.
- **Step 7 neighbouring teams** — skip; there are no 1° teams to stub.

Reframe **Step 2** as the user's focus for the work, not a team charter. Everything else runs unchanged. A solo adopter can switch later by re-running `/setup-awow` and answering "team".

## Step 0 — Installer (REQUIRED)

The starter pack uses `tools/gather.py` to mirror `.agents/` into the harness surfaces (`.claude/`, `.github/`). The installer wires Python via `uv`, creates `.venv`, and runs `gather.py` once so the harness can discover this very command.

1. **Detect.** Run a cheap two-file probe — do not scan further:
   - `.claude/commands/setup-awow.md` present? (signals `gather.py` has run, i.e. stubs are populated)
   - `.venv/` present at repo root? (signals the Python env is wired)

   Three cases:
   - **Both present.** Step 0 is already complete. Skip to step 5.
   - **Stubs present, `.venv/` missing.** Gather has already run, only the venv needs restoring. Tell the user you will run `uv sync --python 3.12` (not the full installer) and ask for explicit confirmation. Once confirmed, run it and skip to step 4.
   - **Stubs missing.** Continue to step 2 for the full installer.

   When invoked with `--root <path>`, both probes still inspect the *repo root* (not `<path>/`); the installer is shared, not duplicated per workspace. Record the inheritance in `<path>/setup-progress.md` so future invocations know Step 0 was satisfied transitively.
2. **Request permission.** Tell the user you are about to run the platform-appropriate installer on their behalf (`./setup/install.sh` on macOS / Linux, `.\setup\install.ps1` on Windows / PowerShell) and ask for explicit confirmation before invoking the shell. Do not run it silently.
3. **Run.** Once confirmed, execute the installer and surface its output verbatim. If it fails — most commonly because `uv` is not on PATH — surface the error and tell the user to install `uv` (`brew install uv` on macOS, or follow uv's installation docs) and then re-invoke `/setup-awow`. Do not try to recover by running `tools/gather.py` under system Python; the installer's error message is the right place to learn what is wrong.
4. **Verify.** Confirm `.venv/` exists and that `.claude/commands/setup-awow.md` and `.github/prompts/setup-awow.prompt.md` are present.
5. Mark Step 0 complete in `setup-progress.md` and continue to Step 1.

## Step 1 — Kickoff (REQUIRED)

The outcome of Step 1 is a **wired-up board read/write surface** plus a fully-populated `context/tooling/board.md` that specifies this team's board — state machine, hierarchy, label taxonomy, fields, team-page conventions — not just the MCP wiring. The agent reads `board.md` thereafter whenever it needs to know what a label means, which states are terminal, or where in the hierarchy a new issue belongs.

Step 1 has two parts. Step 1a wires up the read/write surface (an MCP or, for GitHub, the `gh` CLI). Step 1b walks the team through configuration — either **Mode A** (set up from the reference for greenfield / under-configured boards) or **Mode B** (assess and capture current state for already-running boards). The choice is automatic, driven by counting closed issues.

### Step 1a — Wire the read/write surface

1. **Establish harness.** The starter pack ships both `.claude/` and `.github/` directories, so their presence is not a signal — do **not** infer "both harnesses in use" from directory listing alone. The real signal is which harness you (the model) are currently running inside:
   - If you are Claude Code, the user's current harness is Claude Code.
   - If you are GitHub Copilot, the user's current harness is Copilot.

   Tell the user: "I can see I'm running in `<current harness>`. Does your team also use `<the other one>`, or is `<current>` the only harness to wire up?" Accept one of: *current only*, *both*. Record the choice; this drives which install snippets you surface in step 4.

2. **Detect existing board surface.** Look for an existing MCP server entry whose name or URL references a supported board tool (`linear`, `jira`, `azure`, `github`) in:
   - `.claude/settings.json` and `.claude/settings.local.json`
   - `.mcp.json` at the repo root
   - `.github/copilot-instructions.md` (MCP block) and `.vscode/mcp.json`

   For GitHub-hosted boards also check whether `gh auth status` shows an authenticated CLI with `repo`, `project`, and `read:org` scopes — that is the `gh` CLI alternative documented in `context/tooling/boards/github-issues/reference/mcp.md`. If `gh` is authenticated for the right org, treat it as a valid surface and offer it alongside the MCP option.

   If you find an existing surface:
   - Read the workspace / team identifier from the config.
   - Verify read access with a single call (`list_issues` or `gh repo view`).
   - Tell the user what you found and ask them to confirm or paste the canonical board URL (used for `board.md` and so the wizard can surface team-page links later). Then skip to step 5.

3. **No surface wired yet — ask for the board URL.** Tell the user you need the URL for two reasons: (a) to know which surface to install, (b) to extract the workspace / team identifier that the surface itself requires for config. Refuse to continue without one. Infer the tool family from the URL hostname:
   - `linear.app` → Linear
   - `dev.azure.com` or `*.visualstudio.com` → Azure DevOps
   - `*.atlassian.net` → Jira
   - `github.com/.../issues` or `github.com/orgs/<org>/projects/<n>` → GitHub Issues + Projects
   - Anything else → tell the user the tool is not supported and stop.

4. **Install and verify the read/write surface.** Load `context/tooling/boards/<tool>/reference/mcp.md` (the same file the per-tool `<tool>/README.md` indexes). That file is structured as: **Source docs** link, **Install — Claude Code** snippet, **Install — Copilot** snippet, **Verify** checklist; for GitHub it also includes the **`gh` CLI alternative**. Then:
   - Pick the install snippet that matches the harness recorded in step 1. If the user confirmed they use both, surface both — they will need to wire each.
   - Surface the **Source docs** URL first and tell the user it is authoritative: the snippet in the reference is a summary and may have drifted from upstream.
   - For GitHub, ask whether the user prefers the MCP (full-feature, PAT-managed) or the `gh` CLI (lighter; reuses existing auth). Record the choice as `surface: mcp` or `surface: gh-cli`.
   - Print the exact install command (or JSON snippet) for the user to run / paste. Configure it using the workspace / team identifier extracted from the URL where applicable.
   - Verify read access with a single call.
   - Verify write access with a **no-op** write against a scratch issue (set the description to its current value, or re-add an existing label). If write access is not granted yet, surface that as a blocker — the agent cannot do its job read-only.
   - If the user cannot complete the install in this session (token in another browser, IT ticket, etc.), record the surface as `pending` in `setup-progress.md` and continue with Step 1b so the repo is at least partially usable; mark configuration items that depend on write access as `pending-write`.

### Step 1b — Board configuration (from reference or assess current)

The reference for this team's board lives at `context/tooling/boards/<tool>/reference/`. The wizard reads it section by section and walks the team through either configuring from it (Mode A) or capturing what's already there (Mode B).

5. **Pick mode by counting closed issues.** Use the surface to count closed (or `Done`) issues on the team's board. The threshold is **10 closed issues**: at or above, run Mode B; below, run Mode A. Surface the count and the chosen mode to the user before proceeding:

   > "I see **<n>** closed issues on this board. **<n> < 10**, so I'm running **Mode A — Set up from reference**. I will walk you through each section of the reference and ask you to accept, override, or skip."
   >
   > _or_
   >
   > "I see **<n>** closed issues on this board. **<n> ≥ 10**, so I'm running **Mode B — Assess and capture current**. I will pull what is actually on the board, write it to `board.md` under the same section headings the reference uses, and surface any divergence so you can decide what to close, override, or accept."

   If the count cannot be obtained (e.g. surface is `pending`), default to Mode A and note the deferral.

6. **Tell the user which reference layer is in use.** Before walking any section, check for an enterprise override at `.agents-overrides/tooling/boards/<tool>/reference/`. If it exists, that layer supersedes the starter pack's reference per file. Tell the user explicitly, e.g.:

   > "Reading from `.agents-overrides/tooling/boards/linear/reference/labels.md` (enterprise override) for the label taxonomy; everything else is from the starter pack."

   Repeat this preamble whenever the source layer changes for the next section.

7. **Walk the reference sections in order.** For each file under `<tool>/reference/` (`states.md`, `hierarchy.md`, `labels.md`, `fields.md`, `team-page.md`, `mcp.md` already covered in Step 1a, `cycles.md` / `iterations.md` if present):

   - **Mode A.** Read the reference file. Summarise its decisions to the user. For each decision the reference asks the wizard to surface, ask **accept / override / skip**. Where the surface supports mutation (Linear MCP can create labels; `gh` can edit Project fields), apply the accepted choices. Where it does not (Linear Free workflow states, ADO process templates, Jira project workflows), emit a step-by-step manual checklist for the user to run in the board UI and re-verify after the user confirms. Skipped decisions land in `board.md` as `skipped: <reason>`.
   - **Mode B.** Read the same reference file for its `## What lands in board.md` shape. Pull the current state from the surface (workflow statuses, labels in use, native fields, team page contents). Write it to the corresponding `board.md` section. Diff against the reference; populate the `## Divergence from reference` section of `board.md` with each gap and the user's resolution (`close`, `override`, `accept`).

   Land each section's draft under `proposals/setup/step-1/board.md` incrementally — append, do not overwrite — and keep the user in the loop after each section. Do not silently progress through all sections without stopping; one section per agent turn is fine.

8. **Update labels.md to match reality.** If Mode B surfaces label names that diverge from the reference (e.g. team uses `bug` instead of `type:bug`), update `context/team/conventions/REQUIRED/labels.md` to reflect what is actually on the board, so future agent proposals match the team's reality. Draft the update under `proposals/setup/step-1/labels.md` and ask the user to approve before landing.

### Record and complete

9. **Final board.md.** When all sections are drafted, the file shape under `proposals/setup/step-1/board.md` is:

   ```
   # Board — <team name>

   ## Tool & wiring          # tool family, URL, surface (MCP or gh-cli), identifier, verification, harness choices
   ## State machine
   ## Hierarchy
   ## Label taxonomy
   ## Required fields
   ## Avoiding duplicates    # the tool's dedup limits + the team's search-before-create recipe (from reference/duplicates.md)
   ## Team page conventions
   ## Cycles / iterations    # if applicable for this tool
   ## Divergence from reference   # populated by Mode B; empty for Mode A
   ```

   Ask the user for final approval. Move to `context/tooling/board.md` once approved.

10. **Review-and-adjust gate.** With `context/tooling/board.md` now in place, do **not** silently move on. Read the landed file back, summarise it to the user in a few bullets — surface (MCP / `gh` CLI / pending), state-machine mapping, hierarchy levels in use, label prefixes, fields in use, and any `## Divergence from reference` entries — and ask:

    > "`context/tooling/board.md` is in place. Want me to adjust or evaluate any section before moving on, or are you happy with this and we proceed?"

    Accept one of:
    - **Proceed.** Continue to step 11.
    - **Adjust `<section>`.** Re-enter Step 1b for that section only. Re-walk it in Mode A or Mode B (whichever was used originally; the user can switch), update the draft under `proposals/setup/step-1/board.md`, ask for approval, replace the corresponding section of `context/tooling/board.md`, then return to this gate.
    - **Evaluate `<section>`.** Re-pull the live board state for that section via the surface, diff it against what is in `board.md`, surface differences, and ask the user whether to update `board.md` or leave as-is. Return to this gate.

    Loop on the gate until the user says proceed. Do not skip the gate even if the user approved the final draft in step 9 — the file existing on disk changes the question from "is this draft good enough to land?" to "now that it is the source of truth, does it still represent the team?".

11. Update `setup-progress.md` to check off Step 1. Record:
    - The mode used (A or B).
    - Any `pending` items (surface install, manual board-UI checklists, label normalisation).
    - The reference layer used per section (starter pack vs. enterprise override).
    - Any sections the user re-walked or evaluated at the gate (so a later session has the audit trail).

After Step 1, tell the user:

> The repo is usable and the board is documented. You can stop here and start using `/refinement-prep` on a real story, or continue with `/setup-awow` to fill in mission, conventions, members, and knowledge base. Each step is a few minutes; none are required.

## Step 2 — Mission

Ask: "What is your team's mission, in one sentence?"

Refuse anything trivial ("be excellent", "ship great software"). A useful mission names the audience, the change being made, and the constraint. Iterate with the user until you have a sentence both of you would put a name to.

Land at `context/team/mission.md` via `proposals/setup/step-2/mission.md`. Update `setup-progress.md`.

## Step 3 — Required conventions (observe or guide)

For each of the four REQUIRED conventions (`issue-titles.md`, `labels.md`, `branches.md`, `output-discipline.md`):

- If the board has ≥10 closed issues, **observe**: query the board, summarise the existing pattern, and draft the convention to match. Show the user three real examples from their board so they can confirm. `labels.md` may already have been drafted in Step 1b (Mode B); reuse that draft and extend it with the rules.
- If the board is greenfield (<10 issues), **guide**: propose sensible defaults from `context/tooling/boards/<tool>/reference/`. Let the user opt out of any rule that does not fit.

`output-discipline.md` is non-negotiable. If the user objects, explain why (the agent over-produces without it). Iterate on the rules, do not skip the file.

Land each under `proposals/setup/step-3/<convention>.md`, get approval, move to `context/team/conventions/REQUIRED/<convention>.md`. Update `setup-progress.md`.

**Session-board correlation (opt-in).** Ask whether the team wants agent-authored board entries linked back to their session traces. If **yes**, first run the `session-correlation` skill's prerequisite check: tracing must already be wired (`MLFLOW_CLAUDE_TRACING_ENABLED=true` plus the MLflow `Stop` hook in `.claude/settings.local.json`). This skill does **not** set tracing up — if it is missing, stop and point the user at the team's `claudetracing` library (`../claudetracing`) to configure tracing first, then resume. Once tracing is confirmed: install the footer rule from the skill — append its Rule 4 to `output-discipline.md` here, add its shape note to `board-output.md` in Step 4, and wire the SessionStart accessor hook per the skill's "Enabling it" steps. The rule then flows into the generated `CLAUDE.md` at Step 5 and is enforced from then on. If **no**: leave all three untouched; the skill stays available to enable later via `/awow-add`. Record the choice in `setup-progress.md`.

## Step 4 — Members and style

Ask for the team member list (role, responsibilities, focus areas). If members are listed in the board's team page, offer to pull from there.

Draft `context/team/style/board-output.md`, `comments.md`, `placement.md`, `prose.md` from the reference templates, customising only where the user pushes back.

## Step 5 — CLAUDE.md / AGENTS.md bootstrap

Run `tools/bootstrap-claude-md.py` (or the inline equivalent). It reads the stub at `.agents/AGENTS.md` plus every file the wizard has produced so far and writes a team-specific `CLAUDE.md`.

Critically: ask the user to populate the `## Do not propose` block. Surface scope-shedding statements ("we are not adding multi-user this quarter", "do not propose moving away from Linear"). Land the result. Run `tools/gather.py` to mirror to `.claude/CLAUDE.md` and `.github/AGENTS.md`.

## Step 6 — Knowledge base seed

Walk the user through `context/knowledge-base/README.md` — what lives there vs. on the board. Offer to seed `glossary.md` from any glossary they already have. Stub the architecture/patterns/runbooks/decisions subfolders with one example each if useful.

**The capture → synthesize spine.** Explain how durable knowledge gets *in*, so the KB isn't a folder nobody fills:

- **Capture.** Mining a day's activity (`/kb-mine`, or `/daily-routine` Phase 3) stages candidates as committed files in `context/kb-inbox/` — one durable insight per file. Point the user at `context/kb-inbox/README.md`.
- **Tune.** What mining keeps is governed by `context/knowledge-base/mining-policy.md`. Show its frontmatter dials (`selectivity`, `categories`, the two caps). It ships strict (`selectivity: 2`); ask whether the team wants to start more generous, and adjust the one value if so. This is the only knob they need to touch.
- **Synthesize.** Draining the inbox into the durable KB is `/kb-synthesize` (per `context/knowledge-base/synthesis.md`) — **human-gated by default** (novel → write, matches → annotate, covered → no-op, thin → drop). Make clear no autonomous write path ships; unattended nightly drain is opt-in and out of the box.

**Locations (optional).** The two KB folders — `kb_root` (default `context/knowledge-base/`) and `inbox` (default `context/kb-inbox/`) — are declared in `context/tooling/knowledge-base.md`. Ask whether the team wants them elsewhere (e.g. a top-level `docs/kb/`, or an existing wiki/vault path). If **yes**: update the two paths in that config **and move the folders to match** (`git mv` the existing `context/knowledge-base/` and `context/kb-inbox/` contents). The contracts and commands resolve locations from the config, so nothing else needs editing. If **no**, leave the defaults. Keep the two folders distinct — the drain moves files from `inbox` into `kb_root`.

Nothing is required here — the spine works on its defaults. The only optional knobs are the `selectivity` dial and these two paths. Record in `setup-progress.md` whether the default policy and locations were kept or adjusted.

## Step 7 — Neighbouring teams

Ask for the 1° teams (teams whose work the user's team depends on or supplies into). Generate empty stubs at `context/company/neighbouring-teams.md`. Tell the user each neighbouring team is expected to write its own; the stubs are placeholders.

## Step 8 — Surface the extras

Read the commands in `.agents/commands/` whose frontmatter declares `phase: spread` or `phase: standardise`. List each command, its phase, its prerequisites, and the pain it removes. Tell the user:

> These are not installed. When you are ready for one, run `/awow-add <command>`.

**Design system (detect, then suggest).** Read `context/tooling/design-system.md`.

- If `mode:` is not `absent`, a design system is already configured — name its `path:` and move on; do not re-offer.
- If `mode: absent`, ask one question: *"Does your team produce styled HTML artifacts — decks, blogs, solution designs, one-pagers?"* If **yes**, recommend the add-on flow: *"Run `/awow-add design-system` (or `/design-system` directly) to stand one up or point at an existing one. Until then, HTML artifacts use plain defaults."* Do not run it now — it is opt-in. If **no**, leave the pointer at `absent`.

Record the answer (and any configured `path:`) in `setup-progress.md`.

**Build engine (detect, then suggest).** awow owns the outer loop (board, planning, landing) and hands the *build* step to an optional inner-loop engine. Detect whether one is installed by checking for a `superpowers` directory under `~/.claude/plugins/cache/*/`, `~/.claude/plugins/*/`, or this repo's `.claude/plugins/*/`.

- **Found** — an engine is configured; name it and move on. The `board-aware-development` seam (skill + PreToolUse reminder) is already active. If this team also keeps an architecture plane (ADRs / design records / pattern notes) reachable by a KB agent, offer to write a `context/tooling/architecture.md` pointer (draft it to `proposals/setup/step-8/` first, approve, then land it) — that switches on the parallel `architecture-aware-development` seam. No plane → skip it; the seam stays dormant.
- **Not found** — recommend it as **optional**: *"awow hands the build step to an inner-loop engine. superpowers adds TDD-gated build → review and lights up the board-aware-development seam (and the architecture-aware-development seam, when a `context/tooling/architecture.md` plane is present). Install it with `/plugin` from the `claude-plugins-official` marketplace. This is optional — awow runs on its baseline build guidance without it."* Do not install it for the user, and never make it required. Note that spec-kit is an alternative engine (spec-first rather than test-first) for teams who prefer it.

This is a soft dependency by design — see `proposals/superpowers-integration-plan.md`. Do not add it to the plugin manifest's `dependencies`; that would force-install it on every adopter and couple awow across marketplaces.

Record the choice (engine name, or "none — declined") in `setup-progress.md`.

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
   - **Customise** — open the SKILL.md and the bundled scripts. Draft the changes under `proposals/setup/step-10/<skill>/` first (full proposal-first treatment). Common customisations to surface as concrete options:
     - **mlflow-export** — swap the exporter script for the team's tracing backend (LangSmith, Helicone, OTLP, raw JSONL). The downstream skills consume the JSON layout documented in `mlflow-export/SKILL.md`; match that shape or update the consumers too.
     - **prompt-skill-analysis** — add a parser for the team's harness session format (Copilot, Cursor, etc.). The rubric is harness-agnostic; only the input branch needs work.
     - **awow-usage-coach** — adjust the intent taxonomy if the team's vocabulary doesn't fit; otherwise rely on the harness-agnostic `working_directory` + `files_modified` lenses.
     - **user-story-template** — replace with the team's own template if it differs from the seeded shape.
   - **Drop** — `git rm -r` the skill directory or file. Note in `setup-progress.md` so a re-run of `/setup-awow` doesn't keep re-offering it.

5. If the user wants to **add** a new skill that isn't in the starter pack, point at `.agents/skills/README.md` ("When to write a skill") and offer to scaffold one — either a declarative `<name>.md` or an operational `<name>/SKILL.md` with a `scripts/` directory.

Update `setup-progress.md` to mark Step 9 complete (record per-skill decisions inline so the next session has context).

**Re-run this step whenever the stack changes** — new harness, new tracing backend, new shared rubric. Skills review is not a one-shot.

## Quickest-quickstart (alternative)

If the user invokes `/setup-awow --quickstart`, do Steps 0 → 1 → 2 → 3 → 5 in one turn against the user's responses, with sensible defaults for everything not asked about. Step 0 (installer) still requests permission before running the shell script; the rest skips the per-step review loop. This is the one-shot path for users who already know what they want and don't need the wizard. The conversational wizard remains the default.

## Proposal-first

Every artefact lands first under `proposals/setup/<step>/<file>.md`. The user reviews. Only after explicit approval does the wizard move the artefact to its final location. This is the proposal-first principle from `input/PROPOSAL.md` §3. Do not bypass it.
