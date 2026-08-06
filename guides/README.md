# Guides

How awow works, guide by guide. Plain markdown — readable here on GitHub, in
Obsidian, or by an agent as session context.

New here? Start with
[Setup & the pointer-stub model](guide-setup-and-two-harnesses.md).

## Individual — center of gravity: the session

| Guide | What it covers |
|---|---|
| [Prompt taxonomy](guide-prompt-taxonomy.md) | An eight-intent vocabulary for naming what you're doing before you ask; the lens the usage coach reads sessions back through. |
| [Session timeline](guide-session-timeline.md) | A zero-setup visual picture of how a repo got built across sessions, straight from the Claude Code logs on disk. |
| [Trace analysis](guide-trace-analysis.md) | One skill pulls traces down to local JSON; two read them back as prompt-quality and usage-coaching reports. |

## Team — center of gravity: the board

| Guide | What it covers |
|---|---|
| [The core delivery loop](guide-core-delivery-loop.md) | `/refinement-prep` drafts a right-sized story, `/process-workitem` walks one from board to PR, `/daily-checkin` caps the day — all on the look-first, propose-then-approve spine. |
| [Setup & the pointer-stub model](guide-setup-and-two-harnesses.md) | The resumable `/setup-awow` wizard — only Steps 0 and 1 required — and authoring once under `.agents/` for both harnesses. |
| [Board & MCP integration](guide-board-and-mcp.md) | How a board URL becomes the one file the agent reads, and how an approved MCP gets wired into both harnesses. |
| [Canonical knowledge sources](guide-canonical-knowledge-sources.md) | Routing from HUB context to authoritative repositories, SharePoint, and vector-backed sources without copying their contents. |
| [Updating awow](guide-update-and-versioning.md) | Pulling newer awow against the lockfile: starter-owned paths move, your edits survive, conflicts land as sidecars. |
| [Transcript router](guide-transcript-router.md) | One entry point reads the transcript, recommends a specialist, and gates before anything reaches the board. |
| [Solution design collaboration](guide-solution-design-collaboration.md) | The three things a recorded decision needs — a place, a lifecycle, and a feedback channel that doesn't drift into chat. |
| [Agentic retro workflow](guide-agentic-retro-workflow.md) | Turning retros into named anti-patterns, owned actions, and concrete diffs to your agent instructions. |
| [Coordinating delivery](guide-delivery-coordination.md) | The delivery graph re-grouped into coordination buckets — proposed, never acted on without approval. (Parked.) |
| [Standardise reporting](guide-standardise-reporting.md) | `/daily-digest` at two altitudes, a day or a week: what happened, where it heads, what connects. |
| [Design systems & HTML artifacts](guide-design-system-and-artifacts.md) | Stand a house style up once, then render every deck and one-pager from it. Opt-in. |
| [Session correlation](guide-session-correlation.md) | Linking agent-authored board entries back to their session trace via a footer id. Opt-in, and gated on tracing already being wired. |

## Pillar · cross-team — center of gravity: the activity RACI

| Guide | What it covers |
|---|---|
| [Cross-team & pillar](guide-cross-team-and-pillar.md) | Why a pillar is a different archetype, not a bigger team: three mechanisms across the seam, spined on one activity×team RACI. (Draft.) |
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
