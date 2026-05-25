---
phase: standardise
argument-hint: "[path to a written or voice account, e.g. checkins/<user>/YYYY-MM-DD.md] (optional — omit to capture live or to reconstruct from board + code)"
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "Optional: an account of the day in any form — written note, voice memo, or none. The command also runs from board + code activity alone."
removes_pain: "the I-did-the-work-but-the-board-doesn't-show-it problem"
---

# /daily-checkin — capture your day, map it to the board, execute approved updates

You capture an individual's working day — from whatever account they give you, in whatever form — map it onto the team's board, cross-reference it against code activity, identify structural gaps, and execute board updates **only after explicit confirmation**.

The check-in is **optional and elastic**. Its depth scales with what the user provides: a detailed account yields a rich summary; a couple of lines yields a lighter one; nothing at all still works, because the board and code activity carry most of the signal. Never treat any single input as mandatory, and never pressure the user into providing one.

You are not evaluating performance. You are not doing strategic forecasting. You are enforcing structural clarity: making sure the work that happened is reflected on the board, scoped sensibly, and not silently missing a ticket.

**Bias hard against noise — this is the point of the command, not a footnote.** A daily check-in run every day is a noise machine if you let it be: duplicate tickets, verbose recaps, a new issue for every passing thought. Your default is the opposite. Advance work that is *already* tracked — comment on or move an existing issue. Treat creating a new issue as the exception that must justify itself, never the reflex. Keep every proposed board write to the minimum useful text.

**The team has already written down how it works with its board — defer to it, don't reinvent it.** `context/tooling/board.md` is the mechanics: write surface, states, and the board's limitations. `.agents/CLAUDE.md` carries the look-first, never-duplicate rule; `context/team/style/board-output.md` carries placement and minimum-useful discipline. Read those before proposing anything, and when in doubt, propose less.

**Writes to the board — but only after a gate.** Everything up to Section 5 is read-only synthesis. No issue is created, moved, or commented on until the user explicitly approves in Section 5.

---

## Pipeline overview

```
Section 0 ─ Input sources & ingestion
Section 1 ─ Conversation phase
Section 2 ─ Post-processing (internal logic)
Section 3 ─ Output (the daily summary)
Section 4 ─ Clarification round
Section 5 ─ Board execution           ──→ GATE (explicit approval)
Section 6 ─ Behavioral boundaries
```

---

## Section 0 — Input sources & ingestion

A check-in draws on up to three input sources. **None is mandatory.** Some days you'll have all three, some days only the board and code. Collect whatever is present, synthesize from that, and don't demand a particular format.

### A. The user's own account (any form — and entirely optional)

This is the user's own description of their day, in whatever shape they choose to provide it:

- **A written note** — the argument points to a markdown file (e.g. `checkins/<user>/YYYY-MM-DD.md`), or the user types a few lines directly into the conversation. This is just as valid as a voice memo — often more reliable.
- **A voice memo** — a voice-to-text transcription file. One convenient option among several, not the expected default.
- **Nothing at all** — the user already logged their work on the board and would rather not narrate it again. That's a perfectly good check-in. Lean on sources B and C, reconstruct what happened, and confirm it with them.

If an account is provided, read all of it before interpreting anything. The richer the account, the richer the summary — but a sparse account is not a failure to correct, just less to work with.

**Voice-specific handling.** *Only* when the account is a voice-to-text transcription, treat it as unreliable. Written accounts are taken at face value — apply the protocol below to voice input only:

- **Homophones & phonetic substitutions** — words that sound alike get swapped ("genic" → "agentic"; a name → a common word).
- **Missing punctuation and run-on sentences** — the memo may be one continuous stream.
- **Dropped or merged words** — small words vanish; compound names get split or joined.
- **Garbled proper nouns** — people, project, product, and technical names are frequently wrong.

**Disambiguation protocol (voice input only):**

1. Read the full transcript before interpreting anything.
2. Cross-reference every proper noun against known entities: projects and people from `context/team/members.md`, product and domain names from `context/team/`, and code repositories.
3. When a word matches no known entity but sounds like one, assume the known entity.
4. Collect all ambiguous terms and present them for confirmation **before** producing the summary. Do not guess silently. Group the questions efficiently ("I read X as Y and A as B — correct?").

### B. Code activity (automatic)

Before synthesizing, inspect today's code activity via the team's code-hosting surface:

1. Pull commits, PRs, and review events from today across the team's repositories.
2. Cross-reference against the account — code activity confirms and enriches work the user mentioned, and can surface work they didn't. When no account was given, this is your primary signal.
3. Identify any code activity **not** mentioned in the account as a separate section for the user to confirm.

### C. Meeting transcripts (when provided)

If meeting transcripts are referenced, **do not parse them inline here.** Route them through `/process-transcript`, which handles transcripts under an explicit gate (they may contain personal data). Pull only the structured output — decisions, action items, commitments — back into this check-in, and flag any action item assigned to the user that has no board ticket.

**Input priority when sources conflict:** processed transcript (highest factual accuracy) > code activity (verifiable) > the user's account (richest context; lowest accuracy if it's a voice transcription).

---

## Section 1 — Conversation phase (optional)

If an account was already provided as the argument, read it and skip straight ahead — to the disambiguation round (Section 0.A step 4) for voice input, or to Section 2 for a written note.

If no account was provided, **offer** a short conversation — don't impose one. Some people like talking through their day; others would rather you reconstruct it from the board and code activity. Ask which they prefer, and respect "just pull it from the board" as a complete answer — proceed to Section 2 and build the summary from sources B and C.

If they do want to talk, open with:

> How was your day? (optional — skip if you'd rather)
> What did you work on, and who did you work with?
> Walk me through what you delivered.

Rules for live narration:

- Allow free narration. Do **not** interrupt mid-flow.
- Do **not** enforce structure during narration.
- Capture everything. Move to structuring only after the user finishes.

---

## Section 2 — Post-processing (internal logic)

Once you have the inputs — the account (if any), code activity, and any processed transcript — work through the following internally before drafting the summary:

### A. Extract context first

Identify each project or area worked on and who collaborated. Most work is internal — don't impose a client or external framing where none exists. If external parties (clients, partners, other teams) genuinely came up, note them; otherwise leave that out.

### B. Identify concrete deliverables

Translate abstract descriptions into tangible outputs, decisions made, changes created, artifacts produced, and conversations that changed direction. Focus on outcomes, not activities.

### C. Board discovery

Search the board for project / area names, keywords, related topics, and recently updated issues, then map today's work onto existing issues. Apply the team's board doctrine here — don't re-derive it: the look-first, never-duplicate rule in `.agents/CLAUDE.md`, the placement and minimum-useful rules in `context/team/style/board-output.md`, and the query/write mechanics and limitations in `context/tooling/board.md`. **Never require the user to provide issue IDs.**

### D. Code cross-reference

Map today's code activity to board issues (linked branches, issue IDs in commit messages or PR descriptions). Identify: work mentioned with corresponding code activity (confirms), code activity not mentioned (forgotten work), and repositories with no corresponding board project (structural gap). Include code links in proposed board comments where relevant.

### E. Structural gaps

Note only genuine gaps — work a teammate would expect on the board but can't find, a real dependency or follow-up that would otherwise be lost. What counts as board-worthy is the team's call (set in `.agents/CLAUDE.md` and `context/team/style/board-output.md`); apply it, don't redefine it. "No gaps today" is a fine and common outcome.

### F. Knowledge discovery (implicit)

Without being asked, identify reusable insights, documentation gaps, and recurring confusion, and suggest a capture location — for durable rationale that's `context/knowledge-base/` (per the placement rules in `.agents/CLAUDE.md`). No speculation beyond what the sources support.

---

## Section 3 — Output (the daily summary)

**Keep it short.** A daily artefact should be readable at a glance. Four sections, each of which may be a single line — or omitted entirely when there's nothing to say. Descriptive only: no performance judgement, no forecasting. Resist padding; an exhaustive summary is a failure mode, not thoroughness.

```markdown
# Daily check-in — YYYY-MM-DD

## Summary
2–4 sentences: what was worked on, with whom (only if it matters), which tracked
work advanced, and anything notably unstructured. A short paragraph, not a list.

## What moved
One line per concrete thing that happened, tied to its board issue where there
is one. Fold the issue touched, the outcome, and the related commit/PR into the
*same* line — do not split them into separate sections.
* <AWOW-123> <Issue title> — what changed today (PR #, decision, result)
* (untracked) <what happened> — see Proposed updates below

## Proposed board updates — NOT YET EXECUTED
The only section that drives writes. Keep each entry to minimum-useful text.
* Update <AWOW-123>: comment (shape below) [+ move → <state>]
* Move <AWOW-124> → <state>
* **New issue** (only if it cleared the bar in Section 2.C): <title> — one line of why
Prefer the first two. If this list proposes more new issues than updates, you are
almost certainly generating noise — go back to Section 2.C and re-map.

## Gaps & follow-ups  *(only genuine ones — omit the section if none)*
* Work with no ticket that truly needs one (not every passing task).
* A repo with no corresponding board project.
* An insight worth capturing durably → suggest `context/knowledge-base/`.
* Tomorrow's single top priority or a real blocker, if there is one.
```

Proposed board comments follow the team's board-output rules (`context/team/style/board-output.md`). Use this shape:

```
[Daily check-in — YYYY-MM-DD]

Progress:
- …

Next:
- …

Blockers:
- …
```

---

## Section 4 — Clarification round

After presenting everything, ask up to five questions. Default toward fewer — only ask what genuinely changes the proposed updates:

1. Is the issue mapping correct?
2. Should any issue move to Done?
3. Did I miss any deliverable?
4. Is anything sensitive that should not be recorded?
5. (Only if you proposed a new issue) Does this really need its own ticket, or does it belong as a comment on an existing one?

---

## Section 5 — Board execution (explicit approval required)

After clarification, ask:

> Should I execute these updates on the board?

Rules:

- **Never write to the board without explicit confirmation.**
- If the user confirms:
  - Re-verify each issue match before touching it.
  - Execute updates exactly as approved — add comments in the standardized format, move states only if confirmed, create new issues only if approved.
  - Confirm each action taken.
- If ambiguity surfaces mid-execution, stop and ask before proceeding. No silent changes.

---

## Section 6 — Behavioral boundaries

- **Smallest board footprint wins.** Prefer commenting on or advancing an existing issue over creating a new one; prefer minimum-useful text over a recap. Do not create issues, write long comments, or surface gaps to appear thorough. Noise is the failure mode this command must actively prevent — see `context/tooling/board.md` and `context/team/style/board-output.md`.
- **Stay source-grounded.** Synthesize only from the user's account (if any), code activity, and processed transcript. Never fabricate activity or attribute work incorrectly — and never invent a richer day than the sources support to compensate for a sparse or missing account.
- **No silent guessing** on garbled proper nouns — disambiguate at the gate in Section 0.A (voice input only).
- **No performance evaluation, no strategic forecasting.** Surface structure and gaps; let the human decide.
- **Respect private-team boundaries.** If the team has a private board surface (per `context/team/conventions/REQUIRED/labels.md`), a check-in for a private-team member may write there, but never leak private-team work into a shared surface.
- **Read-only until Section 5.** The board is not touched until the user approves.
- **Route transcripts through `/process-transcript`** — do not ingest raw meeting transcripts inline.
