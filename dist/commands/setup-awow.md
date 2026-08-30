---
description: "Use when a repo has awow files but no board wiring or team context yet, or the user asks how to get started with awow, connect their issue board, or resume an unfinished setup."
phase: kickoff
prerequisites: []
removes_pain: "the I-cloned-the-repo-now-what-do-I-do problem"
channel: bootstrap
consumes: transcript
when-to-use: "The transcript is a team setup or ways-of-working workshop covering mission, work flow, recurring rituals, working agreements, ownership, or awow configuration."
when-not-to-use: "The transcript is an ordinary refinement, standup, planning session, retrospective, interview, or design discussion rather than a deliberate setup conversation."
---

# /setup-awow — incremental, resumable bootstrap

You are the setup wizard for the agentic way of working starter pack. Your job is to walk the user through configuring this repo so the agent can operate against their team's board and context.

The wizard is **incremental and resumable.** State lives in `setup-progress.md` at the repo root. Read it on every invocation. **Step 0** (installer) and **Step 1** (kickoff) are required for the repo to be usable. All subsequent steps are recommended-next, in any order.

If invoked as `/setup-awow --root <path>`, resolve every path in this prompt — `setup-progress.md`, `proposals/setup/`, `context/` — relative to `<path>/` instead of the repo root. Default: repo root. Use `--root` for multi-workspace runs; for example, authoring a test fixture workspace under `tests/fixtures/` from a repo that already has its own top-level `setup-progress.md`.

Two surfaces stay at the repo root regardless of `--root`: the harness infrastructure (`.venv/`, `.agents/`, `.claude/`, `.github/`) and the installer at `setup/install.sh`. Step 0's detection logic explicitly inherits the parent repo's installer state when `--root` is set — there is no separate installer per workspace.

If `--root <path>` is given and `<path>/` does not exist, refuse and tell the user to create it first (`mkdir -p <path>`).

## On every invocation

1. Read `setup-progress.md`.
2. Run the **Preflight** (next section). A fatal miss stops here — print the pointer instead of
   the step map. Soft misses annotate the step map below.
3. **Lay out the plan to the user before doing anything else.** The map has two parts. First the required core — Step 0 (installer), Step 1 (board), and, for an anchored repo, registration — each marked ✓ complete, ⧗ deferred/pending, or ☐ untouched, naming the step you are about to resume. Then one compact line for the deferred fills (profile, conventions, members + style, KB seed, neighbouring teams, extras — §Deferred fills), with a ✓ per fill already landed. Never walk a deferred fill proactively. Keep the whole map compact when the user chose the workshop route.
4. On first entry, offer the workshop and guided routes described below. Walk through the steps in order until Step 0 and Step 1 are both complete on the guided route. On the workshop route, prepare or process the workshop first, then return to uncovered steps and technical wiring.
5. Write every artefact to `proposals/setup/<step>/` first. Land it (move to its final location) only after the user approves.
6. Update `setup-progress.md` when a step completes.

## Preflight — verify prerequisites, change nothing

Run these checks on every invocation, immediately after reading `setup-progress.md` and before
laying out the step map. Preflight is read-only. Never install anything, never register an MCP
server, never run `git init`, never write any file — `setup-progress.md` included. Report, point
at the fix, and gate. Probe in the non-failing style (`cmd && echo ok || echo missing`); never
`cat` a possibly-absent file. Re-probe every invocation; never persist a result — recorded auth
status lies. When the current harness is Visual Studio, do not shell out at all — VS
approval-gates terminal commands, and the preflight must not become a stream of permission
prompts. Probe only what file reads answer (the bridge marker, the config files, candidate
enumeration), render shell-dependent checks as `– (not checkable from Visual Studio)`, and tell
the user to run `/setup-awow` in a Copilot CLI session for the full preflight.

1. **git on PATH.** `git --version >/dev/null 2>&1 && echo ok || echo missing`. Missing: print
   the install pointer for the user's platform — macOS: `xcode-select --install` or
   `brew install git`; Windows: `winget install --id Git.Git` (or `choco install git` where the
   team already uses chocolatey); Linux: the distro package manager, else
   https://git-scm.com/downloads — and stop. Print nothing else — no step map, no steps.
2. **The workspace is a git repository.** `git -C <root> rev-parse --is-inside-work-tree
   2>/dev/null || echo no`, where `<root>` is the repo root, or the `--root` path when given.
   Not a repo: tell the user to run `git init` in `<root>` or cd to the repository they meant,
   and stop as in check 1. Do not offer to run `git init` yourself.
3. **Board surface.** Enumerate candidates: MCP entries referencing a supported board tool
   (`linear`, `jira`, `azure`, `github`) in `.mcp.json`, `.claude/settings.json`,
   `.claude/settings.local.json`, `.vscode/mcp.json` — all relative to `<root>` — plus board
   MCP tools already loaded in your own tool surface; when the recorded harness roster names
   Copilot CLI or Visual Studio, also `~/.copilot/mcp-config.json` and `~/.mcp.json`. Identify
   each as server name + endpoint (URL, or command line for stdio) + provenance (which file or
   scope). Then classify into exactly one state:
   - **n/a** — nothing recorded in `setup-progress.md`, no candidates → render
     `board – (wired in Step 1a)`.
   - **unconfirmed** — nothing recorded, candidates exist → list each as
     `<name> — <endpoint> (from <provenance>)`, say confirmation happens at Step 1a, and use
     none of them meanwhile.
   - **ok** — a recorded `board-mcp:` identity matches a loaded server *by name* and one
     identity-bearing read succeeds. Loaded tools expose a server's name only — never its
     endpoint, account, or workspace — so a name match proves nothing on its own; the read must
     return the board the recorded `board-url:` names (else `board.md` §Tool & wiring): Linear —
     `list_teams` contains the team key in the URL; Jira — the project key resolves; Azure
     DevOps — the org/project resolves; GitHub — the repo resolves. A bare "list anything" call
     is not verification. For `surface: gh-cli`: check 4 passes and `gh repo view <owner/repo>`
     on the recorded repo succeeds.
   - **blocked** — a recorded identity this session cannot use. Name the reason and fix, one
     line: *not loaded but configured in `<file>`* → "restart or run `/mcp`"; *not configured
     anywhere here* → "registered at another scope or machine — re-add with `claude mcp add
     --scope user --transport http <name> <endpoint>`, or commit a project `.mcp.json`";
     *unauthenticated* → "run `/mcp` to authenticate" (or the harness-appropriate re-auth);
     *wrong workspace* (a server with the recorded name is loaded and answers, but the identity
     read does not return the recorded team/project/repo) → "`<name>` is loaded but serves
     `<what it returned>`, not `<recorded>` — re-authenticate it (`/mcp`, or the harness
     equivalent) or re-confirm at Step 1a"; *unverifiable* (no `board-url:` recorded and no
     `board.md` to fall back on) → "identity cannot be proven — re-run Step 1a to record the
     board URL"; *diverged* (live candidates, none matching the recorded endpoint) → list them
     with provenance and say re-confirmation happens at Step 1a. Never silently adopt or switch.
4. **gh CLI — GitHub-family boards only.** When the recorded surface is `gh-cli`, or the
   recorded or in-progress board URL is GitHub-hosted: `gh --version`, then `gh auth status`,
   then confirm scopes `repo`, `project`, `read:org`. Pointers per miss, matched to the user's
   platform: install `brew install gh` (macOS) / `winget install --id GitHub.cli` (Windows) /
   https://cli.github.com (elsewhere); `gh auth login`; `gh auth refresh -s
   repo,project,read:org`. Never render this check for other board families.
5. **Current-harness wiring.** You know which harness you are running in. Claude Code: nothing
   to check — the plugin delivered this command. Copilot CLI: `copilot` on PATH — miss points at
   the Copilot CLI install docs. Copilot in VS Code: `.vscode/mcp.json` present when the surface
   is MCP — miss points at the Step 1a install snippet. Visual Studio (and any roster that names
   it): VS never reads the plugin store, so check the bridge chain — `copilot` on PATH, the awow
   plugin at `~/.copilot/installed-plugins/awow/`, and the bridge marker
   `~/.copilot/skills/.awow-bridge.json` present with a version equal to the installed plugin's;
   any miss points at the three-command onboarding (`copilot plugin marketplace add
   CauchyIO/awow` → `copilot plugin install awow@awow` → `/awow-vs`), a stale marker at
   "run `/awow-vs`" — and every such pointer names the Copilot CLI session as where to run it:
   VS has no command surface. Until the VS bridge ships, render `– (VS bridge not yet shipped)`
   instead of checking. Codex, Pi, opencode: no checks defined; render
   `harness ✓ (no checks defined for <harness>)`.
6. **Declared other harnesses.** When `setup-progress.md` records a harness roster, probe what
   is checkable from this machine for each non-current entry (as in check 5 — for Visual Studio
   the full bridge chain) and report misses with the same pointers. These never gate: another
   harness's wiring cannot block this session.
7. **Payload freshness.** When a secondary local channel with a version marker exists (the VS
   bridge's `~/.copilot/skills/.awow-bridge.json`), compare its version against
   `${CLAUDE_PLUGIN_ROOT}/package.json`. Older marker → report it with the pointer to run `/awow-vs` (or
   update the plugin first via `/plugin`). No channel or no marker → render nothing. Never fetch
   anything remote for this.

**Render** one line above the step map when all applicable checks pass:
`preflight: git ✓ · repo ✓ · board ✓ · harness ✓` — expanding any non-✓ item to its own line
with reason and pointer. Omit items that do not apply.

**Gate.** Checks 1–2 are fatal: stop with the pointer; no step map, no steps. Checks 3–5 are
soft: continue, but annotate board-dependent work — Step 1b's issue count and mode pick, Step 3
observe mode, every board write — as `⧗ blocked: <reason>` in the step map, and steer to the
next step that does not need the missing piece. Checks 6–7 are informational only.

## Install shape — standalone or anchored

Classify the install shape before Step 0, once per repo:

- A vendored tree (`.agents/AGENTS.md`) or a recorded `install-shape:` in `setup-progress.md` settles it; do not re-ask.
- A root `AGENTS.md` whose frontmatter carries an `anchor:` key (`hub:` pre-rename) marks this repo as anchored; go to the Anchored track to complete or repair its registration.
- Otherwise, when you run from a plugin install in a repo with no awow files, ask once — and explain the choice inside the ask, in adopter language: "Is this repo joining a team that already runs awow from a shared repo (an 'anchor')? If yes, I'll anchor this repo to it — you'll need the anchor's git URL. If no, or you're not sure, I'll set this repo up on its own; you can anchor it later." An anchor must already exist for anchored to be a valid answer; "not sure" means standalone. Record the answer as `install-shape: standalone | anchored` in `setup-progress.md`; standalone continues with the steps below, anchored continues with the Anchored track.

## Anchored track — register this repo against an anchor

An anchored repo commits its anchor's identity (git remote URL), never a path. Walk these five steps in order; every repo write follows draft → approval → land.

1. **Identify the anchor.** Ask for the anchor's git remote URL and this repo's project name (default: the repo directory name). Never infer the anchor from sibling directories without the user confirming.
2. **Resolve the anchor locally.** Offer an accessible checkout whose normalized `origin` — host + owner/repo, ignoring scheme, credentials, an optional `.git` suffix, and a trailing slash — equals the anchor remote; else ask for a path or offer to clone. A checkout whose `origin` does not match is a stop, not a warning.
3. **Write the machine link.** Write `.awow/anchor.json` as `{"remote": "<anchor remote URL>", "path": "<absolute path to the clone>"}` and ensure `.gitignore` covers `.awow/`. This link is machine-local state: never commit it and never record the path in any committed file.
4. **Draft the anchored-repo PR** in this repo: root `AGENTS.md` with connector frontmatter (`awow: anchored`, `anchor: <remote URL>`, `project: <name>`) and a short body pointing collaborators at the anchor; `.claude/settings.json` enabling the awow plugin at project scope; `context/mission.md` (a project-level profile: what this repo is and its stack, same shape as the anchor's team profile); `context/board-scope.md` with frontmatter `board:` (the anchor's index name for it), `team:` (the board team items land on), optional `project:` and `subpath:` — ask which of the anchor's boards this repo maps to, and with a single-board anchor offer to skip the file; `context/do-not-propose.md` when the user wants one; the `.awow/` gitignore entry. Open the PR only after approval.
5. **Draft the anchor PR** in the anchor checkout: a knowledge-source record for this repo per `{ANCHOR}/context/tooling/knowledge-sources.md` — routing profile plus `anchored:` block — and its `index.md` line. Open it only after approval; when the user lacks anchor PR rights, leave the drafted record under this repo's `proposals/` with a handoff note naming who can land it.

Verify by reporting what a fresh session will see: the connected-anchored reflex with `{ANCHOR}` resolved to the recorded path. Tell the user registration completes when both PRs merge; neither blocks the other, and teammates need only clone the repo and answer the one-time map-the-anchor prompt.

## Orientation — track, hat, and what this repo serves

On first entry (no `track:` recorded in `setup-progress.md`), ask once, in plain language: "Are you setting this up for a whole team, or just yourself? If it's for a team, feel free to mention your role (PO, engineer, lead, …) — it helps me route later questions." Record `track: team | solo`. Do not present hats as a choice: default `hat: both`, and map a mentioned role to a hat ("I'm the PO" → `hat: product`, "engineer" → `hat: engineering`). The hat vocabulary itself surfaces later only when a step lands provisional (see Hats). Never re-ask either.

In **solo** mode, skip the steps that only make sense for a group and mark them as skipped when you lay out the plan:

- **Step 4 members** — skip; the roster is just the user. Still draft the style files, since they shape every artefact.
- **Step 7 neighbouring teams** — skip; there are no 1° teams to stub.

Reframe **Step 2** as what the user is building and in what stack, not a team charter — usually draftable straight from the repo. Everything else runs unchanged. A solo adopter can switch later by re-running `/setup-awow` and answering "team".

With `track: team`, establish what this repo serves: which board or boards, and which team or teams. When a wired surface or board URL is already known and names exactly one team, infer both and state them instead of asking; ask only when nothing is wired or the mapping is ambiguous. Record `boards: <comma list>` and `teams: <comma list>` in `setup-progress.md`. One board, one team — continue; this default path adds no further ceremony. More than one board — Step 1b drafts the index-form `board.md` (a `## Boards` list with sibling `board-<name>.md` specs, per §Context resolution in the agent instructions) and walks its configuration once per board. More than one team sharing members and conventions is one installation — say so, and recommend a separate installation only when the teams' conventions genuinely diverge.

Write `{PROJECT}/.awow/profile.json` (schema per §Context resolution) with the stated hat and, once boards are named, the invoker's default board. Never commit it.

### Hats — who answers which step

Steps carry a hat — **engineering**: 0 (installer), 1a (surface), 5 (bootstrap), 9 (skills review); **product**: 1b (board config), 2 (team profile), 3 (conventions), 4 (members + style), 6 (KB seed), 7 (neighbouring teams), 8 (extras). `hat: both` answers everything with no ceremony.

Any hat may answer any step — never block on the wrong hat. When the invoker's hat does not match the step's, land the artefact with a first line `provisional: needs <hat> confirmation`, mirror it in `setup-progress.md` under `## Pending confirmations`, and offer a hand-off brief at `proposals/setup/handoff-<step>.md` (e.g. `handoff-step-2.md`): one paragraph naming the step, what was answered provisionally, and that running `/setup-awow` resumes exactly there.

Surface pending confirmations in the step map on every invocation. When the right hat confirms or amends, remove the provisional line and the pending entry, and record the confirmation. Record `done-by: <name or hat>` beside every completed step's checkbox.

## Choose the input route — workshop or guided

When `setup-progress.md` has no `route:` entry, offer two equivalent ways to supply the team's setup context:

- **Guided** (default) — offer it as "answer as we go": continue through Steps 0–9 conversationally, one step at a time; the required steps take about 15 minutes.
- **Workshop** — offer it as "have the team talk it through": prepare a 25–30 minute meeting agenda, the team meets in its own time, and the transcript or notes come back as setup proposals.

Offer both in that plain language — a first-time user must be able to choose confidently without knowing awow's terms. Accept either route without persuasion; a user who doesn't choose gets guided. Record `route: workshop` or `route: guided`. Allow the user to switch or combine them later. Both routes land the same context files and use the same approval gates.

Treat a `.vtt`, `.srt`, or transcript-shaped Markdown argument as workshop input. Enter **Process the workshop** directly, including when `/process-transcript` hands you a parsed setup-workshop segment. Do not ask the route question in that case.

### Prepare the workshop

Do not require Step 0 or Step 1 before preparing the conversation. Read any existing setup progress and context that are safely available, then draft `proposals/setup/meeting-brief.md` with this timebox:

| Time | Conversation |
|---|---|
| 0–4 min | What the team exists to change, for whom, and within which boundaries |
| 4–10 min | How work enters, becomes ready, moves, and becomes done |
| 10–20 min | Recurring and custom meetings: purpose, cadence, what is distinctive here, and what useful output looks like |
| 20–25 min | Ownership, collaboration, communication, and where durable output belongs |
| 25–30 min | Confirm agreements, disagreements, deferred questions, and owners |

Write prompts that start a conversation, not an interview checklist. Use examples only to unblock discussion. Tell the facilitator to name whether a statement describes current practice, an agreed change, a suggestion, or unresolved disagreement. Keep credentials, MCP installation, authentication, and other technical wiring out of the meeting.

Show the brief and ask whether to use it. After approval, keep it at `proposals/setup/meeting-brief.md` as the meeting handout, record `meeting brief: prepared` and `meeting transcript: awaiting` in `setup-progress.md`, then stop. Let the team meet in its own time.

### Process the workshop

Read the transcript plus existing `setup-progress.md` and context. Build a coverage map for:

- the team profile — what the team works on, its stack, and any mission line — plus scope boundaries;
- board practice and work flow;
- conventions, members, and writing style;
- recurring and custom meetings;
- ownership, communication, and output placement;
- technical configuration still requiring hands-on setup.

Classify every usable statement as **current practice**, **agreed change**, **suggestion**, or **unresolved disagreement**. Do not convert one person's recollection, an unchallenged suggestion, or a disputed point into team context. When live board observations are available, compare them with what the team said and surface divergence rather than silently choosing one.

Draft the resulting setup changes under the existing `proposals/setup/step-*/` paths. Draft meeting guidance under `proposals/setup/meetings/<slug>.md`:

- For a common ritual, write only the meaningful ways this team differs from the generic lens in `_meeting-archetypes/`.
- For a custom recurring meeting, describe how to recognise it, what matters, and what useful output looks like.
- Use plain Markdown. Do not add frontmatter, identifiers, inheritance, or an `extends` syntax.
- Do not create a meeting file when the generic lens already fits.

Present one synthesis gate with the coverage map, source evidence, disagreements, pending areas, and the actual proposed diffs. Land only the selected proposals after explicit approval. Never copy the raw transcript into durable context.

Update the corresponding Steps 0–9 in `setup-progress.md` after approved proposals land. Record `meeting transcript: processed`. Leave uncovered topics pending and resume them through either route. Always perform credentials, board authentication, MCP installation, harness wiring, and write verification outside the workshop; never infer technical configuration from the conversation.

## Step 0 — Installer (REQUIRED)

The installer exists to serve a **vendored tree**: it wires Python via `uv`, creates `.venv`, and runs `tools/gather.py` once to mirror `.agents/` into the harness surfaces (`.claude/`, `.github/`, `.opencode/`) so the harness can discover this very command.

0. **Is there anything to install?** A plugin install has no vendored tree — both `.agents/AGENTS.md` and `setup/install.sh` are absent from this repo — and needs none: the commands already reach you from the payload, so there is no `.venv/` to create and no stub to generate. Probe with non-failing checks (`test -f .agents/AGENTS.md && echo present || echo absent`), never by reading the files; absent is the normal result here and a `cat` would surface a harmless `ENOENT` as a red error.

   When both are absent, say in one line that this is a plugin install and the installer does not apply, record `0. Installer — n/a (plugin install)` in `setup-progress.md`, and go straight to Step 1. Never offer to vendor a tree, and never run an installer from the payload against the user's repo. The rest of this step is the vendored-tree path only.

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
4. **Verify.** Confirm `.venv/` exists and that `.claude/commands/setup-awow.md`, `.github/prompts/setup-awow.prompt.md` and `.opencode/commands/setup-awow.md` are present.
5. Mark Step 0 complete in `setup-progress.md` and continue to Step 1.

## Step 1 — Kickoff (REQUIRED)

The outcome of Step 1 is a **wired-up board read/write surface** plus a fully-populated `context/tooling/board.md` that specifies this team's board — state machine, hierarchy, label taxonomy, fields, team-page conventions — not just the MCP wiring. The agent reads `board.md` thereafter whenever it needs to know what a label means, which states are terminal, or where in the hierarchy a new issue belongs.

Step 1 has two parts. Step 1a wires up the read/write surface (an MCP or, for GitHub, the `gh` CLI). Step 1b walks the team through configuration — either **Mode A** (set up from the reference for greenfield / under-configured boards) or **Mode B** (assess and capture current state for already-running boards). The choice is automatic, driven by counting closed issues. With more than one board recorded at orientation, run Step 1b once per board: the index-form `board.md` lists each board (name, scope, one-liner) and each board's full spec lands in a sibling `board-<name>.md`.

### Step 1a — Wire the read/write surface

1. **Establish harness.** The starter pack ships the `.claude/`, `.github/` and `.opencode/` directories, so their presence is not a signal — do **not** infer which harnesses are in use from directory listing alone. The real signal is which harness you (the model) are currently running inside:
   - If you are Claude Code, the current harness is Claude Code.
   - If you are GitHub Copilot, the current harness is Copilot.
   - If you are Codex, the current harness is Codex. (Corroborating on-disk signal: a repo-root `AGENTS.md` alongside a `.codex-plugin/` directory.)
   - If you are Pi, the current harness is Pi. (Corroborating on-disk signal: a `.pi/` directory.)
   - If you are opencode, the current harness is opencode. (Corroborating on-disk signal: an `.opencode/` directory or a repo-root `opencode.json`.)

   State it with an escape hatch rather than asking: "I'll wire up `<current harness>`, where we're running now. If your team also uses another supported agent (Claude Code, Copilot, Codex, Pi, opencode), name it and I'll wire that too — otherwise I'll continue." Silence or "continue" means current-only. Record the choice; this drives which install snippets you surface in step 4.

2. **Enumerate candidate surfaces — adopt a sole verified candidate with an escape hatch, ask on ambiguity.** Gather
   every candidate the preflight enumerated: MCP entries referencing a supported board tool in
   `.claude/settings.json`, `.claude/settings.local.json`, `.mcp.json`, `.vscode/mcp.json` (all
   relative to `<root>`), board MCP tools already loaded in your own tool surface, and — for GitHub-hosted boards — an
   authenticated `gh` CLI with `repo`, `project`, `read:org` scopes (the CLI alternative in
   `context/tooling/boards/github-issues/reference/mcp.md`).

   Exactly one candidate, and an identity-bearing read verifies it — the read returns the
   board it serves (Linear: `list_teams`; Jira / Azure DevOps: the projects; GitHub: the repo),
   never a bare "list anything" call — adopt it with the escape hatch rather than asking —
   "I found `<server-name>` (`<endpoint>`) already wired; it serves `<workspace / team>` — I'll
   use it unless you say otherwise." Silence means confirmed. More than one
   candidate, or a sole candidate failing verification: present them as a numbered list, each
   as `<server-name> — <endpoint> (from <provenance>)` (`gh` CLI listed as its own entry), and
   ask the user to pick one or answer "none of these" — never pre-select among several. On an
   adoption or a pick:
   - State the canonical board URL — derived from the config, or from what the identity read
     returned (workspace + team, project, or repo); ask for it only when it cannot be derived.
     It pins the board's identity for every later preflight, and `board.md` and team-page links
     need it.
   - Record the identity in `setup-progress.md`: `surface: mcp` plus
     `board-mcp: <server-name> <endpoint> (confirmed <YYYY-MM-DD>)` — or `surface: gh-cli` for
     the CLI — plus `board-url: <canonical board URL>`. Record the endpoint and the URL, never
     the provenance: which file supplies a server is machine-local, and committing it would lie
     on every other machine.
   - Verify with a single identity-bearing read against that URL: the team key, project, or
     repo it names must come back. If verification cannot succeed in this session — nothing
     loaded, or the loaded server serves another workspace — add `surface-verification:
     pending` to `setup-progress.md` and say so; a later session's passing preflight read
     clears that line. Then skip to step 5.

   On "none of these", or with no candidates at all, continue to step 3.

3. **No surface wired yet — ask for the board URL.** Tell the user you need the URL for two reasons: (a) to know which surface to install, (b) to extract the workspace / team identifier that the surface itself requires for config. Refuse to continue without one. Infer the tool family from the URL hostname:
   - `linear.app` → Linear
   - `dev.azure.com` or `*.visualstudio.com` → Azure DevOps
   - `*.atlassian.net` → Jira
   - `github.com/.../issues` or `github.com/orgs/<org>/projects/<n>` → GitHub Issues + Projects
   - Anything else → tell the user the tool is not supported and stop.

4. **Install and verify the read/write surface.** Load `context/tooling/boards/<tool>/reference/mcp.md` (the same file the per-tool `<tool>/README.md` indexes). That file is structured as: **Source docs** link, **Install — Claude Code** snippet, **Install — Copilot** snippet, **Verify** checklist; for GitHub it also includes the **`gh` CLI alternative**. Then:
   - Pick the install snippet that matches the harness recorded in step 1. If the user confirmed they use both, surface both — they will need to wire each.
   - Surface the **Source docs** URL first and tell the user it is authoritative: the snippet in the reference is a summary and may have drifted from upstream.
   - For GitHub, pick by observation instead of asking: `gh` already authenticated with the right scopes → default to the `gh` CLI (reuses existing auth); otherwise default to the MCP (full-feature, PAT-managed). State the choice in one line and name the alternative as the escape hatch. Record it as `surface: mcp` or `surface: gh-cli`.
   - Print the exact install command (or JSON snippet) for the user to run / paste. Configure it using the workspace / team identifier extracted from the URL where applicable.
   - Verify read access with a single identity-bearing read: it must return the team, project, or repo the board URL names, not merely answer.
   - Verify write access with a **no-op** write against a scratch issue (set the description to its current value, or re-add an existing label). If write access is not granted yet, surface that as a blocker — the agent cannot do its job read-only.
   - If the user cannot complete the install in this session (token in another browser, IT ticket, etc.), record the surface as `pending` in `setup-progress.md` and continue with Step 1b so the repo is at least partially usable; mark configuration items that depend on write access as `pending-write`.

### Step 1b — Board configuration (from reference or assess current)

The reference for this team's board lives at `context/tooling/boards/<tool>/reference/`. The wizard reads it section by section and walks the team through either configuring from it (Mode A) or capturing what's already there (Mode B).

5. **Pick mode by counting closed issues.** Use the surface to count closed (or `Done`) issues on the team's board. The threshold is **10 closed issues**: at or above, run Mode B; below, run Mode A. Surface the count and the chosen mode to the user before proceeding:

   > "I see **<n>** closed issues on this board. **<n> < 10**, so I'm running **Mode A — Set up from reference**. I'll draft the full board spec from the reference and you review it once at the end."
   >
   > _or_
   >
   > "I see **<n>** closed issues on this board. **<n> ≥ 10**, so I'm running **Mode B — Assess and capture current**. I will pull what is actually on the board, write it to `board.md` under the same section headings the reference uses, and surface any divergence at the review gate so you can decide what to close, override, or accept."

   If the count cannot be obtained (e.g. surface is `pending`), default to Mode A and note the deferral.

6. **Tell the user which reference layer is in use.** Before walking any section, check for an enterprise override at `.agents-overrides/tooling/boards/<tool>/reference/`. If it exists, that layer supersedes the starter pack's reference per file. Tell the user explicitly, e.g.:

   > "Reading from `.agents-overrides/tooling/boards/linear/reference/labels.md` (enterprise override) for the label taxonomy; everything else is from the starter pack."

   Repeat this preamble whenever the source layer changes for the next section.

7. **Walk the reference sections in order.** For each file under `<tool>/reference/` (`states.md`, `hierarchy.md`, `labels.md`, `fields.md`, `team-page.md`, `mcp.md` already covered in Step 1a, `cycles.md` / `iterations.md` if present):

   - **Mode A.** Read the reference file and draft the section by applying its defaults — do not interrogate the user per decision. Mark inside the draft any decision the reference flags as team-specific, so the review gate surfaces it. Where the surface supports mutation (Linear MCP can create labels; `gh` can edit Project fields), stage the changes and apply them only after the review gate. Where it does not (Linear Free workflow states, ADO process templates, Jira project workflows), include a step-by-step manual checklist in the draft for the user to run in the board UI, and re-verify after the user confirms.
   - **Mode B.** Read the same reference file for its `## What lands in board.md` shape. Pull the current state from the surface (workflow statuses, labels in use, native fields, team page contents). Write it to the corresponding `board.md` section. Diff against the reference; populate the `## Divergence from reference` section of `board.md` with each gap, and collect the user's resolutions (`close`, `override`, `accept`) as a set at the review gate — not one question per gap.

   Land each section's draft under `proposals/setup/step-1/board.md` incrementally — append, do not overwrite. Draft all sections in one pass: the user reviews the complete spec once at the gate below instead of approving section by section.

8. **Update labels.md to match reality.** If Mode B surfaces label names that diverge from the reference (e.g. team uses `bug` instead of `type:bug`), update `context/team/conventions/REQUIRED/labels.md` to reflect what is actually on the board, so future agent proposals match the team's reality. Draft the update under `proposals/setup/step-1/labels.md` and ask the user to approve before landing.

### Record and complete

9. **The one review gate.** When all sections are drafted, the file shape under `proposals/setup/step-1/board.md` is:

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

   Summarise the whole draft in a few bullets — surface (MCP / `gh` CLI / pending), state-machine mapping, hierarchy levels in use, label prefixes, fields in use, and any `## Divergence from reference` entries with their pending resolutions — and ask once:

    > "Here is your board spec. Happy for me to land it, or is there a section you want to adjust — or have me evaluate against the live board?"

    Accept one of:
    - **Land.** Move the file to `context/tooling/board.md`, apply any board mutations staged in Mode A, re-verify them, and continue to step 10.
    - **Adjust `<section>`.** Re-walk that section only (in the mode used originally; the user can switch), update the draft under `proposals/setup/step-1/board.md`, then return to this gate.
    - **Evaluate `<section>`.** Re-pull the live board state for that section via the surface, diff it against the draft, surface differences, and ask whether to update the draft or leave as-is. Return to this gate.

    Loop on the gate until the user says land. This is the single review gate for Step 1b: no per-section approvals before it, no second confirmation after landing. When a later session resumes with `board.md` already landed but Step 1 unchecked, re-enter this gate against the landed file (offering *proceed* instead of *land*) rather than re-walking sections.

10. Update `setup-progress.md` to check off Step 1. Record:
    - The mode used (A or B).
    - Any `pending` items (surface install, manual board-UI checklists, label normalisation).
    - The reference layer used per section (starter pack vs. enterprise override).
    - Any sections the user re-walked or evaluated at the gate (so a later session has the audit trail).

After Step 1, tell the user:

> The repo is usable and the board is documented — setup is done. Everything else fills in on first need: the first command that needs the team profile, a convention, the member roster, or a neighbouring team will offer to draft it in the moment, from your repo and board where it can. Start with a real command — `/refinement-prep` on a story, `/process-transcript` on a meeting. You can also fill any piece now: say which, or come back to `/setup-awow` whenever.

## Deferred fills — filled on first need

Steps 2–4 and 6–8 are not wizard stations. Per the fill-on-first-need contract in the agent instructions, the command that first needs each artefact offers to draft it in the moment, and these sections are the method such an offer routes to. Enter one only when a fill offer lands here, when the user names it, or on an explicit `/setup-awow` resume of that step. A fill that lands marks its step ✓ in `setup-progress.md` exactly as a wizard walk would, and the hats rules apply to fills as they do to steps.

## Step 2 — Team profile (deferred fill)

**Owner moment:** the first command that frames scope — `/refinement-prep`, `/process-transcript`, `/solution-design-flow`.

The artefact is a short profile — two to five plain sentences: what the team is building or working on right now, for whom, and the tech stack it works in. A one-sentence mission is an optional first line: keep it when the team has one, never demand one, and do not iterate on its quality.

Draft the profile from observation before asking anything:

- **The board.** Project / epic / initiative names and recent item titles say what is being worked on — reuse what Step 1 already pulled where possible.
- **The repo.** Manifests (`pyproject.toml`, `package.json`, `go.mod`, …) and the language mix give the tech stack.
- **The adopter repo's own README**, when one exists.

Present the draft with one gate: "Here's what I gathered from your board and repo — edit anything, or approve." Ask the open question — "what does your team work on, and in what stack?" — only as the fallback when observation comes up empty (bare repo, near-empty board).

The file keeps its path: land at `context/team/mission.md` via `proposals/setup/step-2/mission.md` — every consumer and existing adopter already reads that path; the file's own heading says "Team profile". Update `setup-progress.md`.

## Step 3 — Required conventions (observe or guide; deferred fill)

**Owner moment:** the first board write — until a convention file exists, `workitem-write` cites the reference defaults and offers this fill.

For each of the four REQUIRED conventions (`issue-titles.md`, `labels.md`, `branches.md`, `output-discipline.md`):

- If the board has ≥10 closed issues, **observe**: query the board, summarise the existing pattern, and draft the convention to match. Show the user three real examples from their board so they can confirm. `labels.md` may already have been drafted in Step 1b (Mode B); reuse that draft and extend it with the rules.
- If the board is greenfield (<10 issues), **guide**: propose sensible defaults from `context/tooling/boards/<tool>/reference/`. Let the user opt out of any rule that does not fit.

`output-discipline.md` is non-negotiable. If the user objects, explain why (the agent over-produces without it). Iterate on the rules, do not skip the file.

Land each under `proposals/setup/step-3/<convention>.md`, get approval, move to `context/team/conventions/REQUIRED/<convention>.md`. Update `setup-progress.md`.

## Step 4 — Members and style (deferred fill)

**Owner moment:** the first artefact that needs the roster or the team's voice — speaker mapping in `/process-transcript`, any style-bearing output.

If members are listed in the board's team page, pull the list from there first and present it for confirmation — roles, responsibilities, and focus areas filled in where visible, asked for where not. Ask for the team member list (role, responsibilities, focus areas) only when no team page or member data exists. With more than one board recorded at orientation, also capture per member which boards they work (a `Boards:` line) and name each board's product curator and technical curator — hand-off briefs and provisional confirmations address the curators.

Draft `context/team/style/board-output.md`, `comments.md`, `placement.md`, `prose.md` from the reference templates, customising only where the user pushes back.

## Step 5 — CLAUDE.md / AGENTS.md bootstrap

Run `tools/bootstrap-claude-md.py` (or the inline equivalent). It reads the stub at `.agents/AGENTS.md` plus every file the wizard has produced so far and writes a team-specific `CLAUDE.md`.

Critically: ask the user to populate the `## Do not propose` block. Surface scope-shedding statements ("we are not adding multi-user this quarter", "do not propose moving away from Linear"). Land the result. In a vendored install, run `tools/gather.py` to mirror it to `.claude/CLAUDE.md` and `.github/AGENTS.md`; a plugin install has nothing to mirror — the landed file is the team's own.

## Step 6 — Knowledge base seed (deferred fill)

**Owner moment:** the first `/kb-mine` or `/kb-synthesize` run — the spine works on its shipped defaults; canonical sources come up at the first external reference.

Walk the user through `context/knowledge-base/README.md` — what lives there vs. on the board. Offer to seed `glossary.md` from any glossary they already have. Stub the architecture/patterns/runbooks/decisions subfolders with one example each if useful.

**The capture → synthesize spine.** Explain how durable knowledge gets *in*, so the KB isn't a folder nobody fills:

- **Capture.** Mining a day's activity (`/kb-mine`) stages candidates as committed files in `context/kb-inbox/` — one durable insight per file. Point the user at `context/kb-inbox/README.md`.
- **Tune.** What mining keeps is governed by `context/knowledge-base/mining-policy.md`. Keep its shipped defaults without asking (`selectivity: 2`, strict); say in one line that the dial exists there and can be loosened later. Adjust it now only if the user raises it.
- **Synthesize.** Draining the inbox into the durable KB is `/kb-synthesize` (per `context/knowledge-base/synthesis.md`) — **human-gated by default** (novel → write, matches → annotate, covered → no-op, thin → drop). Make clear no autonomous write path ships; unattended nightly drain is opt-in and out of the box.

**Locations.** The two KB folders — `kb_root` (default `context/knowledge-base/`) and `inbox` (default `context/kb-inbox/`) — are declared in `context/tooling/knowledge-base.md`. Keep the defaults without asking; note in one line that they can be relocated later by updating the two paths in that config **and moving the folders to match** (`git mv`). Act on it now only if the user raises it. Keep the two folders distinct — the drain moves files from `inbox` into `kb_root`.

**Canonical sources (optional).** Ask whether important knowledge remains canonical in another
repository, SharePoint, a vector-backed retrieval system, or another provider. If yes, read
`context/tooling/knowledge-sources.md` and draft one OKF source record per system under
`proposals/setup/step-6/knowledge-sources/`. Each record captures a description, routing signals,
canonical remote URI, and read capability — never source content or a machine-local clone path.
After approval, ensure `context/knowledge-sources/index.md` exists with `okf_version: "0.2"`, land
the records beside it, and link them from that index. Do not test access by writing to an external
source. If no, leave an existing empty catalog alone; when no catalog exists, routing stays inert.

Nothing is required here — the spine works on its defaults. The one question this step asks is
canonical sources; the `selectivity` dial and the two KB paths keep their defaults, adjustable
later. Record in `setup-progress.md` whether the defaults were kept or adjusted and whether
external sources were cataloged.

## Step 7 — Neighbouring teams (deferred fill)

**Owner moment:** the first cross-team boundary a transcript or design touches — `/process-transcript` and `/solution-design-flow` offer to record just the team they named in `context/company/neighbouring-teams.md`.

Nothing is scaffolded up front and no stub files are generated. Each neighbouring team still writes its own summary; ours records the boundary. Use this step only to bulk-record several 1° teams when the user asks for that.

## Step 8 — Surface the extras (deferred fill)

**Owner moment:** the extras detect-then-suggest on their own (`design-system.md`'s absent-mode probe, the correlation opt-in, engine detection); walk this step only on request.

Read the commands whose frontmatter declares `phase: spread` or `phase: standardise` — from `{ANCHOR}/.agents/commands/` if that directory exists (a vendored install), otherwise `${CLAUDE_PLUGIN_ROOT}/commands/`. List each command, its phase, its prerequisites, and the pain it removes. Tell the user:

> These are all available now; each earns its place once its prerequisites hold.

**Design system (detect, then suggest).** Read `context/tooling/design-system.md`.

- If `mode:` is not `absent`, a design system is already configured — name its `path:` and move on; do not re-offer.
- If `mode: absent`, ask one question: *"Does your team produce styled HTML artifacts — decks, blogs, solution designs, one-pagers?"* If **yes**, recommend the add-on flow: *"Run `/design-system` to stand one up or point at an existing one. Until then, HTML artifacts use plain defaults."* Do not run it now — it is opt-in. If **no**, leave the pointer at `absent`.

Record the answer (and any configured `path:`) in `setup-progress.md`.

**Session-board correlation (opt-in).** Ask whether the team wants agent-authored board entries linked back to their session traces. If **yes**, first run the `session-correlation` skill's prerequisite check: tracing must already be wired (`MLFLOW_CLAUDE_TRACING_ENABLED=true` plus the MLflow `Stop` hook in `.claude/settings.local.json`). This skill does **not** set tracing up — if it is missing, stop and point the user at their own tracing library to configure tracing first, then resume. Once tracing is confirmed: install the footer rule from the skill — append its Rule 4 to `context/team/conventions/REQUIRED/output-discipline.md`, add its shape note to `context/team/style/board-output.md`, and wire the SessionStart accessor hook per the skill's "Enabling it" steps. If Step 5 already generated the team's `CLAUDE.md` / `AGENTS.md`, re-run the bootstrap (or edit the file) so the rule flows into it. If **no**: leave all three untouched; the skill stays available to enable later by following its "Enabling it" steps. Record the choice in `setup-progress.md`.

**Build engine (detect, then suggest).** awow owns the outer loop (board, planning, landing) and hands the *build* step to an optional inner-loop engine. Detect whether one is installed by checking for a `superpowers` directory under `~/.claude/plugins/cache/*/`, `~/.claude/plugins/*/`, or this repo's `.claude/plugins/*/`.

- **Found** — an engine is configured; name it and move on. The `board-aware-development` seam (skill + PreToolUse reminder) is already active. If this team also keeps an architecture plane (ADRs / design records / pattern notes) reachable by a KB agent, offer to write a `context/tooling/architecture.md` pointer (draft it to `proposals/setup/step-8/` first, approve, then land it) — that switches on the parallel `architecture-aware-development` seam. No plane → skip it; the seam stays dormant.
- **Not found** — recommend it as **optional**: *"awow hands the build step to an inner-loop engine. superpowers adds TDD-gated build → review and lights up the board-aware-development seam (and the architecture-aware-development seam, when a `context/tooling/architecture.md` plane is present). Install it with `/plugin` from the `claude-plugins-official` marketplace. This is optional — awow runs on its baseline build guidance without it."* Do not install it for the user, and never make it required. Note that spec-kit is an alternative engine (spec-first rather than test-first) for teams who prefer it.

This is a soft dependency by design. Do not add it to the plugin manifest's `dependencies`; that would force-install it on every adopter and couple awow across marketplaces.

Record the choice (engine name, or "none — declined") in `setup-progress.md`.

Update `setup-progress.md` to mark all steps surfaced.

## Step 9 — Skills review (keep / customise / drop)

The starter pack ships several skills — under `{ANCHOR}/.agents/skills/` if that directory exists (a vendored install), otherwise `${CLAUDE_PLUGIN_ROOT}/skills/`. Each is opinionated about *some* part of the stack — harness session format, tracing backend, rubric — and will not fit every team out of the box. This step walks the user through each shipped skill once they have enough context to make a call.

For each entry in that directory (read it; a vendored install holds both declarative `<name>.md` files and operational `<name>/SKILL.md` directories, while the payload renders every skill as `<name>/SKILL.md`):

1. Read each skill's frontmatter `description` and first body paragraph; summarise in one sentence.
2. Identify the **specific assumption** each skill bakes in (e.g. *"assumes Databricks MLflow"*, *"reads Claude Code JSONL"*, *"uses our story template"*). The "Starter shape — adjust for ..." callout at the top of each shipped operational skill states this directly; quote it.
3. Present **one table** covering every shipped skill — summary, baked-in assumption, and what depends on it (from the SKILL.md "Interplay" section) — with the default **keep all**, and ask for exceptions only:

   > "Default is to keep all of these. Name any skill to customise or drop — or say keep."

   Do not ask per skill.

4. Apply the user's answer per named exception:
   - **Keep** — no change.
   - **Customise** — open the SKILL.md and the bundled scripts. Draft the changes under `proposals/setup/step-10/<skill>/` first (full proposal-first treatment). Common customisations to surface as concrete options:
     - **mlflow-export**, **prompt-skill-analysis**, **awow-usage-coach**, **project-timeline**, **session-export** — these five ship in the separate `awow-telemetry` plugin, not in `awow`. If the team has not installed it (`/plugin install awow-telemetry@awow`), say so once and move on; do not offer to customise skills that are not present. If it is installed, or the repo is vendored and carries the sources under `.agents/skills/`, the customisations worth surfacing are:
       - **mlflow-export** — swap the exporter script for the team's tracing backend (LangSmith, Helicone, OTLP, raw JSONL). The downstream skills consume the JSON layout documented in `mlflow-export/SKILL.md`; match that shape or update the consumers too.
       - **prompt-skill-analysis** — add a parser for the team's harness session format (Copilot, Cursor, etc.). The rubric is harness-agnostic; only the input branch needs work.
       - **awow-usage-coach** — adjust the intent taxonomy if the team's vocabulary doesn't fit; otherwise rely on the harness-agnostic `working_directory` + `files_modified` lenses.
     - **user-story-template** — replace with the team's own template if it differs from the seeded shape.
   - **Drop** — `git rm -r` the skill directory or file. Note in `setup-progress.md` so a re-run of `/setup-awow` doesn't keep re-offering it.

5. If the user wants to **add** a new skill that isn't in the starter pack, point at `{ANCHOR}/.agents/skills/README.md` ("When to write a skill") when the vendored tree is present — the payload does not carry it — and offer to scaffold one — either a declarative `<name>.md` or an operational `<name>/SKILL.md` with a `scripts/` directory.

Update `setup-progress.md` to mark Step 9 complete (record per-skill decisions inline so the next session has context).

**Re-run this step whenever the stack changes** — new harness, new tracing backend, new shared rubric. Skills review is not a one-shot.

## Quickest-quickstart (alternative)

If the user invokes `/setup-awow --quickstart`, do Steps 0 → 1 → 2 → 3 → 5 in one turn against the user's responses, with sensible defaults for everything not asked about. Step 0 (installer) still requests permission before running the shell script; the rest skips the per-step review loop. This is the one-shot path for users who already know what they want and don't need the wizard. The conversational wizard remains the default.

## Proposal-first

Every artefact lands first under `proposals/setup/<step>/<file>.md`. The user reviews. Only after explicit approval does the wizard move the artefact to its final location. This is the proposal-first principle. Do not bypass it.
