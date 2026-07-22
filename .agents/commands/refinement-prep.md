---
description: "Use when the user has a feature brief, quarterly slidedeck, or board issue and wants it broken into right-sized stories before a refinement session, or asks to prep work for the next refinement."
autofire: true
phase: seed
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "{HUB}/context/team/mission.md exists"
removes_pain: "the scramble-the-day-before-refinement problem"
---

# /refinement-prep — draft a feature for the next refinement

You prepare a feature for an upcoming refinement session. The output is a draft the team reviews *before* the session, so the live meeting becomes design discussion rather than discovery.

One person can do this alone. The value shows up immediately in their own work, and the output is visible to the whole team at the next refinement. This is typically the first prompt a team adopts.

## What refinement decides — the *how*, never the *what*

Refinement works out **how** to deliver work that has already been chosen. It does not decide *what* to build or *why* — that is set upstream in quarter planning, where the program board and PO define the outcomes (OKRs), the PO breaks each outcome into epics, and the PO with the tech lead breaks an epic into the **features** that enter refinement. A feature arrives already mapped to an outcome; refinement turns it into board-ready, right-sized stories and never re-opens the decision to build it. If a feature's *what* or *why* is still open, that is a planning gap — surface it; do not resolve it by drafting stories. The planning chain lives in `{HUB}/context/quarterly/`; how outcome → epic → feature → story map onto board primitives lives in the board hierarchy reference under `{HUB}/context/tooling/boards/`, falling back to `{AWOW_ROOT}/context/tooling/boards/`.

Populating the board is not one ceremony. Which route you take depends on team size, the kind of work, and cadence:

- **Feature-level refinement** — a feature becomes 3–7 stories, reviewed in a session. This command's default, and what the template below produces.
- **User-story refinement** — a smaller team skips the feature wrapper and refines stories directly. Run this command from a thin brief and emit the stories without a heavyweight feature layer.
- **Continuous / BAU / operations** — no session. A PO or analyst spins up individual stories as operational work arrives. The same right-sizing and duplicate rules apply; there is simply no feature to wrap.
- **Solution design** — when the feature carries a real design decision, refine it through `/solution-design-flow` instead: it locks the design and decomposes it into a work-item tree with stated edges.

This command covers the first three. Reach for `/solution-design-flow` when the open questions are architectural, not just scoping.

## Inputs

The user provides one of:

- A short brief (one paragraph, in chat or as a file in `input/`)
- A slidedeck or document in `input/quarterly/` to extract from
- A board issue URL to expand into stories
- A meeting transcript output from `/process-transcript`

## Steps

### 1. Load context

Read:

- `{HUB}/context/team/mission.md` — the feature must serve the mission. If you cannot see how, ask the user before drafting.
- `{HUB}/context/team/conventions/REQUIRED/issue-titles.md` — story title verbs and patterns
- `{HUB}/context/team/conventions/REQUIRED/labels.md` — label taxonomy
- `{HUB}/context/team/conventions/REQUIRED/output-discipline.md` — story body rules (short!)
- `{HUB}/context/team/style/board-output.md` — voice and shape
- `{HUB}/context/knowledge-base/glossary.md` — domain terms; use these consistently
- `{HUB}/context/knowledge-base/patterns/` — link to existing patterns rather than restating
- `{HUB}/context/tooling/board.md` — sizing rules per board family

**An absent `board.md` is a question, not a stop.** Infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess from a GitLab, Bitbucket, or Azure DevOps remote; ask. With no remote, or with `gh` absent or unauthenticated, ask once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line and read it rather than asking twice; ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make it durable; never write `{HUB}/context/tooling/board.md` yourself.

### 2. Check for duplicates and overlap (REQUIRED before drafting)

Search the board for existing work using keywords extracted from the brief. Identify:

- Stories that duplicate or overlap with what you are about to draft
- A parent feature / epic the new work should attach to
- Related work that should inform scope

If duplicates exist, report them to the user with IDs and titles. Ask whether to:

- Proceed with new stories anyway
- Link to / extend existing issues instead
- Cancel and let the user reconcile

Do not draft if potential duplicates exist without confirmation.

### 3. Draft

Output to `{PROJECT}/proposals/refinement/<feature-slug>.md` with the structure below.

Right-size every story so a single session can ship a working PR. Each story must:

- touch 1–5 files,
- be describable in 2–3 sentences without hand-waving,
- leave no architectural decisions to the agent — the story tells *what*, the codebase tells *how*,
- carry 5 or fewer acceptance criteria.

Split anything that fails these.

## Output template

The feature wrapper:

```markdown
# <Feature title — verb-first per issue-titles.md>

<One-paragraph plain-language description. Names the user, the change, the value.>

**Parent:** <parent-issue-id-if-any>
**Owner:** <feature owner>
**Cycle:** <target cycle / sprint>

## Stories

<3–7 user stories. Use the shape defined by the `user-story-template` skill.>

## Dependencies

<State as edges, one per line: `Story A → Story B` (A blocks B). Name cross-team dependencies with neighbouring-team links. Note the likely critical path if one is visible. These edges feed forward — /project-plan formalises them into the dependency graph — so capture them as relations, not prose.>

## Open questions

<Things the team needs to resolve at refinement, not before. Keep short — questions you cannot answer from the brief plus context belong here, not in story bodies.>

## Risks

<What could go wrong. Brief. Each risk: impact, likelihood, mitigation discussed if any.>

## Attachments (optional)

<Screenshots, sample data, references to upstream documents. Link, do not embed.>
```

For the per-story shape inside `## Stories`, follow the `user-story-template` skill. The template defines what every story carries, what to add only when needed, and the anti-patterns to avoid. Do not duplicate the per-story structure here.

## Anti-patterns

See the anti-patterns table in the `user-story-template` skill. The same rules apply to every story produced by this command.

## Quality bar

Iterate until the feature owner would put their name on the draft in the refinement session. If they would not, the draft is not done. **Co-author the feature; never ghost-write it.**

## What not to do

- Do not propose stories that require design decisions the team has not made. Surface those as open questions instead.
- Do not write a "kitchen-sink" story ("implement X, add tests, update docs, refactor Y"). Split.
- Do not duplicate content that lives in the knowledge base. Link to it.
- Do not assign owners speculatively. Leave the owner field blank if the team hasn't decided.
