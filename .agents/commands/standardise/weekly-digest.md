---
phase: standardise
prerequisites:
  - "Step 0 of /setup-awow complete (board MCP wired)"
  - "/daily-digest has been running for at least four working days"
  - "Most of the team actively committing"
removes_pain: "the I-cannot-see-what-shifted-Mon-to-Fri problem"
---

# /weekly-digest — synthesize a full week of activity into a trajectory view

You aggregate the week's daily digests, board activity, code activity, and (optionally) voice memos into a higher-level synthesis. This is **not** a summary of the daily digests. It answers different questions: what moved, what stalled, what shifted, where the team spent its time.

**Read-only.** This command never mutates the board, the codebase, or any external system. Output is `digests/weekly/YYYY-Www.md`.

You are not evaluating performance. You are producing a weekly synthesis layer.

---

## 0. Determine target week

Parse the argument:

- If `YYYY-Www` is provided (e.g. `2026-W12`), use that ISO week.
- If no argument is provided, use the current ISO week.
- Determine the Monday–Friday date range. (Adjust if the team's working week differs — read `context/team/members.md` or `context/team/conventions/REQUIRED/labels.md` for any team-specific working-week notes.)

---

## 1. Data collection

Collect for the full week.

### A. Daily digests

Read all daily digest files for the target week from `digests/YYYY-MM-DD.md`. These are the primary source — they already contain synthesized narratives, project snapshots, cross-team connections, structural observations.

For each day:

- If a daily digest exists, read it in full.
- If a daily digest is missing, note the gap. This is a data-coverage issue worth flagging.

### B. Board activity (weekly aggregate)

Pull all issues updated during the target week via the board MCP. For each issue:

- Creation date (new this week vs existing)
- State transitions during the week
- Assignee
- Project

Counts: issues created, issues completed (moved to Done), issues stale (in progress all week with no state change).

**Private-team data is strictly excluded** from the shared weekly digest. Pull it internally only for per-person sections.

### C. Code activity (weekly aggregate)

Pull commits, PRs, and review events for the target week. Per repo: PRs merged, PRs opened, commits per contributor. Map code activity to board issues where possible.

### D. Previous week comparison

If a weekly digest exists for the previous week (`digests/weekly/YYYY-W(xx-1).md`), read it to:

- Identify connections that were active last week but absent this week (dropped connections).
- Compare project trajectories.

---

## 2. Synthesis rules

### This is not a summary of daily digests

Do not concatenate or condense the daily digests. The weekly digest answers different questions:

- **What actually moved this week?** (outcomes, not activity)
- **What shifted between Monday and Friday?** (trajectory changes)
- **Where did the team spend its time?** (workload distribution)
- **What patterns are emerging?** (recurring gaps, growing collaborations)
- **What should change next week?** (signals, not recommendations)

### Cross-relevance aggregation

Instead of listing daily connections, aggregate into:

- **Active collaborations** — connections that appeared 3+ times across the week's daily digests.
- **Emerging connections** — connections that appeared for the first time this week.
- **Dropped connections** — connections that were active last week but absent this week.

### Personalized week-in-review

For each team member (from `context/team/members.md`), answer:

- What was their most significant contribution this week?
- What commitments are they carrying into next week?
- What cross-team items need their attention?

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

A matrix showing who worked on which projects this week, derived from voice memos, board activity, and code activity. Use block characters to indicate relative effort:

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

## 4. Output delivery

After generating:

1. Write the output to `digests/weekly/YYYY-Www.md`.
2. Present a summary to the user.
3. Ask if they want to share specific sections with specific team members (but do NOT execute any sharing without confirmation).

---

## 5. Behavioral boundaries

You must:

- Stay data-grounded. Only synthesize from actual daily digest / board / code / memo data.
- Never fabricate activity or attribute work incorrectly.
- Never evaluate individual performance.
- Never make strategic recommendations — only surface connections, signals, and patterns.
- **Private-team data is strictly excluded from the shared digest.** Not in general sections, not in personalized sections, not in the pipeline view. If an opportunity only exists on a private-team board, omit it entirely.
- This command is read-only. Do not create, update, or modify any board state.
- All issue identifiers referenced must correspond to actual issues seen in data collection. Do not invent.
