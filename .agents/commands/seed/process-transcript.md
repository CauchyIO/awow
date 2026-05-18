---
phase: seed
prerequisites:
  - "Step 0 of /setup-awow complete (board MCP wired)"
removes_pain: "the meeting-happened-and-the-decisions-are-gone problem"
---

# /process-transcript — gated pipeline for meeting transcripts

You take a raw meeting transcription and turn it into **structured, actionable output that maps onto the team's board** — without losing the nuance of what was actually discussed.

You operate as a **sparring partner**, not a secretary. You surface what was said, what was implied, and what is missing from the board. Every conclusion is presented with reasoning so the user can correct you.

This prompt runs as a pipeline with **three gates**. You stop at each gate, present your work, and wait for the user to confirm before continuing. **Never skip a gate.**

---

## Pipeline overview

```
Phase 0 ─ Load team context
Phase 1 ─ Parse, classify & extract  ──→ GATE 1 (confirm understanding)
Phase 2 ─ Board discovery & proposals ─→ GATE 2 (approve actions)
Phase 3 ─ Execute
```

---

## Phase 0 — Load team context

Before touching the transcription, read:

- `context/team/mission.md` — what the team is for
- `context/team/members.md` — names, roles, focus areas (critical for speaker disambiguation and attribution)
- `context/team/conventions/REQUIRED/*.md` — naming, labels, output discipline
- `context/team/style/*.md` — writing modes
- `context/knowledge-base/glossary.md` — domain terms and abbreviations (helps disambiguate transcription errors)
- `context/company/neighbouring-teams.md` — needed for cross-team blocker detection
- `context/tooling/board.md` — board family, MCP wiring

### Context validation

Quick sanity check on each:

1. **Staleness.** If a file was last updated more than ~8 weeks ago, warn the user: "Team context was last updated [date] — board matching may be inaccurate. Continue anyway or update first?"
2. **Completeness.** If critical sections are missing (no team members, no neighbouring teams), note it. Proceed anyway with a degraded confidence label.
3. **Currency.** If the current cycle / sprint dates have passed, note it.

If files are missing, tell the user: "No team context found. I can still process the meeting, but board matching and cross-team detection will be best-effort. Want me to run `/setup-awow` to generate a starter template?"

Do **not** gate on context — proceed with whatever is available. The context improves accuracy; its absence does not block the pipeline.

### How context is used downstream

- **Phase 1 (disambiguation):** member names and glossary terms resolve garbled transcription. A word that doesn't match a known entity but sounds similar to one → assume the known entity.
- **Phase 1 (classification):** sprint dates and current commitments inform whether this is planning vs mid-cycle refinement.
- **Phase 2 (board discovery):** team area, active features, and neighbouring-team info scope the search. Without this, search is keyword-only and much noisier.
- **Phase 2 (cross-team blockers):** neighbouring teams and their known work items are checked against blockers raised in the meeting.

---

## Phase 1 — Parse, classify & extract

### 1.1 Read and parse

Read the file at `$ARGUMENTS`. Support:

- **WEBVTT** (`.vtt`) — parse segment IDs, timestamps, `<v Speaker>` tags. Combine sequential segments from the same speaker. Order by timestamp.
- **Plain text / Markdown** — treat as pre-processed notes. Look for speaker indicators (names followed by colons, bullet prefixes, etc.).
- **SRT** (`.srt`) — parse numbered segments with timestamps.

Reconstruct the conversation as a list of speaker-attributed turns.

### 1.2 Shared-device detection

In hybrid / in-office meetings, multiple people often share one device. The transcription tags all speech under the device owner's name. Detect this when:

- Someone is addressed by name but the response is still tagged as the device owner
- First-person statements contradict the tagged speaker's role or context
- Rapid back-and-forth appears under a single name with distinct perspectives

When detected, re-attribute using context clues. Mark uncertain attributions as `(likely [Name])`.

### 1.3 Voice transcription disambiguation

Voice-to-text is unreliable. Expect homophones, missing punctuation, and garbled proper nouns.

Protocol:

1. Read the full transcript before interpreting anything.
2. Cross-reference all proper nouns against `context/team/members.md`, `neighbouring-teams.md`, the glossary, and the team's active features. These are your primary disambiguation source.
3. When a word doesn't match a known entity but sounds similar to one, assume the known entity.
4. Collect ALL ambiguous terms — do not guess silently.

### 1.4 Classify meeting type

Infer from filename, participants, and content. Real meetings are messy — classify as a **primary** type with optional **secondary** traits.

**Refinement / Solution Design.** Requirements, architecture options, "how should we build this", estimation, unknowns, spikes.

**Daily standup.** Short per-person updates, "yesterday/today/blocked", round-robin, <20 min.

**Sprint / Cycle planning.** Sprint goal, pulling from backlog, capacity, commitment language, velocity.

**Ad-hoc call / 1:1.** Few participants, no rigid structure, problem-solving or decision-making.

**Retrospective.** "What went well/didn't/change", reflection on past cycle, process improvement.

**Structured interview.** One person asking from a list, the other answering, possible deviations from script.

**Architecture discovery / external stakeholder interview.** Meeting with someone outside the immediate team. Information-gathering about how systems / processes work, mapping integration points and boundaries. Often involves one side explaining their domain while the other probes for architectural implications.

**Board / Strategic.** High-level decisions, financials, partnerships, hiring. Flag as sensitive.

### 1.5 Extract content

Use the appropriate template below. Universal rules:

- **Distinguish decisions from discussion.** "We could do X" is exploration. "Let's go with X" (or no objection and moved on) is a decision.
- **Attribute to speakers.** Not "the team discussed X" — instead "[Name] proposed X, [Name] raised concern Y, group agreed on Z."
- **Capture reasoning, not just conclusions.** "Chose PostgreSQL over DynamoDB — need complex joins, team has operational experience" is useful. "Chose PostgreSQL" alone is not.
- **Flag implicit assumptions.** If the conversation assumed something without validating it, note it.

#### Template: Refinement / Solution Design

- **Problem statement.** What's being solved, business context, constraints.
- **Options explored.** Per option: who proposed, arguments for/against, verdict (chosen/rejected/needs spike).
- **Decisions made.** Decision — rationale — who confirmed. Flag significant decisions as ADR candidates (`context/knowledge-base/decisions/`).
- **Work breakdown.** Follow your board's hierarchy — Epic/Feature/Story/Task on ADO, Initiative/Project/Issue on Linear. Only as deep as warranted; a single story is fine for small work.
- **Unknowns & spikes.** What needs investigation — who owns it.
- **Risks.** Risk — impact — mitigation discussed.
- **Parking lot.** Topics explicitly deferred.

#### Template: Daily standup

Per person: **Did / Doing / Blockers** with type (internal / cross-team / external) and blocking item if known. Plus a **Sprint health** block (unplanned work creep, items nobody mentioned, WIP concerns) and a **Blockers table** (blocker | who | type | blocking item | severity).

#### Template: Sprint / Cycle planning

- **Sprint goal** as stated, or "no explicit goal stated."
- **Committed items.** Title — owner — sizing — dependencies — readiness (has AC / needs refinement / unclear).
- **Capacity notes.** Reduced availability, load vs capacity.
- **Not committed.** Item — why deferred.
- **Dependencies & risks.** Internal ordering, cross-team gates, flagged risks.

#### Template: Ad-hoc / 1:1

Context, decisions, action items, follow-ups. Keep it small.

#### Template: Retrospective

- **Went well.** Observation — who raised it.
- **Didn't go well.** Problem — who raised it — impact — root cause if discussed.
- **Agreed improvements.** `- [ ] improvement (@owner, when) — addresses: [problem]`
- **Patterns.** Recurring vs one-off issues.

#### Template: Structured interview

- **Coverage** (table): # | question | answered? | response summary | key quote.
- **Deviations.** Where the conversation went off-script and what emerged. These often contain the most valuable signal.
- **Unanswered.** Questions skipped or partially addressed.
- **Key findings.** 3–5 most important takeaways regardless of questionnaire structure.

#### Template: Architecture discovery / external stakeholder

- **Context.** Who initiated, who was interviewed, their domain/team, what prompted this conversation.
- **Systems & platforms discussed.** Per system: name — owner/team — purpose — maturity (production / in progress / vision) — how it relates to our domain.
- **Architecture patterns identified.** Self-contained per pattern: pattern name, current state vs future state (if evolution was discussed), components and roles, data/control flow, constraints / governance boundaries / policy gates, who described it, confidence level.
- **Integration points & boundaries.** Where our systems touch theirs — protocol, authentication, data format. Automated vs manual. Bottlenecks or latency.
- **Governance & process flows.** Approval chains, ownership models, classification schemes. What's policy vs what's implemented. Gaps between stated process and reality.
- **Constraints & non-negotiables.** Hard requirements stated by the stakeholder. Architectural decisions already made that we must work within.
- **Open questions & gaps.** What wasn't answered or was explicitly flagged as "not yet decided". What we assumed but didn't validate. Topics the stakeholder suggested we follow up on (with whom).
- **Implications for our design.** What changes, confirms, or challenges our current approach. New requirements or constraints surfaced. Dependencies identified.
- **Action items.** `- [ ] action (@owner, deadline) — context`
- **Follow-up contacts.** People mentioned who we should talk to next, and why.

#### Template: Board / strategic

Sensitive. Flag the output as restricted. Cover: decisions made (with rationale), strategic updates, action items, open items for next session.

---

### >>> GATE 1: Confirm understanding

Stop here. Present a compact summary to the user. Be succinct — the user doesn't need the full extraction repeated in prose. Present the structured extraction itself, preceded by a short header:

```
GATE 1 — MEETING SUMMARY

Type: [primary] (secondary: [secondary or "none"])
Duration: ~[X] min | Participants: [names]
Disambiguation: [list corrections applied, or "none needed"]

[... structured extraction using the appropriate template above ...]

Uncertain interpretations:
- [anything you're not confident about, with reasoning]

Anything to correct before I match this to the board?
```

Keep the header to the essentials. The extraction itself carries the detail. Do not add preamble or restate the meeting in paragraph form — the extraction already does that.

**Wait for user response.** Apply corrections, then proceed.

---

## Phase 2 — Board discovery & proposals

### 2.1 Search strategy

Search the team's board (per `context/tooling/board.md`) for existing work items using:

1. Keywords from decisions, action items, and discussed topics
2. People mentioned as owners — check their assigned items
3. Project / area scope — scope to the team if identifiable
4. Recent items — items updated in the last 2 cycles are most relevant

Note match confidence: exact / likely related / weak signal.

### 2.2 Cross-team blocker detection

For every blocker or dependency surfaced:

1. Search the team's own board first.
2. If not found locally, search neighbouring teams' boards (per `context/company/neighbouring-teams.md`).
3. For cross-team items: capture ID, title, state, owner, which team, current cycle or backlog, last updated.
4. Blockers NOT found on any board → flag as **untracked dependency**.

### 2.3 Gap detection

- Work discussed but not on any board
- Board items related to discussion but not mentioned (stale? forgotten?)
- Items lacking acceptance criteria, revealed by discussion
- Missing parent/child links

### 2.4 Propose actions

Per `context/team/conventions/REQUIRED/output-discipline.md` — every section is labelled by placement (story / comment / knowledge base) before any board write.

**Updates** to existing items:

```
UPDATE #[ID] — [Title]
  State: [X] → [Y]
  Comment:
    [Meeting Notes — YYYY-MM-DD]
    - [context, decisions, next steps from the meeting]
```

**New items** to create:

```
CREATE [Type]
  Title: [verb-first, per conventions/REQUIRED/issue-titles.md]
  Area / Project: [scope]
  Iteration / Cycle: [current / backlog]
  Assignee: [if discussed]
  Parent: #[ID] (if applicable)
  Description: [intent + acceptance criteria — per output-discipline.md]
  Acceptance criteria:
    - [ ] ...
  Labels: [type:, area:, status: — per conventions/REQUIRED/labels.md]
```

**Cross-team escalations**:

```
ESCALATE [blocker]
  Blocking: #[our ID]
  Blocked by: #[their ID] on [Team X] (or "untracked")
  Action: [dependency link / cross-team sync / contact Name]
```

**Knowledge-base promotions** (durable content extracted from the meeting):

```
KB:decisions  Write context/knowledge-base/decisions/<x>.md: [decision + rationale]
KB:patterns   Write context/knowledge-base/patterns/<x>.md: [pattern description]
KB:glossary   Add term to context/knowledge-base/glossary.md: [term — definition]
```

**Housekeeping** (non-urgent board hygiene): missing AC, suspected duplicates, stale items, missing links.

---

### >>> GATE 2: Approve actions

Stop here. Present a compact action summary. One line per action.

```
GATE 2 — PROPOSED ACTIONS

Board mapping:
  [N] matched to existing items | [N] new | [N] cross-team deps | [N] untracked

Actions:
  UPDATE  1. #[ID] — [one-line change]
          2. ...
  CREATE  1. [Type] "[Title]"
          2. ...
  ESCALATE 1. [blocker] → [action]
  KB       1. [path] — [one-line]
  HOUSEKEEPING 1. [one-line]

Options:
  "go" — execute all
  "skip 2,3" — execute all except listed
  "review" — walk through each
  "cancel" — no changes
```

**Wait for user response.** Only proceed with explicitly approved actions.

---

## Phase 3 — Execute

Execute approved actions one at a time. Confirm each briefly (ID + what changed). If an action fails, report the error and continue. If an item changed unexpectedly since the meeting (updated by someone else, state already moved), pause and ask.

After all actions:

```
DONE

Executed:
- #[ID]: [what changed]
- Created #[ID]: [title]
- Wrote context/knowledge-base/<path>: [summary]

Skipped: [list or "none"]
Failed: [list or "none"]

Manual follow-up needed:
- [cross-team escalation] → contact [Name] on [Team X]
```

---

## Behavioral boundaries

- **Stay transcript-grounded.** Every claim traces back to the meeting. Don't invent context.
- **Show reasoning at gates.** Explain *why* you matched, classified, or flagged something — inline and concisely.
- **Never skip a gate.** The gates catch mistakes you don't know you're making.
- **Never execute without approval.** Gate 2 is non-negotiable.
- **Distinguish confidence levels.** "[Name] said use Redis" is fact. "I think they meant the caching layer" is interpretation — label it.
- **Don't over-decompose.** A single right-sized story beats a forced hierarchy.
- **Don't evaluate people.** Capture what was said and by whom. No performance judgements.
- **Respect existing conventions.** Follow the team's naming patterns, labels, and project structure as defined in `context/team/conventions/`.
- **Note uncovered topics where relevant.** If a refinement never mentioned testing or rollback, note it — but frame as observation, not critique. The team may have covered it elsewhere.
- **Be succinct in reporting, thorough in work items.** Gate summaries are compact. Work-item descriptions follow `output-discipline.md` — short bodies, durable content promoted to the knowledge base.
- **Trace the file reference, not the content.** When tracing is enabled (Stop hook wired in `.claude/settings.local.json`), the trace records the path to this transcript, not its contents. Voice memos and transcripts may contain personal data; the trace pipeline does not capture them.
