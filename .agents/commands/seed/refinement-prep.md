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

A right-sized story is one an agent or engineer can produce a working PR for in a single session. Sizing checks:

- 1–5 files touched
- 2–3 sentences to describe without hand-waving
- No architectural decisions left for the agent — the story tells *what*, the codebase tells *how*
- 5 or fewer acceptance criteria

If a story fails these, split.

## Output template

```markdown
# <Feature title — verb-first per issue-titles.md>

<One-paragraph plain-language description. Names the user, the change, the value.>

**Parent:** <parent-issue-id-if-any>
**Owner:** <feature owner>
**Cycle:** <target cycle / sprint>

## Stories

<3–7 user stories, each right-sized. Use the template below per story.>

---

### <Story title — verb-first>

**As a:** <Role — be specific. Examples: financial analyst, platform engineer, support lead, data steward>
**I want to:** <One sentence: what change is needed>
**So that:** <Why — what reporting / analysis / capability is enabled>

#### Acceptance criteria (Given / When / Then)

**Scenario 1: <happy path name>**
- Given <precondition>
- When <action>
- Then <observable outcome>

**Scenario 2: <edge case name>**
- Given <precondition>
- When <action>
- Then <observable outcome>

#### Priority
P1 / P2 / P3 — <one line: why this priority>

#### Independent test
<How this story can be verified in isolation>

#### Scope boundary
- In scope: <explicit list>
- Out of scope: <explicit list>

#### Entry point
- File(s): <path/to/file.ext, path/to/other.ext>
- Function / component: <name>
- Related config: <any config files that need updating, reference only>

#### Verification
- Command: `<test or build command>`
- Manual check: <what to look for in the output / UI / API response>

#### Labels
<type:, area: per conventions/REQUIRED/labels.md>

---

## Dependencies

<Stories that block other stories. Cross-team dependencies named (with neighbouring-team links if applicable). One line per dependency.>

## Open questions

<Things the team needs to resolve at refinement, not before. Keep short — questions you cannot answer from the brief plus context belong here, not in story bodies.>

## Risks

<What could go wrong. Brief. Each risk: impact, likelihood, mitigation discussed if any.>

## Attachments (optional)

<Screenshots, sample data, references to upstream documents. Link, do not embed.>
```

## Anti-patterns

| Anti-pattern | Why it's bad | Better |
|---|---|---|
| Multiple unrelated tasks in one story | Confusing, harder to track | Separate stories per logical unit |
| Missing entry point | Requires back-and-forth | Always include named files / components |
| Vague target ("update the dashboard") | Which dashboard? What changes? | Specific, fully-qualified names |
| Empty "So that" | No clear business value | Explain the capability enabled |
| Stories with the word "and" in the title | Two stories in one | Split |
| Acceptance-criteria-as-tasks ("create branch, write code, open PR") | Process, not outcome | AC describes the outcome, not the process |
| Gold-plating (error handling, logging, metrics added to a feature that doesn't exist yet) | Premature scope | First story delivers the feature; observability is a follow-up |

## Quality bar

The feature owner should be able to confidently stand behind this draft in the refinement session. If they would not put their name on it, iterate until they would. **The agent is a co-author, not a ghost-writer.**

## What not to do

- Do not propose stories that require design decisions the team has not made. Surface those as open questions instead.
- Do not write a "kitchen-sink" story ("implement X, add tests, update docs, refactor Y"). Split.
- Do not duplicate content that lives in the knowledge base. Link to it.
- Do not assign owners speculatively. Leave the owner field blank if the team hasn't decided.
