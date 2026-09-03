<p align="center">
  <img src="assets/cauchy.svg" alt="Cauchy" width="64">
</p>

# awow — Agentic Way of Working

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

Claude Code and Copilot install from this repo, which carries the marketplace
manifest both read. Codex, Pi and opencode install from `awow-dist`, which
carries the built payload. Copilot exposes the commands as skills rather than
slash commands.

## First: run `/setup-awow`

`/setup-awow` is the first command to run after installing the plugin. It
wires your board (Linear, Jira, Azure DevOps, GitHub Issues) and writes your
mission, conventions, and members into `context/` — the context every other
command reads.

Its first question is which of two shapes you want, and it records the answer:

1. **Standalone.** awow set up for one repo, with its own context and board
   wiring.
2. **Anchored.** One centralized repo — the **anchor** — holds the shared
   `context/`, and other repos register as **anchored repos** and read the
   anchor's context instead of carrying their own. For teams who want a single
   agentic core across several repositories. The details are in
   [Setup & the plugin model](guides/guide-setup-and-two-harnesses.md).

Run it once in every repo that uses awow — but it does different work depending
on the repo. In a standalone repo or an **anchor**, it walks the full setup and
writes that repo's own `context/`. In an **anchored** repo it detects the anchor
from the root `AGENTS.md` and runs a short registration track instead: it
records which anchor the repo belongs to and which board scope it maps to, then
takes the board wiring, conventions and members from the anchor rather than
building a second copy. So an anchored team sets up the anchor first, then runs
`/setup-awow` again — briefly — in each repo that anchors to it.

How you run it is up to you — the format, the pace, and how far you take it:

- Choose a guided walkthrough, or a 25–30 minute team workshop whose
  transcript becomes the same gated setup proposals.
- It is incremental and resumable: stop after any step, pick up where you
  left off.
- Only Steps 0 and 1 (install shape and board) are required; the rest are
  recommended in any order.

The other commands do run without setup — they ask for what's missing and
carry on — but they work better with it.

## Then: explore the commands

The commands work in any repo (anchor or anchored).

| | |
|---|---|
| `/my-work` | what the board says needs you, grouped by blocked, waiting, or yours now |
| `/process-workitem` | a board item from refinement through a planned change to an opened PR |
| `/refinement-prep` | a brief or a deck broken into right-sized stories before the session |
| `/process-transcript` | a meeting recording turned into decisions, owners, and board items |
| `/solution-design-flow` | an architecture argument turned into a decision record |
| `/artifact` | a deck, one-pager, or report as HTML or PDF |

Each command carries a description of the situation it applies to, so you can
describe what you need instead of typing the command name.

Those six are the ones most teams reach for first; `.agents/commands/` holds
twenty-two in all. `/daily-checkin`, `/handover`, `/process-retro`,
`/board-lifecycle`, `/strategy-flow` and `/okr-cascade` are among the rest. The full set, grouped by
the adoption phase each belongs to, is catalogued in
[`.agents/commands/`](.agents/commands/README.md).

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

- **`.agents/` is the source.** `tools/gather.py` builds it into the payloads
  under `dist/` and `dist-telemetry/`. CI fails on drift with `--check`.
- **Nothing is mirrored into this repo's `.claude/` or `.github/`.** The
  marketplace that Claude Code and Copilot install from *is* this repo. A merge
  to `main` is therefore what reaches a maintainer's own sessions, after
  `/plugin marketplace update awow` and then `/plugin update awow`.
- **`/test-awow` is the one exception.** The eval runner lives in this repo's
  `.claude/commands/` rather than in the payload.

To exercise a branch's payload before it merges:

```bash
python tools/gather.py && claude --plugin-dir dist
```

## Status

**v0.13.0 — pre-1.0, in use.** Working end to end: the installs on all five
harnesses, the command set, canonical knowledge-source routing, the session
context, and the build with its drift check in CI.

Being pre-1.0, names and file shapes can still change between releases. The
one migration currently in flight is the `hub` → `anchor` rename: the legacy
spellings (`hub:`, `$AWOW_HUB`, `.awow/hub.json`, `{HUB}`) are still accepted
everywhere, so pre-rename repos need no action.

What each release changed is in [`CHANGELOG.md`](CHANGELOG.md).

## License

MIT. See [`LICENSE`](LICENSE).
