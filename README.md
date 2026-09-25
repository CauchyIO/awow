<p align="center">
  <img src="assets/cauchy.svg" alt="Cauchy" width="64">
</p>

# awow — Agentic Way of Working

<p align="center"><em>Helping humans work better together, using AI.</em></p>

awow gives a coding agent your team's context: the board it reads, the
conventions it follows, and commands for the work that happens between people.

A coding agent is only as useful as what it starts with, and on most teams that
starting context is scattered. The board lives in one tool, the conventions live
in heads and wiki pages, and every agent product — Claude Code, Codex, Pi,
Copilot, opencode — wants its own copy of the instructions. Each copy drifts,
and every session begins from zero.

awow packages the missing pieces and ships them as a plugin:

- **Working rules** every session starts from — go to the board before starting
  work, write or update the ticket, keep the admin current as you go.
- **Commands** for the work that happens between people: a board item walked
  from refinement to an opened PR, a refinement session prepared in advance, a
  meeting recording turned into decisions, owners, and board items.
- **A `context/` folder your team owns** — board wiring, mission, conventions,
  members — that every command reads, and that stays yours rather than being
  baked into the tool.

It is markdown throughout, authored in one source tree and built into a package
each agent product installs, so there is one copy to keep current instead of
five. Nothing the agent drafts reaches your board or your repo until you have
seen it and approved it.

The full technical guide lives [here](guides/README.md).

## Four terms

| Term | Meaning |
|---|---|
| **core** | The `awow` plugin itself: `/awow-help`, `/setup-awow`, `/process-workitem`, `/my-work`, `/update-context`. Everything else ships as a separate, optional plugin. |
| **anchor** | A repo whose committed `context/` other repos reuse. Any awow repo can be one; nothing marks it as special. |
| **anchored repo** | A repo that reads an anchor's context instead of carrying its own. Its root `AGENTS.md` commits the anchor's git URL; where that anchor sits on your machine stays out of git. |
| **scope** | Which board — and which of its teams' items — a repo's work belongs to. Recorded in `context/board-scope.md` when an anchor serves several boards. |

## Before you install

- **A supported harness**, installed and signed in: Claude Code, Codex, Pi,
  the GitHub Copilot CLI, or opencode.
- **The `gh` CLI, authenticated** (`gh auth login`). Commands use it to open
  PRs, and it doubles as the board surface for GitHub-hosted boards.
- **Access to your team's board** — an account that can read and write it.
  Nothing needs wiring yet: `/setup-awow`'s first required step installs and
  verifies the surface the agent will use — an MCP server for Linear, Jira,
  or Azure DevOps, or `gh` for GitHub Issues and Projects — and records it
  in `context/tooling/board.md`.

## Installing the plugin

A **plugin** is how an agent product installs and versions an extension: one
bundle of commands, skills, and supporting files, added from a **marketplace**
(a catalog of plugins) and updated like any other dependency. awow ships as one
such bundle. Each product documents its own plugin model —
[Claude Code](https://code.claude.com/docs/en/discover-plugins),
[Codex](https://learn.chatgpt.com/docs/plugins),
[Pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)
(which calls them *packages*), and
[GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-cli-plugins).

To install awow, run the commands for the agent product you use — one block
only, not all five:

Claude Code:

```
/plugin marketplace add CauchyIO/awow
/plugin install awow@awow
```

Codex:

```
codex plugin marketplace add https://github.com/CauchyIO/awow-dist
codex plugin add awow@awow
```

Pi:

```
pi install git:github.com/CauchyIO/awow-dist
```

GitHub Copilot (requires the Copilot CLI):

```
copilot plugin marketplace add CauchyIO/awow
copilot plugin install awow@awow
```

opencode:

```
opencode plugin awow@git+https://github.com/CauchyIO/awow-dist.git
```

Claude Code and Copilot install from this repo, which carries a marketplace
manifest for each. Codex, Pi and opencode install from `awow-dist`, which
carries the built payload. Copilot exposes the commands as skills rather than
slash commands.

**Then type `/awow-help`** in the repo you want to work in. It says where that
repo stands, names anything that needs fixing, and gives you one next step —
so you never have to guess which command comes first.

### The workflows bundle

`awow` is the core: `/awow-help`, `/setup-awow`, `/process-workitem`,
`/my-work` and `/update-context`. The broader workflows — meeting
transcripts and retros, design and planning, digests, strategy and OKRs,
knowledge capture, styled documents — ship as a second, optional plugin,
`awow-workflows`. Install it beside `awow` in the repos where those
conversations happen:

| Agent product | Install the bundle |
|---|---|
| Claude Code | `/plugin install awow-workflows@awow` |
| Codex | `codex plugin add awow-workflows@awow` |
| GitHub Copilot | `copilot plugin install awow-workflows@awow` |
| Pi, opencode | nothing to do — see below |

Each plugin is self-contained; `awow-workflows` declares no dependency on
`awow`, but expects a repo already configured by `/setup-awow`. Pi and opencode
install a whole repository as one package and cannot add a plugin from a
subfolder, so their `awow` package already carries the core and the bundle
together.

## First: run `/setup-awow`

`/setup-awow` connects your board (Linear, Jira, Azure DevOps, GitHub Issues) and writes what it
observed there into `context/` — the context every other command reads. It is one command, not
a wizard: it inspects what the repo already has, asks only for what is missing, shows one
configuration diff, and applies it when you approve.

```
/setup-awow <board-url>                 # set this repo up against its board
/setup-awow --anchor <git-url>          # connect this repo to a team's shared repo
/setup-awow                             # on a configured repo: check and repair
/setup-awow --check                     # report, change nothing
```

It works two ways, and asks nothing up front: **standalone**, where this repo gets its own
`context/`, or **anchored**, where it reads a shared repo's instead. What it asks and writes in
each case, and how to undo it, are on one page — **[SETUP.md](SETUP.md)**.

The other commands do run without setup — they ask for what's missing and carry on — but they
work better with it. Nothing about your team is interviewed for: a team that wants to talk its
way of working through runs `/team-workshop` from the optional `awow-workflows` plugin.

## Then: explore the commands

The commands work in any repo (anchor or anchored). Each carries a one-line
description of the situation it applies to, so you can describe what you need
instead of typing the command name. The list below is generated from those
descriptions; `/awow-help` shows the same list inside a session.

<!-- COMMAND-CATALOG:START — generated by tools/gather.py, do not edit -->
### `awow` — the core

| Command | Use when |
| --- | --- |
| `/setup-awow [<board-url>] [--anchor <git-url>] [--check]` | Use when a repo needs awow set up or repaired: connect its board, anchor it to a team's shared repo, join a configured repo on a new machine, or check what is wired. |
| `/process-workitem <item-id> [explain | refine | plan | implement]` | Use when the user points at a board item — a ticket ID, issue link, or “let's pick up X” — and wants it explained, refined, planned, or carried through a code change to an opened PR. |
| `/my-work` | Use when the user asks what they should work on, what is pending or waiting on them, or says they have lost track of the board and want to get oriented before starting a block of work. |
| `/update-context` | Use when a session is wrapping up — a commit, a PR, a sign-off — and the user stated a durable rule about how the team works, so it lands in the context tree. |
| `/awow-help [--commands | <command> | what you want to do]` | Use when the user asks what awow can do here, what a command does, what to run next, or has just installed the plugin and does not know where to start. |

### `awow-workflows` — the optional bundle

| Command | Use when |
| --- | --- |
| `/artifact` | Use when the user asks for a deck, slides, a blog post, one-pager, or report as HTML or PDF — any styled document that should follow the team's house style instead of hand-written CSS. |
| `/board-lifecycle [--check] [--snapshot <path>] [--ledger]` | Use when the board's project layer needs governing — projects without owners or end conditions piling up, nobody sure which containers are alive, or a planning round that needs a trustworthy project overview first. Declares shapes and horizons, sweeps the estate, and turns expiry into a visible exception instead of silent rot or a silent auto-close. |
| `/daily-checkin [path to a written or voice account, e.g. checkins/<user>/YYYY-MM-DD.md] (optional — omit to capture live or to reconstruct from board + code)` | Use when the user recounts their day, points at a check-in note or voice memo, or wants the board to reflect today's work — end-of-day logging, standup prep, catching untracked work. |
| `/daily-digest [--week | YYYY-Www | YYYY-MM-DD] (optional — omit for today)` | Use when the user asks what the team shipped today or this week, wants a daily or weekly digest written up and raised as a PR, or says they have no idea what other people are working on. |
| `/design-system` | Use when the user wants one house style for the HTML they generate — asks to stand up or adopt a design system, points at a site or brand to derive tokens from, or says every deck looks different. |
| `/handover [who it is for, e.g. 'my morning read' or 'another agent to challenge the design'] (optional — omit and you will be asked)` | Use when a session's work must survive it — the user asks for a handover, a resume prompt or a brief for another agent, says they are signing off, switching sessions, running out of context, or wants to pick this up tomorrow. |
| `/kb-mine` | Use when the user asks what's worth writing down from a day's work, wants to backfill knowledge-base candidates for a past day, or says hard-won insight is evaporating unrecorded. |
| `/kb-synthesize` | Use when mined knowledge candidates are piling up unpromoted, or the user asks to drain the KB inbox, review staged candidates, or fold recent learnings into the durable knowledge base. |
| `/okr-cascade` | Use when a department's quarterly OKR cascade needs attention — starting the quarter's objectives, refining key results, translating objectives into team PI-plan proposals, or reviewing drift and KR movement partway through the quarter. |
| `/process-retro` | Use when the user points at or pastes a retrospective transcript or recording notes, or asks to turn a retro into named anti-patterns, owned actions, and diffs to their agent instructions. |
| `/process-transcript` | Use when the user hands over a meeting transcript or recording notes (.vtt, .srt, pasted text), or asks to turn a meeting, standup, refinement, or stakeholder interview into board items. |
| `/project-plan [path to a design artefact from /solution-design-flow, or a parent work-item ID] (optional — omit to be asked)` | Use when a design is locked and decomposed but nothing says what blocks what — the user asks for build order, sequencing, a delivery plan, or a critical path, or just finished /solution-design-flow. |
| `/refinement-prep` | Use when the user has a feature brief, quarterly slidedeck, or board issue and wants it broken into right-sized stories before a refinement session, or asks to prep work for the next refinement. |
| `/setup-department` | Use when a department repo has no identity or OKR surface yet, or the user asks to stand up a department, register a team submodule, or scaffold the department's quarterly OKR doc. |
| `/solution-design-flow` | Use when the user is weighing architectural or solution options, is about to lock a design decision, or points at a transcript of a design discussion — before the decision only exists in chat. |
| `/strategy-flow` | Use when a team or department has a vision but no measurable goals yet — the user wants to name strategic bets and refine each into committed and aspirational KRs with baselines and dated targets, landed as a draft OKR set. Start-of-quarter, or whenever the strategy layer above the board is missing. |
| `/team-workshop [prepare | <transcript.vtt|.srt|notes.md>]` | Use when a team wants to talk its way of working through and needs a meeting brief, or has the workshop transcript back to turn into team context proposals. |
<!-- COMMAND-CATALOG:END -->

## What the agent picks up

- **awow's [working rules](.agents/skills/using-awow/SKILL.md)**, read at the
  start of every session: go to the board before starting work, write or update
  the ticket, and keep the admin current while you work.
- **Your team context**, where it exists — the `context/` that `/setup-awow`
  writes, read by whichever commands need it.
- **An optional OKF catalog**, which routes commands to canonical repositories,
  SharePoint, or vector-backed sources without copying that material into the
  anchor.

## Going deeper

The comprehensive guides live in [`guides/`](guides/README.md) — plain markdown, readable
directly on GitHub or as agent context.

Once the commands are part of how the team works, the next question is usually
whether they are helping. `awow-telemetry` is a second plugin for measuring how
the way of working is going: session timelines, prompt-quality review, usage
coaching. It runs on Claude Code only.

## Contributing to awow

- **`.agents/` is the source.** `tools/gather.py` builds it into one
  self-contained plugin per harness, under `dist/<harness>/<plugin>/`. CI fails
  on drift with `--check`.
- **Nothing is mirrored into this repo's `.claude/` or `.github/`.** The
  marketplace that Claude Code and Copilot install from *is* this repo. A merge
  to `main` is therefore what reaches a maintainer's own sessions, after
  `/plugin marketplace update awow` and then `/plugin update awow`.
- **`/test-awow` is the one exception.** The eval runner lives in this repo's
  `.claude/commands/` rather than in the payload.

To exercise a branch's payload before it merges:

```bash
python tools/gather.py && claude --plugin-dir dist/claude/awow
```

## Status

**v1.0.0 — first public release.** Working end to end: the installs on all five
harnesses, the command set, canonical knowledge-source routing, the session
context, and the build with its drift check in CI.

What each release changed is in [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT. See [`LICENSE`](LICENSE).
