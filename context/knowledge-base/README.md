# Knowledge base

Durable reference. The answer to "stories aren't a wiki."

## What lives here

- **`architecture/`** — system shape: decisions, diagrams, integration patterns. One file per concern.
- **`patterns/`** — "how we do X" — recurring solutions. Each pattern names the problem it solves and the trade-offs.
- **`runbooks/`** — on-call, incident response, common ops. Step-by-step, testable.
- **`glossary.md`** — domain terms. Referenced from stories, not redefined per ticket.
- **`decisions/`** — lightweight ADRs. One file per decision: context, decision, consequences.

## What does NOT live here

- Story-specific status, blockers, or intermediate findings → story comments.
- Story scope or acceptance criteria → story body.
- Meeting recaps → none of those go anywhere; `/process-transcript` extracts what's durable.
- Code → that lives in the codebase. Knowledge base references code paths but does not embed.

## The link discipline

The board links into the knowledge base; the knowledge base does **not** link back to specific stories. This keeps the durable layer from being polluted with transient links. A pattern might say "this approach was chosen in Q3 2026 to replace the X workflow"; it does not say "see story `<TEAM>-123`".

## Lightweight ADRs

`decisions/` uses one-file-per-decision with a short header:

```markdown
# <Decision title>

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Superseded by <link>

## Context
<What problem we faced, what constraints applied.>

## Decision
<What we decided. Active voice. One paragraph.>

## Consequences
<What this means for the team. Trade-offs accepted.>
```

Heavier ADR formats (e.g. MADR) are an OPTIONAL convention. The form above is the REQUIRED minimum.

## Promotion ritual

When a story comment turns out to contain durable content:

1. Extract it into the right `knowledge-base/<subfolder>/<x>.md`.
2. Leave a one-line link in the original comment: `Promoted to context/knowledge-base/<subfolder>/<x>.md`.
3. The original comment becomes a pointer; the content is now durable and findable.

`/process-workitem` and `/process-transcript` perform this routing explicitly.

### The capture → synthesize spine

For durable knowledge surfaced by mining a day's activity, promotion runs through a
committed staging layer rather than inline:

1. **Capture** — the mining lens (`mining.md`, tuned by `mining-policy.md`) stages each
   candidate as one committed file in `context/kb-inbox/`.
2. **Synthesize** — the drain (`synthesis.md`) reads the inbox and, **on explicit
   approval**, applies the disposition (novel → write, matches → annotate, covered →
   no-op, thin → drop), leaves the board pointer, logs provenance, and clears the file.

Both paths land content here the same way and obey the link discipline below.

## Staleness

`tools/validate-context.py` flags knowledge-base files that have not been linked from any story in the last 90 days. These are archival candidates. Soft signal — review at retrospectives, do not auto-delete.
