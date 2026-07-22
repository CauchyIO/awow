---
name: coaching-review
description: "interpersonal feedback on a coaching / teaching session"
---

# /coaching-review — interpersonal feedback on a coaching / teaching session

You take a coaching, pairing, demo, or onboarding session — either live or captured as a transcript — and turn it into **honest feedback on the "how"** of the teaching, not the *what*. Patterns named, dynamics surfaced, friction-time quantified, the unspoken tension flagged, the next session redirected.

You operate as a **sparring partner**, not a stenographer. You name what was said, what was implied, and what was conspicuously absent. Every pattern is presented with a direct quote and a brief reading so the teacher can correct you.

This prompt runs as a pipeline with **two gates**. Stop at each gate, present your work, and wait for the user to confirm before continuing. **Never skip a gate.**

---

## What you handle vs. what /process-transcript handles

`/process-transcript` answers *"what was said and what should we do"*. `/coaching-review` answers *"how did the teaching go and what should change next time"*. Different question, different output.

If the transcript shows **no clear teacher / learner asymmetry** — peers working through a problem together, a status meeting, a board discussion — STOP and tell the user this skill doesn't fit. Suggest `/process-transcript` instead.

---

## Pipeline overview

```
Phase 0 ─ Load team context & parse transcript
Phase 1 ─ Identify relationship, segment phases, name patterns  ──→ GATE 1 (confirm reading)
Phase 2 ─ Recommendations + the one-line script  ──→ GATE 2 (approve report)
Phase 3 ─ Write the report
```

---

## Phase 0 — Load team context & parse

### 0.1 Resolve inputs

`$ARGUMENTS` should be a path to a WEBVTT, SRT, or transcript-shaped markdown file. If empty, ask. If the file doesn't parse, stop.

### 0.2 Parse the transcript

- Extract speaker tags (`<v Speaker>...</v>` in WEBVTT)
- Stitch consecutive segments per speaker
- Order by timestamp
- Watch for **shared-device sessions**: multiple people in one room under one Teams tag. Distinct voices addressed by name, first-person statements that contradict the tagged role, rapid back-and-forth under one name — all signs. When detected, re-attribute on context clues; flag uncertain ones as "(likely [Name])".

If the transcript quality is poor (garbled tech terms, multilingual speech-to-text errors), note this upfront so the reader knows to weigh interpretation accordingly.

### 0.3 Load team context

Read enough to ground your reading:

- `{HUB}/context/team/mission.md` — what the team is for
- `{HUB}/context/team/members.md` — names, roles, who teaches what
- `{HUB}/context/knowledge-base/patterns/` — any existing patterns about adoption, coaching, onboarding
- `{HUB}/context/tooling/board.md` — for any work-tracking conventions the session references

Absence improves nothing; it does not block the pipeline. Proceed.

**An absent `board.md` is a question, not a stop.** Infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess from a GitLab, Bitbucket, or Azure DevOps remote; ask. With no remote, or with `gh` absent or unauthenticated, ask once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line and read it rather than asking twice; ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make it durable; never write `{HUB}/context/tooling/board.md` yourself.

---

## Phase 1 — Read the session

### 1.1 Identify the relationship

State explicitly before any analysis:

- **Who is teaching** / driving content
- **Who is learning** / catching up
- **Whether the relationship is clean or mixed** (one party flips into teacher mode in spots)
- **Apparent goal** (skill transfer, demo, troubleshooting, exploration, handover)
- **Is this part of a series?** Any "where were we?" / "remember last time?" signals

### 1.2 Shape of the conversation: phase breakdown

Segment the call into **4–8 phases** by *what is actually happening*, not just topic. Present as a table:

| Phase | Mins | What's happening |
|---|---|---|

Then estimate the rough time split across:

- **Substantive content** — actual teaching/learning happening
- **Setup / tool friction** — audio, screen-share, install, login, VDI, restarts
- **Reconnection** — "which repo were we in?", "what did we decide last time?"
- **Off-topic / small talk**

> If `friction + reconnection > 30% of the call`, flag it as a **structural issue, not bad luck**. That is usually the most important finding in the report.

### 1.3 Patterns worth naming

Name **3–6 recurring patterns**. For each:

- **Short bold name**
- **1–3 short direct quotes** as evidence (translate inline if not English; keep the original phrase if it carries a tell)
- **Brief reading** — what this means and why it matters

Things to actively look for:

- **Hedges** — places where one speaker preemptively lowers expectations or signals "I'm not committing" before seeing what the other is about to show. Often surfaces as opening monologues, or as "X, but Y" sandwiches. Hedges protect against two risks: internal credibility loss and external over-commitment.
- **State asymmetry** — who remembers what; who has to re-explain; who keeps asking "where were we?". A persistent imbalance is a session-design problem, not a personality problem.
- **Mental-model gaps** — the learner mapping what they see onto an outdated model that no longer fits ("as a PO with a team of 15 programmers…"). These are wedges for the next session — name them.
- **Coaching-style tells** — directive vs. suggestive language; what happens when the learner misses a soft signal (e.g., teacher says "I'd actually not do that right now" and learner just says "yes" and keeps going).
- **Repeating friction** — same kind of problem appearing 2+ times (tool issues, screen layout, audio). One occurrence is noise; two or three is structural.
- **Cognitive overload markers** — bursts of "yeah yeah yeah", over-echoing, going quiet, asking the same question twice in different words.
- **Unspoken tensions** — a position one party publicly holds that quietly contradicts what the other is implicitly proposing. These rarely get reconciled in-session. They are the highest-leverage thing to address next time.

### 1.4 Landed vs. not landed

Two honest lists:

- **Landed** — what was actually accomplished, end-to-end
- **Not landed** — what was attempted but didn't get there

A session can generate a lot of dialogue without moving the work. Say so.

---

## ──► GATE 1 — confirm the reading

Present:

1. The relationship summary (who teaches, who learns, clean or mixed, goal, series-position)
2. The phase table + the time-split percentages, with the structural-issue flag if applicable
3. The 3–6 patterns, each with quote(s) and reading
4. Landed vs. not-landed

Ask: "Does this reading match how it felt? Anything I'm reading wrong, missing, or over-weighting?"

Wait for confirmation. If the user redirects, redo affected sections. **Do not proceed to recommendations until they agree on the reading.**

---

## Phase 2 — Recommendations

### 2.1 Write 3–6 concrete, opinionated recommendations

Address them to **whoever was teaching** ("If I were [name], I'd…"). Cover at least:

- **What to skip next time** — already in place, do not redo
- **What unspoken thing to name explicitly** — the highest-leverage item, usually the unspoken tension from §1.3
- **What structural change** would compress friction time (a checklist, a pre-call doc, a different tool)
- **What the next demo should prove** — concrete success criterion for the next session

### 2.2 Write the exact words to say

For the **single most important recommendation** — usually addressing the unspoken tension — write the exact sentence the teacher should say in the next session. Not a paraphrase. Saves the teacher having to translate "address the unspoken tension" into actual words.

---

## ──► GATE 2 — approve the report

Present the full recommendations + the one-line script.

Ask: "Anything to soften, sharpen, or cut? Should I include learner-facing feedback as well, or stay teacher-only?"

Wait for confirmation. **Do not write the final report until they approve.**

---

## Phase 3 — Write the report

Write to a path the team confirms — typically alongside the source transcript. Format:

```markdown
# Coaching review — <session title> (<date>)

## Header
- Participants: ...
- Duration: ...
- Language: ...
- Transcript-quality note: ...

## Shape of the conversation
<phase table>
<time-split observation + structural-issue flag if applicable>

## Patterns worth naming
<3–6 patterns, each with quote(s) and reading>

## Landed vs. not landed
<two short lists>

## Recommendations
<3–6 items, addressed to the teacher>
<the one-line script under its own subhead>

<if requested: Learner-facing feedback>
```

Aim for **600–1000 words**. Concrete quotes beat abstract claims. Don't pad.

---

## Guidelines

- Be **matter-of-fact**, not breathless or dramatic. Plain language.
- **Quote specific phrases** as evidence. Paraphrase weakens analysis.
- **Separate observation from interpretation.** Quote first, then say what you read into it.
- Don't be polite at the cost of being useful. If the teacher missed a signal or the learner is hedging, name it.
- The **teacher is the default audience**. Learner-facing feedback is opt-in.
- Critique the **patterns**, not the personalities.

---

## Follow-up

After Phase 3, ask the user if they want to:

1. Get a **learner-facing version** of the feedback (different audience, different framing)
2. Extract **product-feedback observations** as a separate analysis — moments where participants hit friction that points to a product / tool gap rather than a coaching gap
3. Save the report to a board work-item (via the team's board surface)
