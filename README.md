# awow

awow gives a coding agent your team's context: the board it reads, the
conventions it follows, and commands for the work that happens between people.

## Install

Claude Code:

    /plugin marketplace add CauchyIO/awow
    /plugin install awow@awow

Codex:

    codex plugin marketplace add https://github.com/CauchyIO/awow-dist
    codex plugin add awow@awow

Pi:

    pi install git:github.com/CauchyIO/awow-dist

GitHub Copilot:

    copilot plugin marketplace add CauchyIO/awow
    copilot plugin install awow

Claude Code installs from this repo. Codex and Pi install from `awow-dist`,
which carries the built payload. Copilot exposes the commands as skills rather
than slash commands.

## Then what

The commands work in any repo without further setup.

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

## What the agent picks up

Every session starts by reading awow's working rules: go to the board before
starting work, write or update the ticket, and keep the admin current while you
work. Commands read your team context where it exists, and ask you once where it
does not rather than stopping.

## Going deeper

`/setup-awow` wires your board (Linear, Jira, Azure DevOps, GitHub Issues) and
writes your mission, conventions, and members into `context/`. It is incremental
and resumable. Commands work better with it, and none require it.

`awow-telemetry` is a second plugin for measuring how the way of working is
going: session timelines, prompt-quality review, usage coaching. It runs on
Claude Code only.

## Prerequisites

A board with hierarchy. The agent reaches it however your team already does:
`gh`, an MCP server, or your own skills and scripts, as long as the instructions
say how. `/setup-awow` records that in `context/tooling/board.md`. Without it the
board commands ask you once and carry on.

## Status

v0.6. The four installs, the command set, the session context, and the build
with its drift check in CI are working. `/awowify`, which vendors the prompts
into your repo as editable files, runs from a clone rather than as a plugin
command. `awow-telemetry` runs on Claude Code only.

The visual tour is [`guides/index.html`](guides/index.html). Self-contained HTML,
no agent session needed.

## License

MIT. See [`LICENSE`](LICENSE).
