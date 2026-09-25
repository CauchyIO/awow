# Story shape

The shape `workitem-write` and `/refinement-prep` apply when drafting a story. The guiding
rule: **as short as it can be, longer only where the work demands it.** Fields earn their
place; a field that adds no signal is left out.

> **Make it yours.** This file is a seed, not a contract. Edit it — or replace it — so it
> reflects how your team actually writes stories. Stricter requirements (a fixed archetype
> catalogue, a mandatory source-to-target mapping, required verification commands) are
> encoded here. The agent reads whatever is in this file.

A story exists to let a competent teammate — human or agent — pick up the work without
asking. The minimum that achieves that is the right size. "As a / I want / So that" is *one*
way to structure intent, not a requirement; plain prose is fine when it is clearer.

## What every story has

1. **A title that names the outcome.** Verb-first, no "and", no domain jargon a reviewer
   won't recognise.
2. **A body that answers: what changes, and why it matters.** One or two sentences if that
   suffices. Use role / action / value framing only if it genuinely sharpens the why.
3. **Tags.** Per `{ANCHOR}/context/team/conventions/REQUIRED/labels.md` — at minimum `type:`
   and `area:`. Tags determine routing, reviewers, and which rules apply; a story without
   them is unroutable.

Bodies that are already sufficient:

> Add tax rates to the invoice line export so finance can reconcile multi-currency revenue in the reporting pack.

> Login redirect intermittently fails on Safari mobile after SSO — affects ~5% of mobile sign-ins. Fix the redirect so the failure rate drops to zero.

> Migrate cron jobs to the managed scheduler. Current host is being decommissioned end of quarter.

That is often the whole story. Add more only when the work needs it.

## What a story adds when needed

Only when they carry their weight — a bullet list of three items beats an empty section header.

- **Specification** — concrete details a reader would otherwise dig for: source/target names,
  contract diffs, the specific file or component, a sketch of the approach. Link durable
  rationale to the knowledge base rather than embedding it.
- **Acceptance criteria** — testable conditions for "done". Given/When/Then where it sharpens
  a criterion; a checkbox list of observable outcomes otherwise. Aim for ≤5; more usually
  means the story is too large.
- **Scope boundary** — explicit out-of-scope items, when the story is at risk of growing.
  Skip when the scope is obvious from the title.
- **Verification** — a command, screen, or response to inspect, when "did this work" is
  non-obvious. Skip when the acceptance criteria already make it clear.

If a section would be empty or repeat the body, leave it out.

## Anti-patterns

| Problem | Why it's bad | Better |
|---|---|---|
| Multiple unrelated tasks in one story | Confusing, hard to track, hard to revert | One story per logical unit |
| Vague target ("update the dashboard") | Reviewer has to guess what changed | Name the specific artefact |
| No "why" anywhere | Reviewers can't make trade-off calls mid-work | One sentence on the motivation |
| Title contains "and" | Two stories in one | Split |
| Missing or invented tags | Story can't be routed; bypasses team conventions | Tag per `{ANCHOR}/context/team/conventions/REQUIRED/labels.md`; search existing labels before creating new ones |
| Acceptance criteria describe the process, not the outcome | AC should be observable from outside | Rewrite to outcomes |
| Story includes error handling, logging, metrics for a feature that doesn't exist yet | Gold-plating | First story delivers the feature; observability is a follow-up |
| Story body embeds long rationale, meeting recap, or design discussion | Bloats the board, rots quickly | Link to the knowledge base instead |
| Empty section headers ("## Acceptance criteria" with nothing under it) | Pure noise | Delete the section |

## Why the shape holds

A story in this shape lets the agent understand intent from title + body, plan against the
specification and acceptance criteria, refuse drive-by changes using the scope boundary, and
check its own work before handing back. Each dropped element removes one of those.

Three habits keep it honest: start with one sentence and add only what a reviewer would still
have to ask for; describe the outcome, not the activity; and when this file keeps fighting you
on individual stories, edit the file rather than working around it forever.
