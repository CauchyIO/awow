# awow

awow gives a coding agent your team's context: the board it reads, the
conventions it follows, and commands for the work that happens between people.
The full technical guide lives [here](guides/README.md).

**Install options**

awow can be used in two configurations:

1. **Standalone install**. Install awow for one specific repo with its own
   context and board wiring.
2. **Anchored**. Run awow from an **anchor**: one centralized repo holding
   the shared `context/` — board wiring, mission, conventions, members. Other
   repos register as **anchored repos** and use the anchor's context instead of carrying
   their own. Useful for teams that want to use a shared agentic core
   throughout multiple repositories.

`/setup-awow` asks which shape you want and records it — details in
[Setup & the plugin model](guides/guide-setup-and-two-harnesses.md).

---

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

---

## Installing the plugin

Claude Code:

    /plugin marketplace add CauchyIO/awow
    /plugin install awow@awow

Codex:

    codex plugin marketplace add https://github.com/CauchyIO/awow-dist
    codex plugin add awow@awow

Pi:

    pi install git:github.com/CauchyIO/awow-dist

GitHub Copilot (requires the Copilot CLI):

    copilot plugin marketplace add CauchyIO/awow
    copilot plugin install awow@awow

opencode:

    opencode plugin awow@git+https://github.com/CauchyIO/awow-dist.git

Claude Code and Copilot install from this repo, which carries the marketplace
manifest both read. Codex, Pi and opencode install from `awow-dist`, which
carries the built payload. Copilot exposes the commands as skills rather than
slash commands.

---

## First: run `/setup-awow`

`/setup-awow` is the first command to run after installing the plugin. It
wires your board (Linear, Jira, Azure DevOps, GitHub Issues) and writes your
mission, conventions, and members into `context/` — the context every other
command reads. Run it for both **anchor** and **anchored** repos.

- Detects whether you are using an anchor or an anchored repo. Anchored repos need only
  minimal setup.
- Choose a guided walkthrough, or a 25–30 minute team workshop whose
  transcript becomes the same gated setup proposals.
- It is incremental and resumable: stop after any step, pick up where you
  left off.
- Only Steps 0 and 1 (install shape and board) are required; the rest are
  recommended in any order.

The other commands do run without setup — they ask for what's missing and
carry on — but they work better with it.

---

## Then: the commands

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

---

## What the agent picks up

Every session starts by reading awow's working rules: go to the board before
starting work, write or update the ticket, and keep the admin current while you
work. Commands read your team context where it exists. An optional OKF catalog
routes them to canonical repositories, SharePoint, or vector-backed sources
without copying that material into the anchor.

---

## Going deeper

The guides live in [`guides/`](guides/README.md) — plain markdown, readable
directly on GitHub or as agent context.

`awow-telemetry` is a second plugin for measuring how the way of working is
going: session timelines, prompt-quality review, usage coaching. It runs on
Claude Code only.

---

## Developing awow

`.agents/` is the source; `tools/gather.py` builds it into the payloads under
`dist/` and `dist-telemetry/`, and CI fails on drift with `--check`. Nothing is
mirrored into this repo's `.claude/` or `.github/`: the marketplace Claude Code
and Copilot install from *is* this repo, so a merge to `main` is what reaches a
maintainer's own sessions (`/plugin marketplace update awow`, then
`/plugin update awow`). To exercise a branch's payload before it merges:

    python tools/gather.py && claude --plugin-dir dist

`/test-awow`, the eval runner, is the one command that lives in this repo's
`.claude/commands/` rather than the payload.

---

## Status

The installs, the command set, canonical knowledge-source routing, the session
context, and the build with its drift check in CI are working; what each
release changed is in [`CHANGELOG.md`](CHANGELOG.md). awow installs as a
plugin: the prompts stay in the payload and an adopter repo holds only its own
`context/`. `awow-telemetry` runs on Claude Code only.

---

## License

MIT. See [`LICENSE`](LICENSE).
