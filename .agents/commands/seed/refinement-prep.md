---
phase: seed
prerequisites:
  - "Step 0 of /setup-awow complete (board MCP wired)"
  - "context/team/mission.md exists"
removes_pain: "the scramble-the-day-before-refinement problem"
---

# /refinement-prep — draft a feature for the next refinement

You prepare a feature for an upcoming refinement session. The output is a draft the team reviews *before* the session, so the live meeting becomes design discussion rather than discovery.

One person can do this alone. The value shows up immediately in their own work, and the output is visible to the whole team at the next refinement. This is typically the first prompt a team adopts.

## Inputs

The user provides one of:

- A short brief (one paragraph, in chat or as a file in `input/`)
- A slidedeck or document in `input/quarterly/` to extract from
- A board issue URL to expand into stories
- A meeting transcript output from `/process-transcript`

## Steps

### 1. Load context

Read:

- `context/team/mission.md` — the feature must serve the mission. If you cannot see how, ask the user before drafting.
- `context/team/conventions/REQUIRED/issue-titles.md` — story title verbs and patterns
- `context/team/conventions/REQUIRED/labels.md` — label taxonomy
- `context/team/conventions/REQUIRED/output-discipline.md` — story body rules (short!)
- `context/team/style/board-output.md` — voice and shape
- `context/knowledge-base/glossary.md` — domain terms; use these consistently
- `context/knowledge-base/patterns/` — link to existing patterns rather than restating
- `context/tooling/board.md` — sizing rules per board family

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

Output to `proposals/refinement/<feature-slug>.md` with the structure below.

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

<3–7 user stories. Use the shape defined in [`.agents/skills/user-story-template.md`](../../skills/user-story-template.md).>

## Dependencies

<Stories that block other stories. Cross-team dependencies named (with neighbouring-team links if applicable). One line per dependency.>

## Open questions

<Things the team needs to resolve at refinement, not before. Keep short — questions you cannot answer from the brief plus context belong here, not in story bodies.>

## Risks

<What could go wrong. Brief. Each risk: impact, likelihood, mitigation discussed if any.>

## Attachments (optional)

<Screenshots, sample data, references to upstream documents. Link, do not embed.>
```

For the per-story shape inside `## Stories`, follow [`.agents/skills/user-story-template.md`](../../skills/user-story-template.md). The template defines what every story carries, what to add only when needed, and the anti-patterns to avoid. Do not duplicate the per-story structure here.

## Anti-patterns

See the anti-patterns table in [`.agents/skills/user-story-template.md`](../../skills/user-story-template.md#anti-patterns). The same rules apply to every story produced by this command.

## Quality bar

Iterate until the feature owner would put their name on the draft in the refinement session. If they would not, the draft is not done. **Co-author the feature; never ghost-write it.**

## What not to do

- Do not propose stories that require design decisions the team has not made. Surface those as open questions instead.
- Do not write a "kitchen-sink" story ("implement X, add tests, update docs, refactor Y"). Split.
- Do not duplicate content that lives in the knowledge base. Link to it.
- Do not assign owners speculatively. Leave the owner field blank if the team hasn't decided.
