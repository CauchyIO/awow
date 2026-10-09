---
description: "Use when a team wants to talk its way of working through and needs a meeting brief, or has the workshop transcript back to turn into team context proposals."
phase: spread
layer: team
argument-hint: "[prepare | <transcript.vtt|.srt|notes.md>]"
prerequisites:
  - "A board connected (`/setup-awow`), so live board observations can be compared with what the team said"
removes_pain: "the we-talked-about-how-we-work-and-nothing-was-captured problem"
channel: workflows
consumes: transcript
when-to-use: "The transcript is a team setup or ways-of-working workshop covering mission, work flow, recurring rituals, working agreements, ownership, or awow configuration."
when-not-to-use: "The transcript is an ordinary refinement, standup, planning session, retrospective, interview, or design discussion rather than a deliberate setup conversation."
---

# /team-workshop — prepare the conversation, then turn it into team context

You help a team capture how it works by talking it through in its own time, rather than answering a questionnaire. Two halves: **prepare** a short meeting brief, and **process** the transcript or notes that come back into proposals for the team's context. Every context write goes through one gate. `/setup-awow` never does this; it configures the repo and stops.

Enter **Process** directly when the argument is a `.vtt`, `.srt`, or transcript-shaped Markdown file, or when `/process-transcript` hands you a parsed setup-workshop segment. Enter **Prepare** on `prepare` or with no argument.

## Prepare the workshop

Do not require any context to exist first. Read what is safely available — `{ANCHOR}/context/tooling/board.md`, `{ANCHOR}/context/team/`, the repo's README — then draft `{PROJECT}/proposals/workshop/meeting-brief.md` with this timebox:

| Time | Conversation |
|---|---|
| 0–4 min | What the team exists to change, for whom, and within which boundaries |
| 4–10 min | How work enters, becomes ready, moves, and becomes done |
| 10–20 min | Recurring and custom meetings: purpose, cadence, what is distinctive here, and what useful output looks like |
| 20–25 min | Ownership, collaboration, communication, and where durable output belongs |
| 25–30 min | Confirm agreements, disagreements, deferred questions, and owners |

Write prompts that start a conversation, not an interview checklist. Use examples only to unblock discussion. Tell the facilitator to name whether a statement describes current practice, an agreed change, a suggestion, or unresolved disagreement. Keep credentials, MCP installation, authentication, and other technical wiring out of the meeting — those are `/setup-awow`'s.

Show the brief and ask whether to use it. After approval, keep it at `{PROJECT}/proposals/workshop/meeting-brief.md` as the meeting handout and stop. Let the team meet in its own time.

## Process the workshop

Read the transcript plus the existing context under `{ANCHOR}/context/`. Build a coverage map for:

- the team profile — what the team works on, its stack, and any mission line — plus scope boundaries;
- board practice and work flow;
- conventions, members, and writing style;
- recurring and custom meetings;
- ownership, communication, and output placement;
- technical configuration still requiring hands-on setup (route it to `/setup-awow`; never infer it from the conversation).

Classify every usable statement as **current practice**, **agreed change**, **suggestion**, or **unresolved disagreement**. Do not convert one person's recollection, an unchallenged suggestion, or a disputed point into team context. When a board is wired, settle which one with the `board-target` skill, read it, and compare what it shows with what the team said; surface divergence rather than silently choosing one. This command never writes to the board.

Draft the proposals under `{PROJECT}/proposals/workshop/`, one file per destination:

- `mission.md` → `{ANCHOR}/context/team/mission.md` — the team profile, two to five plain sentences; a mission line only when the team stated one.
- `conventions/<name>.md` → `{ANCHOR}/context/team/conventions/REQUIRED/<name>.md` — only where the team's stated practice differs from what is already there.
- `members.md` → `{ANCHOR}/context/team/members.md` — roles, responsibilities, focus areas as stated, never inferred.
- `meetings/<slug>.md` → `{ANCHOR}/context/team/meetings/<slug>.md`:
  - For a common ritual, write only the meaningful ways this team differs from the generic lens in `_meeting-archetypes/`.
  - For a custom recurring meeting, describe how to recognise it, what matters, and what useful output looks like.
  - Use plain Markdown. Do not add frontmatter, identifiers, inheritance, or an `extends` syntax.
  - Do not create a meeting file when the generic lens already fits.

Present one synthesis gate with the coverage map, source evidence, disagreements, pending areas, and the actual proposed diffs — one line per destination file. Land only the selected proposals after explicit approval; accept a partial answer. Never copy the raw transcript into durable context. Leave uncovered topics pending and say which; a later workshop or `/update-context` picks them up.
