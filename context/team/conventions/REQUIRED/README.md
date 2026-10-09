# context/team/conventions/REQUIRED/

The four conventions every team needs to make the agent useful. These are non-negotiable.

| File | Purpose |
|---|---|
| `issue-titles.md` | Verb-first title patterns. Example: `Implement {thing}`, `Fix {symptom} in {area}`, `Update {thing}`. Vague titles fail. |
| `labels.md` | Prefixed label taxonomy: `type:`, `area:`, `status:`. Priority lives in the board's native priority field, not in labels. |
| `branches.md` | Branch naming rule. Usually generated from the issue identifier. |
| `output-discipline.md` | Brevity rule + placement decision tree (story body / comment / knowledge base). Read at every session start. |

## Populated by

`/setup-awow`. Where the board shows existing patterns it drafts from what it observes, with real examples; on a new board it proposes the reference defaults. Every draft is a proposal.

## The "REQUIRED" name is load-bearing

The agent treats these as hard constraints. The team is free to disagree with the proposed defaults — but the file must exist with *some* content that the agent can apply consistently.

`output-discipline.md` is the strictest of the four. Without it, every agent-driven board over-produces, and the noise problem this repo is meant to prevent shows up on day one.
