# The agentic retro workflow

How a retrospective transcript becomes named anti-patterns, owned actions, and concrete diffs back into your agent's instructions.

> **TL;DR** — Point `/process-retro` at a retro transcript. It parses, classifies, and probes for
> anti-patterns against a maintained library, every finding carrying a verbatim
> `[hh:mm:ss] @Speaker` quote. It stops twice: Gate 1 to confirm it understood the session, Gate 2
> to approve what gets written. The output that matters isn't the retro notes — it's the
> tightened instructions: concrete diffs to `CLAUDE.md` that the *next* retro checks for.

## The pipeline

The agent works as a **sparring partner, not a secretary** — it shows its reasoning so you can
correct it.

```mermaid
flowchart TD
  t[Retro transcript] --> ctx[Load context + Prime-Directive check]
  ctx --> analyse[Parse, classify & analyse]
  analyse --> g1{{"Gate 1 — confirm understanding"}}
  g1 --> report[Report + instruction diffs]
  report --> g2{{"Gate 2 — approve closures"}}
  g2 --> land["Report saved to retro-reports/&lt;team&gt;/ · approved diffs landed in CLAUDE.md"]
```

## Why it exists

Retros generate good intentions that evaporate — action items lost in a doc, or vague tickets
nobody pulls. Here a recurring problem becomes a concrete diff to the agent's instructions, and the
*following* retro verifies whether it stuck. That is what makes a retro a learning loop instead of
a venting ritual.

## What it reads first

Whatever team context is available — it runs even if none of these files exist.

| Source | What it unlocks |
| --- | --- |
| `context/retros/canon.md` | The main grounding: Prime Directive, the five-phase model, format taxonomy, what "good" looks like. |
| `context/retros/anti-patterns.md` | The maintained library of named issues to check for. |
| `context/team/members.md` | Speaker attribution and the sentiment pass. |
| `context/tooling/board.md` | Verifying whether last retro's promises were actually delivered. |
| `retro-reports/<team>/` | Prior reports — the input for trajectory analysis. |

It also runs a **Prime-Directive check**: scanning the opening minutes for Norm Kerth's blameless
framing — read aloud, paraphrased, or absent — and recording which. If it's absent, nothing is
blocked — the report just records that.

## 1 · Parse, classify & analyse

The agent parses WebVTT, plain text, or SRT, re-attributes shared-microphone speech where it can,
then does the analytical work:

- **Detects the format actually run** — open discussion, silent generation, 1-2-4-All, Lean
  Coffee, TRIZ, futurespective — or flags *conversational dominance*, which is a pathology, not a
  chosen format.
- **Filters noise** with a discard taxonomy (greetings, demo mechanics, drift). If it discards a
  lot, that itself says something about how the session ran.
- **Probes for anti-patterns** — `venting-ritual`, `action-orphan`, `duplicate-creation`,
  `attribution-gap`, `prompt-drift`, `board-zombie` and the rest — split in two: patterns with
  existing research behind them, and new ones specific to working with AI agents.

Where history exists it adds a **sentiment & safety pass** (talk-time share, cut-offs, hedges,
energy) and **trajectory analysis**, classifying each issue as recurring, new, or resolved.

**Gate 1 — confirm understanding.** It presents detected format, participants, anti-patterns
found, recurring issues, sentiment notes, and anything it is unsure about, then waits. Fix an
attribution or add a missed topic here, before it drafts.

## 2 · Report & instruction diffs

Every claim cites `[hh:mm:ss] @Speaker`; where the transcript gives it nothing, it says so
instead of padding the report. Three bands:

| Band | What's in it |
| --- | --- |
| **Core** — every retro | Header & format · sentiment & safety snapshot · what worked / what didn't · detected anti-patterns (general vs agentic-AI) · action list (ranked by severity and scope; every action has an owner). |
| **Trajectory & closure** — when history exists | Cost & velocity · trajectory vs last retro · counter-signal (what was conspicuously absent) · closure tracker against the board. |
| **Loop & audiences** | Instruction-tightening diffs · three role-conditioned summaries · next-retro format recommendation. |

**Gate 2 — approve closures.** It presents the instruction diffs (these change agent behaviour —
review them carefully), the sponsor one-pager, and any `@unassigned` actions. Only what you
approve gets written, and the diffs go into `CLAUDE.md` with a comment saying where they came
from.

## Closing the loop into the instructions

**Actual diffs, not vague suggestions** — concrete lines for `CLAUDE.md`,
`copilot-instructions.md`, or a specific prompt, each with its reason:

```markdown
# Add to CLAUDE.md § board interaction

When creating a board item, first search for an existing one that
covers the scope; link it instead of creating a duplicate.

# Reason: duplicate-creation anti-pattern, 3 instances this retro.
```

Because the diffs go into version control, the next retro's closure tracker can check whether they
prevented their target anti-pattern. Recurring nuisances get promoted to blockers automatically —
"this is the 3rd retro flagging X" is the highest-value line in the whole report — and issues
that stay quiet for two retros are marked resolved.

## Three audiences, one retro

Three deliberately distinct summaries, not the same content reordered, each on its own cadence:

| Summary | Shape | Cadence |
| --- | --- | --- |
| **Team-local checklist** | ~10 lines, tactical, for the team going into next retro | next standup |
| **Governance digest** | ~½ page of patterns, risks, and trajectory, manager-level | monthly |
| **Sponsor one-pager** | ~½ page of value, cost, top risks, and the ask | quarterly |

A **solo mode** also exists: point it at a voice memo and it skips the sentiment pass and collapses
the summaries, but keeps anti-pattern detection on.

## Sources of truth

- [`.agents/commands/process-retro.md`](../.agents/commands/process-retro.md) — the pipeline, the two gates, and the report structure
- [`context/retros/canon.md`](../context/retros/canon.md) — the Prime Directive, phase model, and format taxonomy the analysis grounds on
- [`context/retros/anti-patterns.md`](../context/retros/anti-patterns.md) — the library probed against; extend it as the team names new ones
- [`.agents/commands/process-transcript.md`](../.agents/commands/process-transcript.md) — the general-meeting sibling that routes here
- Companion guides: [transcript router](guide-transcript-router.md) — how a transcript reaches this command; [core delivery loop](guide-core-delivery-loop.md) — how the actions a retro raises get from a board ticket to merged code
