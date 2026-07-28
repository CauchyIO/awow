# User story template

A skill the agent reads when drafting stories for refinement or via `/process-workitem`. Defines the shape of a well-structured user story that works for both human reviewers and agent execution.

This is the **seed template** shipped with awow v0.1 — deliberately generic. The guiding rule: **as short as it can be, longer only where the work demands it.** Fields are used when they add signal; skipped when they don't.

> **Make it yours.** This file is a seed, not a contract. Edit it directly — or replace it entirely — so it reflects how your team actually writes stories. If your team has stricter requirements (a fixed archetype catalogue, a mandatory source-to-target mapping table, a required labels taxonomy, specific verification commands), encode them here. The agent reads whatever is in this file.

---

## Core principle

A story exists to let a competent teammate (human or agent) pick up the work without asking. The minimum that achieves that is the right size. The "As a / I want / So that" Mad Libs is *one way* to structure intent — it is not the only way, and it is not required. Plain prose is fine when it is clearer.

---

## What every story has

Three things, always:

1. **A title that names the outcome.** Verb-first, no "and", no domain jargon a reviewer won't recognise.
2. **A body that answers: what changes, and why it matters.** One or two sentences if that suffices. Use role / action / value framing if it genuinely sharpens the why — otherwise skip it.
3. **Tags.** Per [`{HUB}/context/team/conventions/REQUIRED/labels.md`](../../context/team/conventions/REQUIRED/labels.md). At minimum the story declares its `type:` and `area:`; add `status:` only when it carries information the workflow state does not. Tags determine routing, reviewers, and which rules apply — a story without them is unroutable.

Examples of sufficient bodies:

> Add tax rates to the invoice line export so finance can reconcile multi-currency revenue in the reporting pack.

> Login redirect intermittently fails on Safari mobile after SSO — affects ~5% of mobile sign-ins. Fix the redirect so the failure rate drops to zero.

> Migrate cron jobs to the managed scheduler. Current host is being decommissioned end of quarter.

That is often the whole story. Add more only when the work needs it.

---

## What a story adds when needed

Use these only when they carry their weight. A bullet list of three items beats an empty section header.

- **Specification** — concrete details a reader would otherwise have to dig for: source/target names, contract diffs, the specific file or component, a sketch of the approach. Link to the knowledge base for durable rationale rather than embedding it.
- **Acceptance criteria** — testable conditions for "done." Use Given/When/Then when it sharpens a criterion; a checkbox list of observable outcomes is fine otherwise. Aim for ≤5; more usually means the story is too large.
- **Scope boundary** — explicit out-of-scope items, when the story is at risk of growing. Skip if the scope is obvious from the title.
- **Verification** — a command, screen, or response to inspect, when "did this work" is non-obvious. Skip when the acceptance criteria already make it clear.

If a section would be empty or repeat the body, leave it out.

---

## Anti-patterns

| Problem | Why it's bad | Better |
|---|---|---|
| Multiple unrelated tasks in one story | Confusing, hard to track, hard to revert | One story per logical unit |
| Vague target ("update the dashboard") | Reviewer has to guess what changed | Name the specific artefact |
| No "why" anywhere | Reviewers can't make trade-off calls mid-work | One sentence on the motivation |
| Title contains "and" | Two stories in one | Split |
| Missing or invented tags | Story can't be routed; bypasses team conventions | Tag per [`labels.md`](../../context/team/conventions/REQUIRED/labels.md); search existing labels before creating new ones |
| Acceptance criteria describe the process, not the outcome | AC should be observable from outside | Rewrite to outcomes |
| Story includes error handling, logging, metrics for a feature that doesn't exist yet | Gold-plating | First story delivers the feature; observability is a follow-up |
| Story body embeds long rationale, meeting recap, or design discussion | Bloats the board, rots quickly | Link to the knowledge base instead |
| Empty section headers ("## Acceptance criteria" with nothing under it) | Pure noise | Delete the section |

---

## How this fits the agentic workflow

When a story follows this shape, the agent can:

1. **Understand intent** — from title + body, decide whether the request is well-formed.
2. **Plan implementation** — use the specification + acceptance criteria (when present) to draft a plan (per `/process-workitem`).
3. **Stay in scope** — use the scope boundary, or the implied scope from a tight title, to refuse drive-by changes.
4. **Validate completion** — use acceptance criteria + verification to check work before handing back.

---

## Tips for the team

1. **Start with one sentence.** Add more only when a reviewer would still have to ask.
2. **Outcome over activity.** Reviewers care that the thing works, not that someone touched a file.
3. **Fix the template, not the story.** If this file keeps fighting you on individual stories, edit the file — that's cheaper than ad-hoc workarounds repeated forever.
