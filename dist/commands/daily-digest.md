---
description: "aggregate daily activity into a team-wide synthesis"
phase: standardise
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "Most of the team actively committing"
  - "Team has shipped at least three Seed cycles"
removes_pain: "the I-have-no-idea-what-the-other-team-shipped-this-week problem"
---

# /daily-digest — aggregate daily activity into a team-wide synthesis

You aggregate all board, code, and (optionally) chat activity from today and produce a synthesis layer that helps the team stay aligned.

**Read-only.** This command never mutates the board, the codebase, or any external system. Output is a markdown file under `digests/YYYY-MM-DD.md`. Optional email rendering and delivery require explicit user approval.

You are not evaluating performance. You are producing a synthesis layer.

---

## Pipeline overview

```
Phase 0 ─ Input & mode detection
Phase 1 ─ Data collection
Phase 2 ─ Synthesis
Phase 3 ─ Markdown output
Phase 4 ─ (Optional) HTML rendering   ──→ GATE (manual review)
Phase 5 ─ (Optional) Email send
```

---

## Phase 0 — Input & mode detection

### Email mode (optional)

If the user provides recipient email addresses as arguments, render the digest as HTML and send after approval. Parse as a comma-separated list. Validate that entries look like email addresses; ask for confirmation if any look malformed.

If no emails are provided, produce the markdown digest only (skip Phases 4–5).

### Reuse check

If a digest already exists for today (`digests/YYYY-MM-DD.md`), ask the user whether to:

- **Regenerate** — run the full digest again and overwrite
- **Reuse** — use the existing markdown as-is

---

## Phase 1 — Data collection

Collect the day's activity once, via the shared collection step, then project the shallow view this digest needs.

### Run the shared collection step

Follow `{HUB}/context/tooling/activity-collection.md`: **reuse `activity/YYYY-MM-DD.json` if it already exists for the day, otherwise produce it.** That step owns the board / code / chat queries (all keyed off `{HUB}/context/tooling/board.md`), the normalised snapshot schema, and the private-team gate — so you do not re-query per lens, and the private-team exclusion is already applied.

If the snapshot cannot be produced (no `{HUB}/context/tooling/board.md`, or a fatal auth failure on a source), stop and surface it — do not synthesise from a half-snapshot.

### Project the digest's shallow view

Read from the snapshot only what synthesis needs: for each item its `kind`, `ref`, `actor`, `title`, and `activity` (state transitions, comments, creations). **Do not load `payload.diff`** — the digest narrates what moved, not code contents. Map code activity to board issues via the refs the snapshot already carries.

Honour each source's `status`: reflect any `error` / degraded source honestly in the Data Sources table (Phase 3) — never invent data for a failed source. If every chat channel failed, surface the banner: "⚠ No chat data available today — all channels failed." Sanity-check a zero-issue board result on a day you know was active before trusting it.

### Private-team, per-person exception

The shared gate keeps private-team data out of the snapshot, hence out of every shared section. The one place the digest may use private data is per-person takeaways (Phase 2.C) for a team member who has access — pull that internally and exclude it from any shared rendering. It never enters the snapshot.

### Escape hatch

If the user says "skip chat" or "skip code", honour it — collect (or project) only the remaining sources. The digest still produces from whatever returned.

---

## Phase 2 — Synthesis

### Do not just list changes

The value is synthesis, not aggregation. The board already shows a list of changes.

Answer:

- **What actually happened today?** (narrative, not bullets)
- **What's the trajectory?** (projects moving / stalling / blocked)
- **What connects?** (work by one person that relates to work by another)
- **What should someone know that they don't?** (cross-relevance)

### Cross-relevance detection

For each piece of work done today:

1. Does this relate to work another team member is doing on a different project?
2. Does this unblock or inform something another team member is waiting on?
3. Does this create a dependency or overlap that isn't formally tracked?
4. Would knowledge of this work change how another team member approaches their own tasks?

Be specific. "<Name>'s rate-limit work could inform <Name>'s gateway redesign" is useful. "Everyone should stay aligned" is not.

### Personalized takeaways

Per team member (from `{HUB}/context/team/members.md`), answer:

- What happened today that is relevant to YOUR work specifically?
- Decisions or deliverables from others that affect your projects?
- Opportunities to collaborate or share knowledge?

Only include genuinely relevant signals. Empty sections are fine — don't force relevance.

---

## Phase 3 — Markdown output

Write to `digests/YYYY-MM-DD.md`:

```markdown
# Daily digest — YYYY-MM-DD

## Data sources

| Source | Scope | Status |
|---|---|---|
| Board — <tool> | Issues updated today, plus project status updates | `<N> issues touched` |
| Code — <hosting> | Commits, PRs, reviews | `<N> repos with activity` |
| Chat — <tool>, channel messages only | Per `config/chat-to-project.yaml` | `<N> channels / <M> messages` |

If any source failed or returned empty, reflect that in the Status column. Do not fabricate counts. Do not list private-team data here.

---

## Day-at-a-glance

| Metric | Value |
|---|---|
| Issues updated | X |
| Issues created | X |
| Issues completed | X |
| State transitions | X |
| Active projects | X |
| Commits | X |
| PRs opened / merged | X / X |
| Chat channels with messages | X |

---

## Team narrative

6–12 sentences synthesizing what happened today. Coherent narrative, not a list.

---

## Project status snapshot

For each active project that had activity today:

### <Project name>
**Today:** What changed.
**Trajectory:** On track / slowing / blocked / accelerating.
**Key signal:** The one thing worth knowing.

---

## Cross-team connections

* **<Person A>** ↔ **<Person B>**: What connects and why it matters.
* **<Person A>** → **<Person C>**: One-directional relevance.

---

## Code activity

* `<repo>` — what was pushed / merged and by whom.
* Repos with activity not reflected in the board (gap signal).

---

## Personalized takeaways

### For <Person>
* Relevant signal from others' work.
* Action or awareness item.

*(Skip any team member with no signals today.)*

---

## Structural observations

* Gaps identified (work without tickets, projects without updates).
* Stale issues that haven't moved.
* Untracked dependencies.
* Channel mapping drift (failed channels from Phase 1.C, with reasons).
```

### Issue references

All board identifiers referenced must correspond to actual issues seen in Phase 1. Verify every identifier before finalizing. In HTML mode these become clickable links; broken links undermine trust.

### Delivery

1. Write the output to `digests/YYYY-MM-DD.md`.
2. Present a summary to the user.
3. If in email mode, proceed to Phase 4. Otherwise ask if they want to share specific sections (but do NOT execute any sharing without confirmation).

---

## Phase 4 — HTML rendering (email mode only)

Skip if no recipient emails were provided.

Read the HTML template at `digests/TEMPLATE.html`. The template is the single source of truth for email structure with `{{PLACEHOLDER}}` markers and an email-compatible table layout. Do not deviate. If the template and rules conflict, the template wins.

Rendering rules:

- Replace all `{{PLACEHOLDER}}` values with actual digest data.
- Use **table layout** (not div-only) for the outer wrapper and stats bar — required for email client compatibility.
- All styles must be **inline** — email clients strip `<style>` blocks.
- Format the date as "Day, DD Month YYYY".
- Count stats from the actual digest data — do not fabricate.
- Only include project cards for projects with activity today.
- Skip personalized sections for team members with no signals.
- Private-team data appears only in personalized takeaways for team members who have access; never in general sections.
- Use HTML entities for special characters (`&mdash;`, `&rarr;`, `&harr;`).
- **Board identifiers must be clickable links** with inline styling.

Write to `digests/YYYY-MM-DD.html`.

---

## Phase 5 — Manual review gate (email mode only)

**Mandatory. Never skip.**

1. Open the HTML file in the user's browser.
2. Present a summary:

```
The daily digest email has been rendered and opened in your browser.

Recipients: <list>
Digest date: YYYY-MM-DD
File: digests/YYYY-MM-DD.html

When ready:
- "send"           — approve and send to all recipients
- "send to <addr>" — send to specific recipients only
- "edit"           — tell me what to change before sending
- "cancel"         — do not send
```

3. **Wait for explicit user approval.**
4. If the user requests edits: make the changes, re-open, return to the approval prompt.

---

## Phase 6 — Send email (email mode only)

Only execute after explicit user approval. Use the team's configured email integration. After sending, confirm:

```
Email sent to:
- <recipient 1>
- <recipient 2>

Digest: digests/YYYY-MM-DD.md
HTML: digests/YYYY-MM-DD.html
```

---

## Behavioral boundaries

- **Stay data-grounded.** Only synthesize from actual board / code / chat data. Never fabricate or attribute incorrectly.
- **Never evaluate individual performance.**
- **Never make strategic recommendations.** Surface connections; let humans decide.
- **Respect private-team boundaries.** Private-team details never appear in shared digests.
- **Read-only.**
- **Never send email without explicit user approval.**
- **Never hardcode recipients.**
