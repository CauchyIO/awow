# context/team/conventions/OPTIONAL/

Conventions that are not required for the agent to start being useful. Each file appears as a stub with `# OPTIONAL — defer` at the top until the team decides to fill it in.

## Why these are deferred

The most common adoption failure is feeling overwhelmed by standards. Asking a team to define infra-naming, data-object naming, and code-style conventions before they have shipped anything is a fast way to lose them.

Each of these files solves a real problem — but the problem usually only becomes visible after the team has run one or two Seed cycles. Defer until you feel the pain.

## Files

| File | When to fill it in |
|---|---|
| `infra-naming.md` | When the team starts creating cloud resources with `/process-workitem` and the names drift |
| `data-objects.md` | When schemas, catalogues, or tables start being created via the agent |
| `code-style.md` | When language-specific style choices fall outside what the linter / formatter enforces |

## `/setup-awow` does NOT ask about these

The wizard physically skips OPTIONAL conventions during setup. They surface in retrospectives once the team has earned the right to ask the question.
