---
phase: standardise
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "/daily-digest has been running for at least four working days"
  - "Most of the team actively committing"
removes_pain: "the I-cannot-see-what-shifted-Mon-to-Fri problem"
---

# /weekly-digest — synthesize a full week of activity into a trajectory view

You aggregate a week of activity into a higher-level synthesis: what moved, what stalled, what shifted, where the team spent its time. This is **not** a summary of the daily digests — it answers different questions at a different altitude.

**Read-only.** This command never mutates the board, the codebase, or any external system. Output is `digests/weekly/YYYY-Www.md`.

You are not evaluating performance. You are producing a weekly synthesis layer.

---

## This command is /daily-digest at a weekly altitude

`/weekly-digest` reuses `/daily-digest`'s workings — don't restate them, run them over a wider window. **Read `/daily-digest` first.** The following carry over unchanged, just scaled from one day to a Monday–Friday week:

- **Data collection** — the same board, code, and chat surfaces, the same sync-resilience handling (hard vs partial vs clean failure), and the same escape hatches ("skip chat", "skip code").
- **Synthesis discipline** — synthesis, not aggregation; cross-relevance detection; genuinely-relevant personalized sections only (empty is fine).
- **Behavioral boundaries** — read-only; data-grounded; never fabricate or misattribute; no performance evaluation; no strategic recommendations; **private-team data strictly excluded from the shared digest** (pulled internally only for per-person sections).

This file specifies **only what differs** at the weekly altitude.

---

## 1. Target week (the parameter)

Parse the argument:

- `YYYY-Www` (e.g. `2026-W12`) → use that ISO week.
- No argument → the current ISO week.
- Resolve to the Monday–Friday date range. If the team's working week differs, read `context/team/members.md` or `context/team/conventions/REQUIRED/labels.md` for the convention.

Every collection and synthesis step runs over this range instead of "today".

---

## 2. What changes from /daily-digest

### A. One extra primary source — the week's daily digests

Read every `digests/YYYY-MM-DD.md` in the target week. These are your richest input: they already contain synthesized narratives, project snapshots, cross-team connections, and structural observations. Read each in full. **A missing daily digest is a data-coverage gap — note it; do not silently skip the day.**

### B. One extra comparison — last week

If `digests/weekly/YYYY-W(ww-1).md` exists, read it to detect **dropped** connections (active last week, absent this week) and to compare project trajectories.

### C. Aggregate, don't re-collect

Run daily-digest's board / code / chat collection across the whole week, then transform the result into weekly shapes:

- **Counts:** issues created, issues completed, issues stale (in progress all week with no state change), active projects, PRs merged.
- **Collaborations** instead of single-day connections: **active** (appeared 3+ days), **emerging** (first appeared this week), **dropped** (active last week, absent this week).
- **Trajectory** instead of a single-day snapshot: where each project stood Monday vs Friday, and the direction of travel.

### D. Different questions

The daily digest asks "what happened today?". The weekly asks:

- What actually **moved** this week (outcomes, not activity)?
- What **shifted** between Monday and Friday (trajectory)?
- Where did the team **spend its time** (workload distribution)?
- What **patterns** are emerging (recurring gaps, growing collaborations)?
- What should change next week (signals, not recommendations)?

---

## 3. Output format

Write to `digests/weekly/YYYY-Www.md`:

```markdown
# Weekly digest — YYYY-Www (Mon DD MMM – Fri DD MMM)

## Week-at-a-glance

| Metric | Value |
|---|---|
| Issues created | X |
| Issues completed | X |
| Issues stale | X (in progress all week, no updates) |
| Active projects | X |
| Code PRs merged | X |
| Cross-links surfaced | X |

---

## Weekly narrative

8–15 sentences synthesizing what happened across the team(s) this week. Coherent narrative answering: What were the 2–3 dominant threads? What shifted between Monday and Friday? What was unexpected?

---

## Project trajectory report

For each active project:

### <Project name>

| | |
|---|---|
| **Start of week** | Status / trajectory on Monday |
| **End of week** | Status / trajectory on Friday |
| **Direction** | Accelerating / On track / Slowing / Stalled / Pivoted / New / Closed |
| **Key events** | 2–3 bullets |
| **Next-week signal** | What to watch for |

Projects with **no updates all week** get a separate "Silent projects" subsection.

---

## Team activity heatmap

A matrix showing who worked on which projects this week, derived from board activity, code activity, and (where present) `/process-transcript` attribution signals. Use block characters to indicate relative effort:

```
              ProjectA  ProjectB  ProjectC  Content  Platform  Internal
Person A      ███       ██        █                            ██
Person B      ██                  ███                ██
Person C      █                             ███      ██
Person D                █████                        █
Person E                ██                           ███
```

Use 1–5 blocks to represent relative time allocation (not precise hours). Derive from board issue assignments and commits; if `/process-transcript` outputs are present for the week, fold in their attribution signals. Leave blank if no signals.

---

## Cross-team connections

### Active collaborations (appeared 3+ days)

* **<Person A>** ↔ **<Person B>** (<project>): Description of ongoing collaboration.

### Emerging connections (new this week)

* **<Person A>** → **<Person C>** (<project>): Description of new connection.

### Dropped connections (active last week, absent this week)

* **<Person A>** ↔ **<Person B>** (<project>): Was active last week, no signals this week.

---

## Code activity

Weekly summary per repo:

* `<repo>` — X commits, Y PRs merged by [contributors]. Key changes: <summary>.

---

## Personalized week-in-review

### For <Person>

* **Top contribution:** Their most significant delivery or progress this week.
* **Carried into next week:** Outstanding commitments or open items.
* **Cross-team:** Items from others that need their attention.

*(Repeat for each team member. Skip members with no signals.)*

---

## Structural observations

Roll-up of daily structural observations, deduplicated and prioritized:

* Recurring gaps (flagged on multiple days).
* Unresolved items from last week.
* New structural concerns.

---

## Pipeline / sales / opportunity weekly view (optional)

For each active opportunity:

* **<Client>** — Status: <Active / Pending / Critical / Slow>. Change vs last week: <description>. Next action: <what + who>.
```

---

## 4. Delivery

Follow `/daily-digest`'s delivery pattern, but write to `digests/weekly/YYYY-Www.md`: write the file, present a summary, and ask before sharing any section with anyone (do **not** share without confirmation). If the team uses daily-digest's email mode, the same render → review-gate → send flow applies — never send without explicit approval.

---

## 5. Boundaries

All of `/daily-digest`'s behavioral boundaries apply (see the weekly-altitude section above). One bears repeating because the weekly view spans more data: **every issue identifier referenced must correspond to an actual issue seen during collection — never invent or guess one.**
