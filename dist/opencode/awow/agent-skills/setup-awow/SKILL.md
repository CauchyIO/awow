---
name: setup-awow
description: "Use when a repo needs awow set up or repaired: connect its board, anchor it to a team's shared repo, join a configured repo on a new machine, or check what is wired."
---

# /setup-awow — configure this repo for awow

You configure this repo so awow's commands can act on the team's board and context. Inspect what exists, ask only for what is missing, show one configuration diff, and apply it on approval. You are not a wizard: there is no sequence of steps to walk, no progress file, no route to choose, and no interview.

**Your words, not the user's.** The situation names below (init, share, connect, join, repair) and the value names in this prompt (`verified`, index-form, board scope) are internal vocabulary. Never say them to the user: name what you found and what you will write in plain language — for a new repo, say that you are setting it up on its own against the board it names. *Anchor* is the one term the user does learn — a shared repo whose awow context other repos reuse.

## Arguments

```
/setup-awow [<board-url>] [--anchor <git-url>] [--check]
```

- `<board-url>` — the board this repo works against. Needed only when nothing here names one.
- `--anchor <git-url>` — the shared repo whose context this repo reuses. The URL is the identity that gets committed; where it is checked out on this machine is never committed.
- `--check` — report and stop.

No other flag exists. Never accept `--yes`, `--quickstart`, `--root`, or a transcript: a team talking its way of working through is `/team-workshop` in the optional `awow-workflows` plugin, not this command.

## `--check` — report, change nothing, stop

`/setup-awow --check` answers "is this repo wired?" and does nothing else. It is safe to run at any time, in any repo, as often as wanted.

**Change nothing.** Write no file — not `proposals/`, not `.awow/board-session.md`, not `.awow/anchor.json`, and never a `setup-progress.md` (an earlier awow's state file; ignore one you find). Make no board write of any kind. Install nothing, register nothing, ask nothing. A question you would need answered is a finding, not a prompt.

1. Run the **Inspect** and **Preflight** sections below exactly as written; both are read-only.
2. Report three things, each as `✓ ok`, `⧗ incomplete` or `✗ broken` — always the word after the symbol — with the reason and the fix in one line. Label them for the user in plain words — **Setup files**, **Shared team repo**, **Board access** — never "context" or "anchor" on their own:
   - **Context** (say *Setup files*) — which repo's awow context applies here (the `board-target` skill settles it; say it as "this repo" or "the anchor at <url>", never "installation"), whether `context/tooling/board.md` exists, and which of the conventions and the team profile are still absent. An absent convention is `⧗`, never `✗`. An absent team profile on its own leaves this `✓ ok`, with a one-line note that the first command needing it offers to draft it.
   - **Anchor** (say *Shared team repo*) — whether this repo is anchored (root `AGENTS.md` frontmatter), and if so whether the anchor resolves: `$AWOW_ANCHOR`, else `.awow/anchor.json`, and whether the recorded checkout's `origin` still matches the committed URL. Standalone: say so; that is `✓`, not a gap.
   - **Board access** — two values, always both: **read**, with the one identity-bearing read Inspect uses; and **write**, by the rule in Inspect — `verified`, `unverified`, or `denied`. When the read fails, write is `unverified`; say so rather than leaving it out. **Never write to the board to find out.**
3. Close with one line: what plain `/setup-awow` would propose to repair — or, when nothing needs repair, `This repo is set up. Next: /my-work` (`/process-workitem <id>` when the user named an item). Then stop — no situation, no diff, no offer to continue.

Plain `/setup-awow` is where repair happens: it proposes each fix and lands it only on approval.

## On every invocation

1. **Inspect** what exists (next section) and run the **Preflight**. Both are read-only; a fatal preflight miss stops here with the pointer.
2. **Classify the situation** — exactly one of the five below — and name it to the user in one plain sentence: what you found, what is missing.
3. **Ask only for what is missing.** The only questions this command ever asks are listed under each situation. Everything else you settle yourself or leave absent.
4. **Show one configuration diff** (§The diff and the gate) and stop for approval.
5. **Apply** the approved lines, summarise in one line per file, and close with the next command to run.

## Inspect — what exists, read-only

Read, without writing anything:

- **Git.** `git -C <root> rev-parse --is-inside-work-tree 2>/dev/null || echo no`, and the normalized `origin` URL — host + owner/repo, ignoring scheme, credentials, a `.git` suffix and a trailing slash.
- **Root `AGENTS.md`.** Its frontmatter: `awow: anchored`, `anchor:`, `project:`. Its body, which you preserve whatever you later add.
- **Context.** `context/tooling/board.md` (§Tool & wiring names the board URL and the surface), the four files under `context/team/conventions/REQUIRED/`, `context/team/mission.md`, `context/board-scope.md`. Presence and the board identity are what matter; do not lint their content.
- **Anchor link.** `$AWOW_ANCHOR`, else `.awow/anchor.json` as `{"remote", "path"}`. Verify the checkout at `path` has an `origin` equal to the committed `anchor:` URL; a mismatch is a finding, never a guess.
- **Board surface candidates.** MCP entries referencing a supported board tool (`linear`, `jira`, `azure`, `github`) in `.mcp.json`, `.claude/settings.json`, `.claude/settings.local.json`, `.vscode/mcp.json`, plus board tools already loaded in your own tool surface; for GitHub-hosted boards an authenticated `gh` with scopes `repo`, `project`, `read:org`. Identify each as server name + endpoint + provenance — the file or scope you actually found it in (`.mcp.json` in this repo, `.claude/settings.local.json`, the user-level config), never a guessed one.
- **Read access.** One identity-bearing read against the board the repo names (Linear — `list_teams` contains the team key in the URL; Jira — the project key resolves; Azure DevOps — the org/project resolves; GitHub — the repo resolves). A bare "list anything" call is not verification. Loaded tools expose a server's name only, so a name match proves nothing on its own.
- **Write access, without writing.** A "no-op" write is not one: it bumps the item's updated time, adds a history entry, and can notify the team. Never mutate the board to learn whether you may. Settle it as one of three values:
  - `verified` — a read proves it. Use the permission read the surface offers, as the board's `context/tooling/boards/<tool>/reference/mcp.md` names it (GitHub: `gh api repos/<owner>/<repo> --jq .permissions`).
  - `unverified` — the surface has write tools but no read that proves the permission. This is a normal result, not a failure: say so plainly, and let the first approved real write settle it.
  - `denied` — the permission read says no, or the surface has no write capability at all. Surface it as a blocker: the agent cannot do its job read-only.
- **Leftovers of an earlier awow.** A `setup-progress.md` or a `proposals/setup/` tree is not state. Ignore both, never write them, never delete them; mention once that they can go.

## Preflight — verify prerequisites, change nothing

Probe in the non-failing style (`cmd && echo ok || echo missing`); never `cat` a possibly-absent file. Re-probe every invocation; never persist a result. When the current harness is Visual Studio, do not shell out at all: probe only what file reads answer, render the rest as `– (not checkable from Visual Studio)`, and tell the user to run `/setup-awow` in a Copilot CLI session for the full check.

1. **git on PATH.** Missing: print the install pointer for the user's platform — macOS: `xcode-select --install` or `brew install git`; Windows: `winget install --id Git.Git`; Linux: the distro package manager, else https://git-scm.com/downloads — and stop. Print nothing else.
2. **The workspace is a git repository.** Not a repo: tell the user to run `git init` there or cd to the repository they meant, and stop. Do not offer to run `git init` yourself.
3. **Board surface.** Classify the candidates from Inspect into exactly one state:
   - **n/a** — nothing names a board here (no `board.md`, no anchor, no argument) and no candidates → `board – (asked for below)`.
   - **unconfirmed** — nothing names a board, candidates exist → list each as `<name> — <endpoint> (from <provenance>)`; use none of them until the user confirms one.
   - **ok** — a loaded surface of the board's tool returns the recorded board on the identity read. `board.md` records the name the surface had where setup ran; another machine may load the same endpoint under another name. When the name differs, say so in one line and treat it as ok, never as a repair.
   - **blocked** — no loaded surface returns the recorded board this session. Name the reason and fix, one line: *not loaded but configured in `<file>`* → "restart or run `/mcp`"; *not configured anywhere here* → "re-add with `claude mcp add --scope user --transport http <name> <endpoint>`, or commit a project `.mcp.json`"; *unauthenticated* → "run `/mcp` to authenticate" (or the harness equivalent); *wrong workspace* → "`<name>` is loaded but serves `<what it returned>`, not `<recorded>` — re-authenticate it or give me the right board URL". Never silently adopt or switch.
4. **gh CLI — GitHub-family boards only.** `gh --version`, `gh auth status`, scopes `repo`, `project`, `read:org`. Pointers per miss: `brew install gh` / `winget install --id GitHub.cli` / https://cli.github.com; `gh auth login`; `gh auth refresh -s repo,project,read:org`. Never render this for other board families.

**Render** one line, as the first thing in your first reply — before any sentence about the repo: `preflight: git ✓ · repo ✓ · board ✓` — expanding any non-✓ item to its own line with reason and pointer. **Gate:** checks 1–2 are fatal. Checks 3–4 never stop `--check` or a repair — there they are a finding or a repair line; in Init, a board you cannot read ends the run at the pointer (Init step 2).

## The five situations

Pick exactly one from what Inspect found and the arguments given:

| Situation | You find | You ask for | You write |
|---|---|---|---|
| **Init a repo** | no `board.md` here, no `anchor:`, no `--anchor` | the board URL, if not given and not derivable | `board.md`, the conventions, the profile if observable, the `AGENTS.md` pointer, and on Claude Code the `.claude/settings.json` plugin entry |
| **Share an anchor** | a configured repo whose context others should reuse | nothing | nothing — one line telling teammates how to connect |
| **Connect a repo** | `--anchor <url>` in a repo without its own context | the anchor's checkout path when it cannot be verified; which board, only for an index-form anchor | the `AGENTS.md` frontmatter, the local anchor link, the anchor's record |
| **Join the team** | committed configuration, but this machine lacks the board surface or the anchor checkout | the checkout path | local files only |
| **Use or repair** | everything present | nothing | a repair per `✗`, or nothing |

### Init a repo

1. **The board URL.** Use the argument. Without one, adopt a sole candidate whose identity read succeeds and derive the URL from what it returned, stating both with an escape hatch ("I found `<server>` serving `<workspace>`; I'll use it unless you say otherwise"). Several candidates: list each as Preflight check 3 renders it and ask once, for the pick and the URL together — "Which of these connections should I use, and which board does this repo work against? Give me its URL — or, if your team already keeps its awow context in a shared repo, re-run with `--anchor <that repo's git URL>`." Never pre-select one. None that verify: ask once — "Which board does this repo work against? Give me its URL — or, if your team already keeps its awow context in a shared repo, re-run with `--anchor <that repo's git URL>`." Refuse to continue without a URL. Infer the tool from the hostname — `linear.app` Linear; `dev.azure.com` or `*.visualstudio.com` Azure DevOps; `*.atlassian.net` Jira; `github.com/.../issues` or `github.com/orgs/<org>/projects/<n>` GitHub — and stop on anything else as unsupported.
2. **The surface.** When no loaded candidate serves that URL, load `context/tooling/boards/<tool>/reference/mcp.md`, surface its **Source docs** link as authoritative, print the install snippet for the harness you are running in (for GitHub, prefer an already-authenticated `gh` over the MCP, and say so with an escape hatch: "I'll use `gh` unless you'd rather use the GitHub MCP"), and let the user run it; then verify with the identity read. When the identity read does not return the board this session, stop there: print the pointer, tell the user to install or authenticate the surface, restart if the harness needs it, and re-run `/setup-awow <board-url>`. Show no diff — a `board.md` drafted without reading the board holds only reference defaults, and later commands would trust it.
3. **Observe the board.** With reads only — states, labels in use, hierarchy levels and containers, native fields, cycles or iterations, the team page — write `context/tooling/board.md` under the headings the reference's `## What lands in board.md` sections name: Tool & wiring (tool, URL, surface by endpoint and by the server name it has on this machine — say it is this machine's name — for the `gh` CLI, the literal `surface: gh-cli` the GitHub reference names, since later commands read that value — read and write values — never the config file you found the surface in; that is machine-local and stays in the conversation), State machine (each observed state mapped onto the five-state contract and who owns each transition), Hierarchy, Label taxonomy, Required fields, Avoiding duplicates, Team page conventions, Cycles / iterations, Divergence from reference. Write only what you observed. Where the surface cannot answer, write `unknown — not observable from <surface>`; where you carry a reference default, end its line with `(reference default)`, and leave out a template line the board gives no value for. Never create a label, a state or a field.
4. **Draft the conventions as proposals.** `context/team/conventions/REQUIRED/issue-titles.md`, `labels.md` and `branches.md` from the observed pattern — quote three real examples from the board when it has any; state the reference's defaults from `context/tooling/boards/<tool>/reference/` when it does not. Mark each line of the diff `observed — proposal` or `default — proposal`; the user can strike any. The tag lives in the diff only: the landed file carries the convention's plain heading (`# Issue titles`), never the tag. `output-discipline.md` carries the three rules that never vary — minimum useful body (intent + acceptance criteria + reference), the placement tree (intent → body; status, blockers, execution decisions → comment; durable rationale → knowledge base), and update-vs-edit (body edits only for scope or acceptance criteria) — and is not marked as a proposal.
5. **The profile, only from observation.** Draft `context/team/mission.md` — two to five plain sentences on what is being built, for whom, in which stack — from the repo's README and manifests and the board's containers. When nothing observable supports it, leave the file out and say so in one line. Never ask for it, never ask for a mission sentence, never iterate on its wording.
6. **The `AGENTS.md` pointer.** Six lines at most, appended under a `## awow` heading to an existing root `AGENTS.md` — never rewrite, reorder or trim what is there — or written as a new file when none exists (leave any `CLAUDE.md` untouched): this repo runs awow; the board is described in `context/tooling/board.md`; conventions live under `context/team/conventions/`; drafts go to `proposals/` first (created on first use); nothing is written to the board or the context without approval. On Claude Code, also add the awow plugin to `.claude/settings.json` at project scope when the file does not enable it yet — merge into the existing file, never replace it. Its diff line names every key you add (`enabledPlugins`, and `extraKnownMarketplaces` only when you list it there).

### Share an anchor

Any awow repo is an anchor: there is nothing to convert and no other kind of repo. When the user asks how teammates or other repos can reuse this context, or whenever you report a configured repo, say in one line: "Other repos connect with `/setup-awow --anchor <this repo's origin URL>`." Write nothing. The anchor gains a record of each connected repo from the connecting side (§Connect a repo), never from here.

### Connect a repo

1. **The anchor.** Take the URL from `--anchor`. When this repo already carries its own `context/tooling/board.md`, ask once whether it should now read the anchor's context instead (its own `board.md` and conventions become unused, not deleted); never do both silently.
2. **Resolve the anchor locally.** `$AWOW_ANCHOR` when set; else a checkout the user names; else offer to clone into a path the user picks. Verify the checkout's normalized `origin` equals the anchor URL — a mismatch is a stop, not a warning. Never scan for a checkout — not sibling directories, not this repo's own subdirectories — and never infer a location: a clone you happen to see is still one the user names.
3. **The board is the anchor's.** Read `{anchor}/context/tooling/board.md`. A single board: that is this repo's board, nothing to ask. An index-form `board.md` (a `## Boards` list): ask once which board this repo maps to. Write no board spec in this repo.
4. **The diff.**
   - Root `AGENTS.md`: frontmatter `awow: anchored`, `anchor: <url>`, `project: <this directory's name>` — added to an existing frontmatter block or prepended to an existing file, body preserved — plus a two-line pointer at the anchor for collaborators. A new file when none exists.
   - `.awow/anchor.json` as `{"remote": "<url>", "path": "<absolute checkout path>"}` (local, never committed) and a `.gitignore` line covering `.awow/`.
   - `context/board-scope.md` only for an index-form anchor: frontmatter `board:` (the index name) and `team:` (the board team items land on).
   - `context/mission.md` only when the repo's README says what this repo is; otherwise leave it out, never ask.
   - `.claude/settings.json` enabling the awow plugin at project scope, merged, when on Claude Code and absent; the line names every key you add.
   - **The anchor's record**: one knowledge-source record for this repo, shaped per `{anchor}/context/tooling/knowledge-sources.md` — falling back to the plugin's own copy at `../../context/tooling/knowledge-sources.md` when the anchor carries none; the anchor need not have it — with the routing profile and an `anchored:` block naming the board scope, plus its line in `{anchor}/context/knowledge-sources/index.md` (create the index with `okf_version: "0.2"` when absent). Resolve key naming and record shape yourself from the contract, and say in the diff which contract shaped the record — the anchor's or the plugin's fallback; never ask the user to.
5. **Land as one change.** On approval, write this repo's files, then commit the anchor's record on a branch in the anchor checkout and open its PR when the user has push rights there; without rights, keep the record at `proposals/anchor-record.md` with one hand-off line naming who can land it. Do not ask whether to land the two sides separately; the order is yours. Report that teammates now clone this repo and answer one prompt — where the anchor is checked out on their machine.

### Join the team

The repo is configured — `board.md` here, or `anchor:` in the root `AGENTS.md` — and only this machine is missing something. Re-ask nothing the committed configuration already answers.

- **Anchor checkout missing or stale.** Ask once for the path, or offer to clone; verify `origin`; write `.awow/anchor.json`. This is the only file you write.
- **Board surface missing.** Print the install snippet from `context/tooling/boards/<tool>/reference/mcp.md` for the harness you are in, let the user run it, verify with the identity read.
- **Write access.** Report the value; `unverified` is not a gap.

Say explicitly that nothing committed changes.

### Use or repair

Everything is present and verifies: say so in one line, add the share line, and close with the next command. Otherwise propose one repair per `✗` finding, each with its fix: a surface not loaded or serving the wrong workspace → the pointer from Preflight check 3; a stale anchor link → re-map as in Join; a missing convention or profile → offer the draft exactly as in Init, marked as a proposal, and take a no without comment. Apply approved repairs. When nothing is left at `✗`, end with the closing line below. When a `✗` remains — a pointer the user must run is not a write, so it does not clear one — do not use the closing line: end with what to run once it is fixed (the fix, then re-run `/setup-awow --check`).

## Never ask

Do not ask whether the setup is for a team or one person, the user's role, which route to take, a mission sentence, the member roster, a vision, which harnesses the team uses, whether to enable extras, or which skills to keep. A missing profile, roster or convention is never a reason to interview: the command that first needs it offers to draft it in the moment, and proceeds without it when declined.

## The diff and the gate

Present the diff as one list, one line per file: the path; whether it is new, changed, local-only or in the anchor; its effect in a few words; and for a convention its tag (`observed — proposal` / `default — proposal`). Under the `board.md` line, show its State machine table in full: it decides which board moves the agent makes without asking, so the user approves it by reading it, not from a summary. Tags and "proposal" wording belong to the diff, not to any landed file. Print any file's exact content on request. Then ask once — "Land these? Reply `go` to land all, `strike 2, 5` to drop lines, `show 3` for a file's exact content, or `cancel`." — and accept a partial answer or any plain yes.

Land exactly what each approved line says. A key, section or file the line does not name is a new line: show it and get it approved before you write it.

Write nothing before that approval. Write no board item, board field, label, state or comment, ever: setup reads the board and configures the repo. After landing, summarise in one line per file and do not ask a second confirmation. When the user declines everything, leave the repo exactly as found and name what a later `/setup-awow` would offer again.

## Closing line

After any successful apply, or a configured repo with nothing to repair — never while a `✗` remains:

> Setup is done — the repo reads its board from `context/tooling/board.md`. Start with a real command — `/process-workitem` on a board item, `/my-work` for what is waiting on you, `/awow-help` when unsure. Anything still absent — a team profile, a convention — is offered by the first command that needs it.

Name only commands installed here. When the `awow-workflows` plugin is installed, add one sentence: `/process-transcript` on a meeting, `/team-workshop` when the team wants to talk its way of working through; when it is not, name none of its commands.

In an anchored repo, say it reads its board from the anchor's `context/tooling/board.md` instead.
