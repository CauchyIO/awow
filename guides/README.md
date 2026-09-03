# Guides

How to go from zero to a working setup, then every guide, in reading order. Plain markdown
throughout: readable here on GitHub, in Obsidian, or by an agent as session context.

## What awow is

The case for awow — the scattered-context problem it solves, what it gives an agent, and
how it is built and versioned — is in the [repo README](../README.md). These guides assume
it and pick up from there.

## From zero to working

1. **Install the plugin.** The per-product install commands are in the
   [repo README](../README.md).
2. **Run `/setup-awow`.** A handful of questions and one review: it wires your board
   (Linear, Jira, Azure DevOps, GitHub Issues), drafts a team profile from what it can
   observe in your board and repo, and writes both into `context/`. Works solo or for a
   team, standalone or attached to a shared team repo (an *anchor*).
3. **Work the loop.** `/my-work` for what needs you, `/refinement-prep` before the session,
   `/process-workitem` from ticket to PR, `/daily-checkin` to cap the day.
4. **Grow when it earns its place.** Digests, design systems, transcript processing,
   telemetry — each guide below says what it assumes and what pain it removes.

## Reading order

Three guides carry the core; read them in this order:

1. [Setup & the plugin model](guide-setup-and-two-harnesses.md) — the wizard, and how one
   source tree serves every agent product without drifting copies.
2. [The core delivery loop](guide-core-delivery-loop.md) — the day-to-day: board to PR,
   with a human approval before anything irreversible.
3. [Board & MCP integration](guide-board-and-mcp.md) — how the agent actually reaches your
   board, and what gets recorded about it.

Everything else is on-demand — come back when the topic comes up. The tables below say what
each guide covers.

## Individual — center of gravity: the session

| Guide | What it covers |
|---|---|
| [Prompt taxonomy](guide-prompt-taxonomy.md) | An eight-intent vocabulary for naming what you're doing before you ask; the lens the usage coach reads sessions back through. |
| [Session timeline](guide-session-timeline.md) | A zero-setup visual picture of how a repo got built across sessions, straight from the Claude Code logs on disk. |
| [Trace analysis](guide-trace-analysis.md) | One skill pulls traces down to local JSON; two read them back as prompt-quality and usage-coaching reports. |

## Team — center of gravity: the board

| Guide | What it covers |
|---|---|
| [The core delivery loop](guide-core-delivery-loop.md) | `/refinement-prep` drafts a right-sized story, `/process-workitem` walks one from board to PR, `/daily-checkin` caps the day — all on the same check-the-board-first, propose-then-approve pattern. |
| [Setup & the plugin model](guide-setup-and-two-harnesses.md) | The resumable `/setup-awow` wizard — only Steps 0 and 1 required — and how one `.agents/` source becomes the plugin package every agent product installs. |
| [Board & MCP integration](guide-board-and-mcp.md) | How a board URL becomes the one file the agent reads, and how an approved MCP gets wired into both harnesses. |
| [Canonical knowledge sources](guide-canonical-knowledge-sources.md) | Routing from the anchor's context to authoritative repositories, SharePoint, and vector-backed sources without copying their contents. |
| [Updating awow](guide-update-and-versioning.md) | Plugin updates replace the plugin's files wholesale; `/migrate-to-plugin` cleans up an older copied-in install once, edits preserved, parity proven. |
| [Transcript router](guide-transcript-router.md) | One entry point reads the transcript, recommends a specialist, and pauses for approval before anything reaches the board. |
| [Solution design collaboration](guide-solution-design-collaboration.md) | The three things a recorded decision needs — a place, a lifecycle, and a feedback channel that doesn't drift into chat. |
| [Agentic retro workflow](guide-agentic-retro-workflow.md) | Turning retros into named anti-patterns, owned actions, and concrete diffs to your agent instructions. |
| [Standardise reporting](guide-standardise-reporting.md) | `/daily-digest` at two zoom levels, a day or a week: what happened, where it heads, what connects. |
| [Design systems & HTML artifacts](guide-design-system-and-artifacts.md) | Stand a house style up once, then render every deck and one-pager from it. Opt-in. |
| [Session correlation](guide-session-correlation.md) | Linking agent-authored board entries back to their session trace via a footer id. Opt-in; requires tracing to already be wired. |

## Pillar · cross-team — center of gravity: the activity RACI

| Guide | What it covers |
|---|---|
| [Cross-team & pillar](guide-cross-team-and-pillar.md) | Why a pillar is a different kind of node, not a bigger team: three mechanisms across the team↔pillar boundary, built on one activity×team RACI. (Draft.) |
| [Program portfolio view](program-portfolio-view.md) | Allocation under constraint — priority routes down to the team boards, size and progress roll back up. (Illustrative.) |

## Writing a guide

Every guide is one markdown file, humans and agents both:

1. `# Title` and a one-sentence subtitle.
2. A `> **TL;DR**` blockquote — the whole guide in 3–6 lines.
3. Plain `##` sections; GFM tables for decisions; Mermaid fences only where a
   diagram encodes real structure.
4. Each fact in one place — if a table carries it, the prose doesn't restate it.
5. A closing `## Sources of truth` section: each entry a repo path plus a short
   descriptor of what it governs. Nothing follows it.
6. Its last entry is a `Companion guides:` line — each related guide, lowercase
   link text, `— what it governs` after each.

Terseness is the idea. Relative links between guides; no external links; no
HTML, styling, or badges.
