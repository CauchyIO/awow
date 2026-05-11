# context/knowledge-base/decisions/

Lightweight architectural decision records. One file per decision.

## Template

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

Heavier ADR formats (MADR, etc.) are an OPTIONAL convention. The form above is the REQUIRED minimum — small enough that nobody can object to writing one.

## When to write a decision record

- A team-level technical choice with non-trivial consequences (database, framework, hosting model)
- A non-obvious constraint that future readers will need to know
- A choice made under explicit trade-off that future readers might second-guess

## When NOT to write one

- "We use TypeScript" without trade-off discussion — that's tribal knowledge, put it in `patterns/` or skip
- Single-story decisions — those belong in story comments, not as ADRs
- Decisions made for one engagement that don't outlast the engagement
