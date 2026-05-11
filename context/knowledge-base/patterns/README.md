# context/knowledge-base/patterns/

"How we do X." Recurring solutions the team has converged on. One file per pattern.

A pattern names the problem it solves, the trade-offs accepted, and shows the canonical shape. Patterns are referenced from stories (story body says "follows `patterns/<x>.md`") rather than restated.

## Template

```markdown
# <Pattern name>

## Problem
<What problem this solves.>

## Approach
<Canonical shape. Example code, configuration, or diagram.>

## When to use this
<Conditions.>

## When NOT to use this
<Conditions where this approach is wrong.>

## Trade-offs
<What this approach gives up.>
```

## Promotion ritual

Patterns often start life as a comment on a story or a paragraph in a transcript. When the same pattern is referenced more than twice, promote it: extract into a file here, leave a one-line link in the original location.
