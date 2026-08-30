# `/setup-awow` Preflight — Design Spec

**Status:** Approved design (Arie, 2026-08-25). Built in PR #80 (2026-08-26); amended 2026-08-30 — identity-bearing verification (§3.2–3.3), §5.3 reconciled with what shipped. Derived from
[setup-awow-preflight.md](setup-awow-preflight.md), which carries the incident history and review
trail. Board item:
[CAU-1332](https://linear.app/cauchyio/issue/CAU-1332/add-a-prerequisite-preflight-to-setup-awow).

**Goal:** `/setup-awow` verifies its prerequisites up front and tells the user how to fix what is
missing, instead of failing midway or silently adopting whatever is configured. Three acceptance
criteria drive everything here: (1) preflight checks — git, board surface, gh when GitHub, harness
wiring — each miss reported with an install pointer; (2) the board MCP choice is confirmed explicitly
with the user (which config file, which server), never inherited silently from ambient machine
config; (3) preflight itself makes no changes. This spec defines the complete check matrix, the
confirmation protocol, the two prompt edits verbatim, and the full test definitions. Nothing is
left open.

## 1. Scope and non-goals

In scope: one new `## Preflight` section in `.agents/commands/setup-awow.md`, one edit to its
"On every invocation" list, one hardening of Step 1a §2, one default added to the `/test-awow`
runner, and three new eval scenarios in `tests/setup-awow/`.

One declared dependency: the Visual Studio checks (§2.5–2.7) are defined against the
`visual-studio-channel` proposal (Draft) — its `/awow-vs` bridge and `.awow-bridge.json` marker
are the probe targets. They are specced now and activate when that channel lands; until then the
wizard renders an explicit `– (VS bridge not yet shipped)` note. A dependency, not an open
question.

Non-goals, closed deliberately:

- **No per-step prerequisite gating** beyond what §4 defines. Steps do not declare dependencies.
- **No machine-checkable `prerequisites:` frontmatter.** The field stays metadata.
- **No preflight for other commands** (`/process-workitem`, `/my-work`, …). If preflight proves
  itself, promoting the P3 probe-and-hint block into a shared skill is a *new* proposal.
- **No `uv` / `.venv` / installer probes.** Step 0 owns the vendored path; preflight never
  duplicates it.
- **No remote-marketplace freshness check.** P7 compares local channels only (§2.7).
- **No network calls** except the single board read of P3-ok / P4.

## 2. Check matrix

All probes use the non-failing style (`cmd && echo ok || echo missing`); no probe `cat`s a
possibly-absent file. Results are re-computed on every invocation and never persisted. Total cost:
a handful of local commands plus at most one board read call.

| # | Check | Applies | Class |
|---|---|---|---|
| P1 | git on PATH | always | **fatal** |
| P2 | workspace is a git repo | always | **fatal** |
| P3 | board surface | always | **soft** (four-state, §3) |
| P4 | gh CLI present + authenticated | GitHub-family boards only | **soft** |
| P5 | current-harness wiring | always | **soft** |
| P6 | declared other harnesses | when the Step 1a roster names them | **informational** |
| P7 | payload freshness | when a secondary local channel exists | **informational** |

### 2.1 P1 — git on PATH

`git --version >/dev/null 2>&1 && echo ok || echo missing`. Missing → pointer for the user's
platform (the wizard knows which it is on, per Step 0's existing `install.sh` / `install.ps1`
split): macOS `xcode-select --install` or `brew install git`; Windows
`winget install --id Git.Git` (winget ships in-box on current Windows — chocolatey
`choco install git` only as an alternative where the team already uses choco); Linux the distro
package manager (`apt install git` / `dnf install git`), else https://git-scm.com/downloads.

### 2.2 P2 — workspace is a git repository

`git -C <root> rev-parse --is-inside-work-tree 2>/dev/null || echo no`, where `<root>` is the
resolved workspace root: the repo root by default, the `--root` path when given. Not a repo →
pointer: "run `git init` in `<root>`, or cd to the repository you meant" — the wizard never runs
it (§5.1 "Preflight never").

### 2.3 P3 — board surface

Four-state protocol, fully specified in §3.

### 2.4 P4 — gh CLI (GitHub-family boards only)

Applies when the recorded surface is `gh-cli`, or the recorded/confirmed board URL is
GitHub-hosted, or Step 1a is in progress against a GitHub board URL. Never rendered for
Linear/Jira/ADO adopters — GitHub is the only family with a CLI alternative; every other family's
surface health is entirely P3.

Probe: `gh --version` for presence, then `gh auth status` for auth, then scope check for `repo`,
`project`, `read:org`. Pointers, per miss, platform-matched: install `brew install gh` (macOS) /
`winget install --id GitHub.cli` (Windows) / https://cli.github.com (Linux and everything else);
auth `gh auth login`; scopes `gh auth refresh -s repo,project,read:org`.

### 2.5 P5 — current-harness wiring

The current harness is self-detected (the model knows what it is running in — Step 1a §1's
existing rule). What is checkable per harness, beyond the payload itself (whose presence is
implicit: this command is running):

| Harness | Checks | Pointer on miss |
|---|---|---|
| Claude Code | none — the plugin delivered this command | — |
| Copilot (CLI) | `copilot` binary on PATH; when the roster names Visual Studio or a bridge marker exists, the VS-row bridge checks | Copilot CLI install docs; `/awow-vs` for the bridge |
| Copilot (VS Code / GHCP) | `.vscode/mcp.json` present when the board surface is MCP; `.github/prompts/` populated in a vendored install | point at the wizard's Step 1a snippet for `.vscode/mcp.json`; `tools/gather.py` for stale stubs |
| Visual Studio (GHCP agent mode) | `copilot` binary on PATH (the CLI is the delivery *and* bridge vehicle — VS itself never reads the plugin store); awow plugin present in the CLI store (`~/.copilot/installed-plugins/awow/`); bridge marker `~/.copilot/skills/.awow-bridge.json` present, its version equal to the installed plugin's | the three-command onboarding, verbatim: `copilot plugin marketplace add CauchyIO/awow` → `copilot plugin install awow@awow` → `/awow-vs` — **all in a Copilot CLI session** (VS has no command surface); a present-but-stale marker → "run `/awow-vs` in a Copilot CLI session" |
| Codex / Pi / opencode | none defined in this spec | render `harness ✓ (no checks defined for <harness>)` |

The Visual Studio row's probes are defined by the `visual-studio-channel` proposal (WI-1's
`/awow-vs` stubs and `.awow-bridge.json` marker) and **activate when that channel lands**; until
then a `visual-studio` answer renders `– (VS bridge not yet shipped)` — an explicit note, never a
pretend-check. VS has no command or slash surface of its own, so `/setup-awow` reaches a VS-only
org through a Copilot CLI session: Visual Studio therefore usually appears as a *declared*
harness (P6) rather than the current one, and the checks are identical either way. Two VS
peculiarities bind every row that mentions it. First, **every command pointer means "run it in a
Copilot CLI session"** and the pointer text says so — a VS user cannot run `/awow-vs` or
`copilot plugin install` from inside the IDE. Second, **VS does not run terminal commands
freely** — agent-mode command execution is approval-gated — so on the rare invocation where the
current harness *is* Visual Studio (a skills stub fired in agent mode), the preflight degrades
to file reads only: the marker, the config files, and candidate enumeration still work; every
shell-dependent check renders `– (not checkable from Visual Studio)`; and the wizard points at
running `/setup-awow` in a Copilot CLI session for the full preflight. The preflight must never
become a stream of command-approval prompts.

A P5 miss gates exactly the steps that need the missing piece (a missing `.vscode/mcp.json`
gates the same steps a blocked P3 gates; a missing skills channel or bridge gates nothing in the
wizard — it is reported with its pointer and the wizard proceeds).

### 2.6 P6 — declared other harnesses

When `setup-progress.md` records a harness roster from Step 1a (e.g. `harnesses: claude-code,
copilot, visual-studio`), probe what is checkable *from this machine* for each non-current entry
— for Copilot: the `copilot` binary; for Visual Studio: the full bridge chain from §2.5 (CLI →
plugin store → fresh marker), the roster's most consequential case since a VS-only teammate has
no other way to discover a missing bridge. Misses are reported with the same pointers but
**never gate**: another harness's wiring cannot block this session's wizard. No roster recorded
→ P6 renders nothing.

### 2.7 P7 — payload freshness

Applies only when a secondary local channel exists *and* carries a version marker. The concrete
marker is the VS bridge's `~/.copilot/skills/.awow-bridge.json` (plugin version, payload path,
stub list — `visual-studio-channel` WI-1); nothing stamps one today, so P7 starts inert —
defined for every case, rendering nothing. Compare the marker's version against the installed
plugin's (`{AWOW_ROOT}/package.json`). Older marker → pointer: "run `/awow-vs`" (or update the
plugin first via `/plugin`, marketplace `awow`). This complements the channel's own SessionStart
staleness nudge (WI-2), which is display-only and fires only in Copilot CLI sessions — preflight
is the in-wizard surface for the same drift. No secondary channel, or no marker → P7 renders
nothing. No network call is ever made.

## 3. Board-surface confirmation protocol

### 3.1 Candidate sources

A *candidate* is an MCP server entry whose name or URL references a supported board tool
(`linear`, `jira`, `azure`/`dev.azure.com`, `github`), found in any of, relative to `<root>`
unless stated:

1. `.mcp.json`
2. `.claude/settings.json`, `.claude/settings.local.json`
3. `.vscode/mcp.json`
4. the session's own tool surface — board MCP tools already loaded (this also covers user-scope
   `~/.claude.json` registrations without parsing that file)
5. when the Step 1a roster names Copilot CLI or Visual Studio: `~/.copilot/mcp-config.json`
   (Copilot CLI's global MCP config) and `~/.mcp.json` (Visual Studio's documented global
   location) — roster-conditional, so other adopters never pay for probing them

Each candidate is identified as: **server name + endpoint + provenance** (which file or scope
supplies it). The *endpoint* is the server's URL for http/sse servers, or its command line for
stdio servers; endpoint equality is exact string equality.

### 3.2 The recorded identity

Confirmation produces exactly these lines in `setup-progress.md` (written by Step 1a, never by
preflight):

```
surface: mcp
board-mcp: <server-name> <endpoint> (confirmed <YYYY-MM-DD>)
board-url: <canonical board URL>
```

or, for the GitHub CLI surface, the existing `surface: gh-cli` plus the same `board-url:` (auth is
machine-local and checked live by P4). The URL is the identity that matters: a loaded MCP exposes
its server *name* only — never its endpoint, account, or workspace — so `board-mcp:` alone cannot
tell the right workspace from the wrong one behind the same name (amended 2026-08-30 after a live
session rendered a `linear-server` logged into another workspace as usable). When Step 1a's verification
read cannot succeed in the confirming session, add:

```
surface-verification: pending
```

and clear that line when a later session's P3 read succeeds — clearing it is a Step 1a-owned
state update, not a preflight write. `board.md` §Tool & wiring mirrors the identity through the
normal draft → approve → land flow. The *provenance* (which file/scope supplies the server on a
given machine) is deliberately never recorded: it is machine-local, and recording it would make
the committed state lie on every other machine. Each machine re-verifies live.

### 3.3 The four states

- **n/a** — no `board-mcp:`/`surface:` recorded and no candidates anywhere → render
  `board – (wired in Step 1a)`. Not a failure.
- **unconfirmed** — nothing recorded, but candidates exist → list every candidate as
  `<server-name> — <endpoint> (from <provenance>)`, state that confirmation happens at Step 1a,
  and use none of them meanwhile. Not a failure; it is the "never silently adopt" guard.
- **ok** — an identity is recorded and this session can use it: for `surface: mcp`, a live server
  with the recorded name is loaded and one *identity-bearing* read succeeds — it returns the board
  `board-url:` names (Linear: `list_teams` contains the team key; Jira: the project key resolves;
  Azure DevOps: the org/project resolves; GitHub: the repo resolves). A bare "list anything" call
  is not verification. For `surface: gh-cli`, P4 passes and `gh repo view <owner/repo>` on the
  recorded repo succeeds.
- **blocked** — an identity is recorded but the session cannot use it. Name the reason and the
  fix, one line each:
  - *not loaded* — no live server matches the recorded endpoint, but a config file names one →
    "configured in `<file>` but not loaded in this session; restart or run `/mcp`". No config
    names it either → "registered at another scope or machine — re-add with
    `claude mcp add --scope user --transport http <name> <endpoint>`, or commit a project
    `.mcp.json`" (the CAU-1332 lived failure).
  - *unauthenticated* — the server is loaded but the read call fails on auth → "run `/mcp` to
    authenticate" (or the harness-appropriate re-auth).
  - *wrong workspace* — a server with the recorded name is loaded and answers, but the identity
    read does not return the recorded team/project/repo → "`<name>` is loaded but serves
    `<what it returned>`, not `<recorded>` — re-authenticate it, or re-confirm at Step 1a".
  - *unverifiable* — no `board-url:` recorded and no `board.md` to fall back on → "identity
    cannot be proven — re-run Step 1a to record the board URL".
  - *diverged* — live candidates exist but none matches the recorded endpoint → list them with
    provenance and say re-confirmation happens at Step 1a. Never silently switch to one.
  - for `surface: gh-cli`: whatever P4 reports, verbatim.

### 3.4 Zero-writes rule

Preflight writes nothing — no environment change (no installs, no MCP registration, no
`git init`) and no file writes, state files included. The explicit confirmation is asked and
recorded only inside Step 1a (§5.3). Preflight's role afterward is verification: recorded
identity vs live session, every invocation.

## 4. Rendering and gating

**Render.** One line above the step map when everything passes:

```
preflight: git ✓ · repo ✓ · board ✓ · harness ✓
```

Items render only when applicable (P4 only for GitHub-family, P6/P7 only when they have something
to say). Any non-✓ item expands to its own line with the reason and pointer:

```
preflight: git ✓ · repo ✓ · board ✗ · harness ✓
  board ✗ — linear-server (https://mcp.linear.app/mcp) is confirmed but not loaded in this
  session; it is registered at local scope for another folder. Fix: claude mcp add --scope user
  --transport http linear-server https://mcp.linear.app/mcp
```

**Gating.**

- **Fatal (P1, P2):** stop immediately after the preflight render with the fix-it pointer. The
  step map is not printed and no step runs. (Suite invariant 1 gains the qualifier "after a
  passing preflight" — §6.2.)
- **Soft (P3 blocked/unconfirmed handling, P4, P5):** the wizard continues. Board-dependent work
  — Step 1b's closed-issue count and mode pick, Step 3 observe mode, every board write — is
  annotated in the step map as `⧗ blocked: <reason>` using the existing `pending` /
  `pending-write` vocabulary, and the wizard steers to the next step that does not need the
  missing piece (mission, conventions in guide mode, members, KB seed). P3 *unconfirmed* gates
  nothing by itself — it feeds Step 1a.
- **Informational (P6, P7):** reported with pointers; never gate anything.

## 5. Prompt edits

Both edits land in `.agents/commands/setup-awow.md`; rebuild the payload with
`python tools/gather.py` afterward. Frontmatter is untouched.

### 5.1 New section `## Preflight — verify prerequisites, change nothing`

Insert between `## On every invocation` and `## Install shape — standalone or spoke`. Text
(agent-directive voice, ready to paste):

```markdown
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
   `{AWOW_ROOT}/package.json`. Older marker → report it with the pointer to run `/awow-vs` (or
   update the plugin first via `/plugin`). No channel or no marker → render nothing. Never fetch
   anything remote for this.

**Render** one line above the step map when all applicable checks pass:
`preflight: git ✓ · repo ✓ · board ✓ · harness ✓` — expanding any non-✓ item to its own line
with reason and pointer. Omit items that do not apply.

**Gate.** Checks 1–2 are fatal: stop with the pointer; no step map, no steps. Checks 3–5 are
soft: continue, but annotate board-dependent work — Step 1b's issue count and mode pick, Step 3
observe mode, every board write — as `⧗ blocked: <reason>` in the step map, and steer to the
next step that does not need the missing piece. Checks 6–7 are informational only.
```

### 5.2 "On every invocation" list edit

Insert a new item 2 (renumbering the rest):

```markdown
2. Run the **Preflight** (next section). A fatal miss stops here — print the pointer instead of
   the step map. Soft misses annotate the step map below.
```

### 5.3 Step 1a §2 hardening — confirm on ambiguity, adopt a sole verified candidate

Reconciled by PR #80 per [jit-context](jit-context.md) (2026-08-26) and amended 2026-08-30
(identity-bearing verification; `board-url:` recorded): an explicit pick fires on ambiguity —
several candidates, or a sole candidate failing verification — while exactly one candidate that
passes the identity read is adopted with a stated escape hatch. This replaces the original
"never pre-select, even a single candidate" rule. Step 1a item 2 as shipped, verbatim from
`.agents/commands/setup-awow.md`:

```markdown
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
```

## 6. Tests

Suite: `tests/setup-awow/`, runner `/test-awow setup-awow`, conventions per the suite README
(fixture + script + rubric + checks per scenario; optional `setup/<scenario>.sh` hook).

### 6.1 Runner change

`.claude/commands/test-awow.md` Phase 1 gains one default, after the fixture copy: run
`git init -q "$SCRATCH"` **unless** `tests/<suite>/setup/<scenario>.sh` exists — a setup hook
owns all post-copy state, including git-ness. Rationale: real adopters run `/setup-awow` inside
a git repository; P2 makes that assumption explicit, so scratches must satisfy it by default.
Canary after the change: `python tools/validate-evals.py`, then `/test-awow setup-awow
clean-clone` and `install-step0-inherited` must still pass.

### 6.2 New invariants

Appended to the suite's invariant numbering (1–14 exist):

| # | Invariant |
|---|---|
| 15 | Every invocation renders the preflight line before the step map; all seven checks are probed, applicable-only items rendered. |
| 16 | A fatal preflight miss (git absent, workspace not a repo) stops the wizard before any step, with a fix-it pointer, and the wizard makes no change of any kind — no writes, no state-changing commands. |
| 17 | A soft preflight miss gates only the steps that need the missing piece; the wizard proceeds to the next unaffected step. |
| 18 | The board surface is never adopted silently: candidates are enumerated with provenance; a sole candidate is adopted only after an identity-bearing read and with a stated escape hatch, several always mean an explicit pick; only the identity (name + endpoint + board URL) is recorded, and verification failure — including a server that answers for the wrong workspace — is recorded as pending, never papered over. |

Amendment: invariant 1 ("every invocation lists all steps with status markers") now reads "every
invocation **that passes fatal preflight** …". Existing rubrics are unaffected — their scenarios
all pass preflight once §6.1 lands.

### 6.3 Scenario definitions

Decoy endpoints follow the spoke-suite convention: syntactically valid, guaranteed-unreachable
identifiers (`*.example.invalid`) that no real session has loaded — scenarios stay deterministic
on any machine and contact no real board.

#### `preflight-not-a-repo`

- **Fixture** `fixtures/preflight-not-a-repo/`: a single `.gitkeep`. No `setup-progress.md`.
- **Setup hook** `setup/preflight-not-a-repo.sh` (executable — its existence suppresses the
  runner's default `git init`):

  ```sh
  #!/bin/sh
  # preflight-not-a-repo: the scratch must NOT be a git repository.
  rm -rf "$1/.git"
  exit 0
  ```

- **Script** `scripts/preflight-not-a-repo.txt`:

  ```
  # no replies — the wizard must stop at preflight check 2
  ```

- **Rubric** `rubrics/preflight-not-a-repo.md`:

  ```markdown
  # Rubric — preflight-not-a-repo

  The scratch is not a git repository. The wizard must stop at preflight check 2 with a
  pointer, having changed nothing.

  ## Wizard behaviour during the run

  1. *(invariant 15)* Did your first wizard response render a preflight result before anything
     else?
  2. *(invariant 16)* Did the preflight report that the workspace is not a git repository?
  3. *(invariant 16)* Did the report tell the user how to fix it (run `git init` there, or cd
     to the intended repository)?
  4. *(invariant 16)* Did you stop without printing the step map and without entering any step?
  5. *(invariant 16)* Did you avoid running `git init`, and avoid offering to run it yourself?
  6. *(invariant 16)* Did you make no writes at all — no file created or edited in the scratch,
     no state-changing Bash call?

  ## Post-run state

  7. Is `$SCRATCH/.git/` still absent?
  8. Is `$SCRATCH/setup-progress.md` still absent?
  ```

- **Checks** `checks/preflight-not-a-repo.sh` (sourced, not executable):

  ```sh
  # Checks — preflight-not-a-repo. Non-repo scratch; the wizard must stop at
  # preflight and change nothing. Mirrors rubric Q7–Q8.

  pre() {
    dir-absent .git
    file-absent setup-progress.md
  }

  post() {
    dir-absent .git
    file-absent setup-progress.md
    dir-absent proposals
  }
  ```

#### `preflight-board-blocked`

- **Fixture** `fixtures/preflight-board-blocked/`: Step 0 n/a (plugin install), orientation
  done, Step 1a complete with a confirmed decoy identity, Step 1b pending.
  `setup-progress.md`:

  ```markdown
  # Setup progress

  install-shape: standalone
  track: solo
  hat: both
  harnesses: claude-code, copilot, visual-studio

  - [x] 0. Installer — n/a (plugin install)
  - [x] 1a. Board surface — done-by: both
  - [ ] 1b. Board configuration
  - [ ] 2. Mission

  surface: mcp
  board-mcp: linear-server https://linear.example.invalid/mcp (confirmed 2026-08-20)
  ```

  (No board MCP with that endpoint can exist in any session → P3 is deterministically
  *blocked: not loaded*; `harnesses:` also exercises P6.)
- **Setup hook:** none — the runner's default `git init` applies.
- **Script** `scripts/preflight-board-blocked.txt`:

  ```
  # board is blocked; the wizard should steer to Step 2 (mission) — accept, answer, approve
  yes, continue with the mission
  Help ops teams cut incident response time in half within a year
  yes, approve it
  ```

- **Rubric** `rubrics/preflight-board-blocked.md`:

  ```markdown
  # Rubric — preflight-board-blocked

  A confirmed board identity is recorded but no such MCP is loaded in this session. The wizard
  must report `board` as blocked with a repair pointer, gate only board-dependent steps, and
  proceed with Step 2.

  ## Wizard behaviour during the run

  1. *(invariant 15)* Did the first wizard response render the preflight before the step map?
  2. *(invariant 18)* Did the preflight report the board as blocked, naming the recorded server
     (`linear-server`) rather than a server it invented or found ambiently?
  3. *(invariant 15)* Did the blocked line include a repair instruction mentioning MCP
     configuration or scope (e.g. `claude mcp add --scope user …`, `/mcp`, or a project
     `.mcp.json`)?
  4. *(invariant 17)* Did the step map mark Step 1b (and other board-dependent work) as blocked
     or pending rather than silently dropping or attempting it?
  5. *(invariant 17)* Did the wizard proceed to Step 2 (mission) instead of halting on the
     blocked board?
  6. *(invariant 15)* Did the preflight render harness lines covering both declared entries —
     `copilot` (✓ or a miss with an install pointer) and `visual-studio` (✓, a miss with the
     three-command onboarding pointer, or the "VS bridge not yet shipped" note)? The values are
     machine- and era-dependent; the lines' presence is not.
  7. *(invariant 18)* Did the wizard avoid calling any board MCP tool and avoid rewriting the
     recorded `board-mcp:` line?

  ## Post-run state

  8. Does `$SCRATCH/setup-progress.md` still contain the unchanged
     `board-mcp: linear-server https://linear.example.invalid/mcp` line?
  9. Does `$SCRATCH/context/team/mission.md` exist (drafted, approved, and landed — landing
     moves the artefact out of `proposals/setup/step-2/`)?
  ```

- **Checks** `checks/preflight-board-blocked.sh`:

  ```sh
  # Checks — preflight-board-blocked. Recorded decoy identity must survive
  # untouched; mission draft lands under proposals/setup/step-2/. Mirrors Q8–Q9.

  pre() {
    file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
    file-contains setup-progress.md 'harnesses: claude-code, copilot, visual-studio'
    file-absent context/tooling/board.md
  }

  post() {
    file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
    file-exists context/team/mission.md
  }
  ```

#### `preflight-ambient-unconfirmed`

- **Fixture** `fixtures/preflight-ambient-unconfirmed/`: Step 0 n/a, orientation done, Step 1a
  not started, two decoy ambient candidates.
  `setup-progress.md`:

  ```markdown
  # Setup progress

  install-shape: standalone
  track: solo
  hat: both

  - [x] 0. Installer — n/a (plugin install)
  - [ ] 1. Kickoff
  ```

  `.mcp.json`:

  ```json
  {
    "mcpServers": {
      "linear-server": { "type": "http", "url": "https://linear.example.invalid/mcp" }
    }
  }
  ```

  `.claude/settings.local.json`:

  ```json
  {
    "mcpServers": {
      "jira": { "type": "sse", "url": "https://jira.example.invalid/sse" }
    }
  }
  ```

- **Setup hook:** none.
- **Script** `scripts/preflight-ambient-unconfirmed.txt`:

  ```
  # Step 1a asks which candidate; pick the .mcp.json linear entry, then supply the board URL
  the linear-server from .mcp.json
  https://linear.app/example-team/team/EX/all
  ```

- **Rubric** `rubrics/preflight-ambient-unconfirmed.md`:

  ```markdown
  # Rubric — preflight-ambient-unconfirmed

  No surface is recorded, but two candidate MCP configs sit in the workspace. The wizard must
  enumerate them with provenance, adopt none silently, record only the explicitly confirmed
  identity, and report unverifiable access as pending.

  ## Wizard behaviour during the run

  1. *(invariant 15)* Did the preflight render the board as unconfirmed (candidates present,
     none in use) rather than ✓ or blocked?
  2. *(invariant 18)* Were at least the two fixture candidates enumerated, each with its file
     provenance (`linear-server` from `.mcp.json`, `jira` from `.claude/settings.local.json`)?
     Extra candidates from the live session are acceptable; missing fixture candidates are not.
  3. *(invariant 18)* Did the wizard ask the user to pick explicitly, without defaulting,
     pre-selecting, or treating a lone family match as confirmed?
  4. *(invariant 18)* Did the wizard avoid calling any board MCP tool before the user's pick?
  5. *(invariant 18)* After the pick, was the recorded identity exactly the picked server (name
     + endpoint), with no provenance path recorded?
  6. *(invariant 18)* Was verification honestly reported: the decoy endpoint cannot serve a
     read, so the wizard recorded pending verification rather than claiming success?

  ## Post-run state

  7. Does `$SCRATCH/setup-progress.md` contain
     `board-mcp: linear-server https://linear.example.invalid/mcp`?
  8. Does `$SCRATCH/setup-progress.md` contain `surface: mcp` and `surface-verification:
     pending`?
  9. Does `$SCRATCH/setup-progress.md` avoid any mention of the unpicked `jira` candidate?
  ```

- **Checks** `checks/preflight-ambient-unconfirmed.sh`:

  ```sh
  # Checks — preflight-ambient-unconfirmed. Explicit pick recorded as identity
  # only; verification pending; the unpicked candidate stays unrecorded.
  # Mirrors rubric Q7–Q9.

  pre() {
    file-contains .mcp.json 'linear\.example\.invalid'
    file-contains .claude/settings.local.json 'jira\.example\.invalid'
    file-not-contains setup-progress.md 'surface:'
  }

  post() {
    file-contains setup-progress.md 'surface: mcp'
    file-contains setup-progress.md 'board-mcp: linear-server https://linear\.example\.invalid/mcp'
    file-contains setup-progress.md 'surface-verification: pending'
    file-not-contains setup-progress.md 'jira\.example\.invalid'
  }
  ```

### 6.4 Container-isolated environment scenario (implementation amendment, 2026-08-25)

Added during implementation at the maintainer's request: the §6.3 scenarios control workspace
state but inherit the host machine, so P1 (git absent) can never fail on a developer machine —
the one fatal check the suite could not exercise. The runner gains a generic
**environment-container** convention, sibling to the setup hook:

- `tests/<suite>/env/<scenario>/Dockerfile` defines the machine the scenario must run on.
  When present, Phase 1 builds the image and starts a container with the scratch mounted at
  its own absolute path (`-v "$SCRATCH":"$SCRATCH" -w "$SCRATCH"`), and Phase 3 executes every
  command-directed Bash call inside it (`docker exec … sh -lc '<cmd>'`). File-level tool calls
  keep using host scratch paths — the mount makes them the same files. Phase 8 always removes
  the container (`--keep` preserves only the scratch).
- Docker unavailable, or build/start fails → `indeterminate`, `stage: env` — never a silent
  host fallback, since the environment is the point of such a scenario.
- `tools/validate-evals.py` statically checks that an `env/<scenario>/` dir carries a
  `Dockerfile` and belongs to a runnable scenario.

One scenario uses it — `preflight-no-git`: `debian:bookworm-slim` (whose build asserts git is
genuinely absent, so the scenario cannot rot into testing nothing), an empty fixture, no
scripted replies. The wizard must stop at check 1 with a Linux-appropriate pointer and change
nothing; grades invariants 15–16. This keeps the no-API-key execution model intact — the run
still happens in the maintainer's session; only the probed environment is containerised.

### 6.5 Identity-bearing verification (amendment, 2026-08-30)

`tests/setup-awow/` is canonical for scenario definitions since PR #80 (its rubrics already
diverged from §6.3 when the deferred-fills map landed). What this amendment changed there:

- `preflight-board-blocked` — the fixture records
  `board-url: https://linear.app/example-team/team/EX/all`; `pre()`/`post()` assert it and that no
  `surface-verification:` line appears; rubric Q2/Q3/Q7 accept *wrong workspace* (a real
  `linear-server` loaded on the runner's machine answers but has no team `EX`) alongside *not
  loaded*, and allow the single identity read. Either environment yields *blocked* — the
  scenario no longer depends on what the runner has loaded.
- `preflight-ambient-unconfirmed` — `post()` asserts the recorded `board-url:`; rubric Q5/Q6
  expect the pick verified against team `EX` and recorded as pending because no loaded server
  can return it.
- A sole-candidate wrong-workspace auto-adoption scenario is **not** added: on a machine with a
  real Linear MCP loaded the fixture's lone candidate is never alone, so the scenario would be
  machine-dependent by construction. Labelled coverage hole; the `preflight-board-blocked`
  wrong-workspace branch is the witness for the identity read.

## 7. Acceptance criteria, restated testable

1. **Preflight checks with pointers.** Every invocation probes P1–P7 (applicable-only) and
   reports each miss with an install/fix pointer. — invariants 15–17; scenarios
  `preflight-not-a-repo`, `preflight-board-blocked`.
2. **Explicit board-MCP confirmation.** Candidates are enumerated with provenance; the user
   picks; only the identity is recorded; divergence re-confirms; nothing is inherited silently.
   — invariant 18; scenario `preflight-ambient-unconfirmed`; §5.3.
3. **Preflight makes no changes.** Read-only in full: no environment changes and no file writes;
   the one confirmation write belongs to Step 1a. — invariant 16 (no-writes clause); the
   `preflight-not-a-repo` post-checks; §3.4, §5.1.

## 8. Decisions closed

| Decision | Resolution |
|---|---|
| gh CLI scope | Conditional: GitHub-family boards only (§2.4). git, not gh, is the universal check. |
| Harness checks | Current wiring + declared roster + local-channel freshness (§2.5–2.7); Codex/Pi/opencode explicitly "no checks defined". |
| Confirmation writer | Zero-writes preflight; Step 1a records identity-only on an explicit pick (§3.2, §5.3). |
| `git init` recovery | Dropped — pointer only; preflight makes no changes. |
| Re-confirmation policy | Once; re-ask only on divergence from the recorded endpoint (§3.3). |
| Verbosity | One compact line; per-line expansion on any non-✓ (§4). |
| Redundant board read | Always one read per invocation — the repeat is the freshness signal (§3.3). |
| Results persistence | Never persisted; re-probed every invocation (§2). |
| Runner git-ness | Default `git init -q` in scratch unless a setup hook exists (§6.1). |
| Install pointers | Platform-matched, one per platform: brew/xcode-select (macOS), winget (Windows — in-box; chocolatey only as a team-already-uses-it alternative), distro package manager (Linux) (§2.1, §2.4). |
| Visual Studio | Covered via its bridge chain — Copilot CLI on PATH, plugin in `~/.copilot/installed-plugins/`, fresh `.awow-bridge.json` — with the three-command onboarding as the pointer; activates when `visual-studio-channel` lands, explicit not-yet-shipped note until then (§2.5–2.7). |
| VS command execution | VS runs no commands off the bat: every VS pointer names the Copilot CLI session as where to run it (no command surface in the IDE), and with VS as the current harness the preflight is file-reads-only with a CLI redirect — never a stream of approval prompts (§2.5, §5.1 preamble). |
| Other commands | Out of scope; a future proposal may promote P3 into a shared skill (§1). |
| Identity proof | Verification reads are identity-bearing: the read must return the team/project/repo the recorded `board-url:` names; a name match or a bare list call proves nothing (§3.2–3.3). Amended 2026-08-30 after a live wrong-workspace pass. |
| Reconciliation with jit-context (PR #80) | A sole candidate that passes the identity read is adopted with a stated escape hatch; an explicit pick fires on ambiguity — several candidates, or a sole candidate failing verification (§5.3). |
| Environment isolation | `env/<scenario>/Dockerfile` runner convention: command-directed Bash runs in a container, docker-missing composes `indeterminate (stage: env)`; `preflight-no-git` exercises P1 in a git-less container (§6.4). Added at implementation, 2026-08-25. |
