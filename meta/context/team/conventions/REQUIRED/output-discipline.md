# Output discipline

Non-negotiable. Read at session start.

The board exists to be skim-readable. The knowledge base exists to be findable. Stories that absorb durable content destroy both surfaces at once.

## Rule 1 — Minimum useful body

A story body is the smallest set of sentences that lets a competent teammate pick up the work.

Default skeleton:

```
<One-sentence intent.>

## Acceptance criteria
- [ ] <observable outcome 1>
- [ ] <observable outcome 2>

## Reference
- Pattern: context/knowledge-base/patterns/<x>.md (if applicable)
- Decision: context/knowledge-base/decisions/<x>.md (if applicable)
```

No "Context" section. No "Considerations". No meeting recap. If the agent finds itself writing a third paragraph, it stops and asks whether the extra material belongs in the knowledge base instead.

## Rule 2 — Placement decision tree

Before writing anything to the board, classify the content:

| Kind of content | Goes in | Lifetime |
|---|---|---|
| Intent + acceptance criteria for *this* unit of work | Story body | Until story closes |
| Status update, blocker, decision made during execution | Story comment | Until story closes |
| "How we do X", architectural rationale, domain term, runbook | `context/knowledge-base/` | Durable; outlives every story that links to it |
| Discussion that resolves into a durable decision | Comment first, *then* promoted to `knowledge-base/decisions/` once resolved | Comment is transient; the ADR is durable |

The agent applies this tree explicitly. When `/process-workitem` produces a draft, every section it would write is labelled by kind. The user approves placement, not just words. A story is not allowed to absorb content that belongs in the knowledge base.

## Rule 3 — Update vs. edit

- **Story body edits** are reserved for scope or acceptance-criteria changes.
- **Status, progress, blockers, intermediate findings** go in comments.

The agent does not rewrite the body to "reflect the latest thinking." That is how drift gets locked in. If the body becomes wrong, the fix is to narrow the scope, not expand the body.

## Rule 4 — Session footer

Every board entry you author — issue create, issue comment, PR create, PR comment — ends with a session footer linking it to the session that produced it:

    _session: <session-id>_

Read the id from `$CLAUDE_SESSION_ID` (populated by the session-correlation SessionStart hook) or your harness's equivalent. The id matches the trace's `mlflow.trace.session` tag, so `awow-usage-coach`, `daily-digest`, and `weekly-digest` can join board content to session traces.

**Exempt:** trivial metadata-only changes (label, state, project-add) and one-line status comments. The footer is required when the entry records a decision or finding, or runs two or more sentences.

## awow-specific notes

- Pull request descriptions on `CauchyIO/awow` follow the same skeleton. The PR body is *not* a place to recap the implementation; the diff is the implementation.
- Commit messages on this repo run two sentences maximum (per the user's global commit guideline). The "why" goes in the issue / PR; the commit captures what changed.
- The `awow-test` label is the *only* thing that distinguishes a real awow backlog issue from a walkthrough byproduct. Without it, durability is ambiguous — issues with `awow-test` are ephemeral; issues without it are real work.

## How this is enforced

- This file is part of the REQUIRED conventions set; `/setup-awow` produces it.
- The team's generated `CLAUDE.md` includes a "Board output rules" block lifted from here. Read every session.
- `refinement-prep`, `process-workitem`, and `process-transcript` produce drafts that explicitly tag content by placement before any board write happens.

## What this is not

- **Not a word count.** Brevity is a function of fit. A genuinely complex story can be longer than a trivial one. The rule is "no padding," not "no detail."
- **Not a wiki replacement project.** The knowledge base ships as `context/knowledge-base/`. Teams that already have Confluence or Notion can mirror or point the agent at the external system via `context/tooling/`.
- **Not retroactive cleanup.** Existing story sprawl is not the agent's job to fix on day one. The discipline applies forward.
