# Placement decision tree

See `context/team/conventions/REQUIRED/output-discipline.md` Rule 2 for the canonical table. This file is the human-readable companion.

## Quick reference

```
Is this content...

  about THIS story's intent or acceptance criteria?
    → Story body

  about THIS story's current state, a blocker, or a decision made during execution?
    → Story comment

  durable — true beyond this story, useful to future readers (architecture, pattern, runbook, glossary entry)?
    → context/knowledge-base/<subfolder>/

  a decision being discussed but not yet resolved?
    → Comment now. Promote to context/knowledge-base/decisions/ once resolved.
```

## The discipline

Before writing anything to the board, classify. The agent labels every section by destination *before* anything lands. The user approves placement, not just words.

## awow-specific

- The `input/PROPOSAL.md` and `input/research/` directories at the awow repo root are *one-time* design substrate, not part of the running knowledge base. They are referenced from the knowledge base but not duplicated into it.
- `context/knowledge-base/decisions/` is where Architectural Decision Records (ADRs) about awow itself live (e.g. *"gh CLI vs. MCP for GitHub Projects"*, *"single CLAUDE.md vs. per-harness"*). These are durable rationale, not status.
