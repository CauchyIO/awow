# Board comments

Comments are transient. They describe what is happening *now* on a story; once the story closes, comment content is no longer canonical.

## When to comment

- Status update: "blocked on X", "in review with Y", "deployed to staging".
- Decision made during execution that does not change scope: "chose library A over B because <reason>".
- Intermediate finding worth surfacing: "this also fixes ticket Z".

## When NOT to comment

- Durable rationale → write to `context/knowledge-base/decisions/<x>.md` and link from the story.
- Scope change → edit the story body, do not bury in comments.
- General discussion → use a chat tool; comments are for board-visible state.

## Comment length

One paragraph. Two at most. A long comment is almost always a knowledge-base entry mis-routed.

## awow-specific

- For `awow-test`-labelled issues, comments may be skipped entirely — the issue is ephemeral by design. A comment on an `awow-test` issue is only worth writing if it surfaces a finding that should later be promoted to a real (non-`awow-test`) issue or a knowledge-base entry.
