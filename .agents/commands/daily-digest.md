---
description: "Use when the user asks what the team shipped today or this week, wants a daily or weekly digest written up and raised as a PR, or says they have no idea what other people are working on."
phase: standardise
argument-hint: "[--week | YYYY-Www | YYYY-MM-DD] (optional — omit for today)"
prerequisites:
  - "Step 0 of /setup-awow complete (the agent can read and write the board)"
  - "Most of the team actively committing"
  - "Team has shipped at least three Seed cycles"
  - "For a weekly window only: daily digests exist for at least four working days of it"
removes_pain: "the I-have-no-idea-what-the-other-team-shipped-this-week problem"
---

# /daily-digest — aggregate a day or a week of activity into a team-wide synthesis

You aggregate all board, code, and (optionally) chat activity over a window — one day by default, or a Monday–Friday week — and produce a synthesis layer that helps the team stay aligned.

**Read-only against every source.** This command never mutates the board, the codebase, or any external system. It writes one markdown file and opens a pull request for it; nothing else.

The weekly window is not a summary of the dailies. It answers different questions at a different altitude, and it reads the dailies as input. Where a step below differs by window, both variants are stated.

You are not evaluating performance. You are producing a synthesis layer.

---

## Pipeline overview

```
Phase 0 ─ Window & reuse check
Phase 1 ─ Data collection
Phase 2 ─ Synthesis
Phase 3 ─ Markdown output (with eleventy front matter)
Phase 4 ─ Review gate  ──→ GATE (mandatory)
Phase 5 ─ Open the PR
```

---

## Phase 0 — Window & reuse check

### Resolve the window

Parse the argument. It selects one of two windows, and every step below runs over the window you resolve here:

- **No argument** → the **day** window, today.
- `YYYY-MM-DD` → the **day** window, that date.
- `--week` → the **week** window, the current ISO week.
- `YYYY-Www` (e.g. `2026-W12`) → the **week** window, that ISO week.

For a week window, resolve the ISO week to its Monday–Friday date range. If the team's working week differs, read `{HUB}/context/team/members.md` or `{HUB}/context/team/conventions/REQUIRED/labels.md` for the convention before assuming Mon–Fri.

State the resolved window back to the user in one line before doing any work — `Day: 2026-07-20` or `Week 2026-W29: Mon 13 Jul – Fri 17 Jul` — so a misparsed argument is caught before collection, not after.

### Reuse check

The output path depends on the window: `digests/YYYY-MM-DD.md` for a day, `digests/weekly/YYYY-Www.md` for a week.

If a digest already exists at that path, ask the user whether to:

- **Regenerate** — run the full digest again and overwrite
- **Reuse** — use the existing markdown as-is

---

## Phase 1 — Data collection

Collect the day's activity once, via the shared collection step, then project the shallow view this digest needs.

### Run the shared collection step

Follow `{HUB}/context/tooling/activity-collection.md`, falling back to `{AWOW_ROOT}/context/tooling/activity-collection.md` (a vendored copy wins over the shipped one): **reuse `activity/YYYY-MM-DD.json` if it already exists for the day, otherwise produce it.** That step owns the board / code / chat queries (all keyed off `{HUB}/context/tooling/board.md`), the normalised snapshot schema, and the private-team gate — so you do not re-query per lens, and the private-team exclusion is already applied.

**An absent board pointer is a question, not a stop.** If `{HUB}/context/tooling/board.md` is missing, infer the board from the git remote — a GitHub remote means GitHub Issues via `gh`. Do not guess a board from a GitLab, Bitbucket, or Azure DevOps remote; those map to several products. With no remote, or with `gh` absent or unauthenticated, ask the user once which board they use and how to reach it, and do not offer the `gh` path. Record the answer at `.awow/board-session.md` with a `session:` line, and read it instead of asking again — ignore a note whose `session:` does not match this session. Offer `/setup-awow` Step 1 to make the answer durable; never write `{HUB}/context/tooling/board.md` yourself.

This relaxation covers an absent pointer only. **A fatal auth failure on a data source still stops the run** — surface it and do not synthesise from a half-snapshot.

If the snapshot still cannot be produced for any other reason, stop and surface it.

### Week window — collect across the range

Run the collection step once per day in the range and merge the results, reusing any `activity/YYYY-MM-DD.json` already on disk. Do not re-query a day whose snapshot exists.

### Week window — two extra primary sources

**The week's daily digests.** Read every `digests/YYYY-MM-DD.md` in the range, in full. These are the richest input you have: they already carry synthesised narratives, project snapshots, cross-team connections, and structural observations. **A missing daily digest is a data-coverage gap — name it in the output; never silently skip the day.**

**Last week, for comparison.** If `digests/weekly/YYYY-W(ww-1).md` exists, read it to detect **dropped** connections — active last week, absent this week — and to compare project trajectories. If it does not exist, say so once and omit the dropped-connections subsection rather than leaving it empty.

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

### Week window — different questions, different shapes

The day window asks "what happened today?". The week window asks:

- What actually **moved** this week (outcomes, not activity)?
- What **shifted** between Monday and Friday (trajectory)?
- Where did the team **spend its time** (workload distribution)?
- What **patterns** are emerging (recurring gaps, growing collaborations)?
- What should change next week (signals, not recommendations)?

Three shapes change with it:

- **Counts** become weekly: issues created, issues completed, issues stale (in progress all week with no state change), active projects, PRs merged, cross-links surfaced.
- **Connections** become **collaborations**, classified: **active** (appeared 3+ days), **emerging** (first appeared this week), **dropped** (active last week, absent this week).
- **Project status** becomes **trajectory**: where each project stood Monday versus Friday, and the direction of travel.

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

Write to `digests/YYYY-MM-DD.md` (day window) or `digests/weekly/YYYY-Www.md` (week window).

### Front matter

The digest is a page in the team's eleventy site, so it opens with YAML front matter. awow does not know that site's layouts or permalink scheme, so **infer them: if `digests/` already holds a digest carrying front matter, copy its key set exactly** — same keys, same order, same `layout` and permalink if present — and fill in this run's values.

If there is no sibling to copy from, emit this default and nothing more:

```yaml
---
title: "Daily digest — 2026-07-20"
date: 2026-07-20
tags: [digest, daily]
---
```

For a week window:

```yaml
---
title: "Weekly digest — 2026-W29"
date: 2026-07-17
tags: [digest, weekly]
---
```

`date` is the window's last day. **Never invent a `layout:` key.** Naming a layout the site does not have breaks its build, which is a worse failure than a page rendering unstyled. The site owner adds `layout` once, to one digest, and every later run inherits it.

Then the body:

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

### Week window — output format

Write to `digests/weekly/YYYY-Www.md` instead:

````markdown
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
* Days in the window with no daily digest (coverage gaps).

---

## Pipeline / sales / opportunity weekly view (optional)

For each active opportunity:

* **<Client>** — Status: <Active / Pending / Critical / Slow>. Change vs last week: <description>. Next action: <what + who>.
````

Every issue identifier in a weekly digest must correspond to an item actually seen during collection or named in a daily digest you read. The wider window makes invention easier and harder to spot — never guess an ID.

### Issue references

All board identifiers referenced must correspond to actual issues seen in Phase 1. Verify every identifier before finalizing — a digest that cites an issue nobody can find undermines trust in every other line of it.

### Delivery

Write the file, then go to Phase 4. Do not share, send, or publish anything from this phase.

---

## Phase 4 — Review gate

**Mandatory. Never skip.** Nothing leaves this repo until the user has read the digest.

1. Show the user the file path and a short summary: the window, the number of items synthesised, the sources and their status, and any coverage gaps.
2. Present the options verbatim:

```
Digest written to <path>.

- "ship"            — open a PR with this digest
- "edit <what>"     — change it, then come back here
- "stop"            — leave the file on disk, no PR
```

3. **Wait for an explicit answer.** On `edit`, make the change, re-summarise, and return to this prompt.
4. On `stop`, say where the file is and finish. The file staying on disk uncommitted is a valid outcome, not a failure.

---

## Phase 5 — Open the PR

Only after `ship`.

1. Create a branch off the current branch: `digest/YYYY-MM-DD` for a day window, `digest/YYYY-Www` for a week window. If the branch already exists, reuse it.
2. Commit **only** the digest file. Never sweep unrelated working-tree changes into a digest commit — check `git status` first and, if anything else is staged, unstage it and say so.
3. Commit message: `Add the daily digest for YYYY-MM-DD.` or `Add the weekly digest for YYYY-Www.`
4. Push and open the PR with `gh`. Title matches the commit message; body is the digest's narrative section, so a reviewer sees the substance in the PR itself.
5. Report the PR URL.

**When the PR cannot be opened.** If there is no git remote, or `gh` is absent or unauthenticated, do not fail silently and do not skip the commit. Commit on the branch, then tell the user exactly what is missing and the literal command to finish it themselves — for example `gh pr create --fill --head digest/2026-07-20`. A digest committed on a branch with the user told how to raise the PR is a complete run; a digest silently left unpushed is not.

---

## Behavioral boundaries

- **Stay data-grounded.** Only synthesize from actual board / code / chat data. Never fabricate or attribute incorrectly.
- **Never evaluate individual performance.**
- **Never make strategic recommendations.** Surface connections; let humans decide.
- **Respect private-team boundaries.** Private-team details never appear in shared digests.
- **Read-only against every source.** The board, the codebase, and every external system are read, never written. The only writes are the digest file and its branch.
- **Never open a PR without the Phase 4 gate.** No exceptions, no "obviously fine" runs.
- **No HTML.** This command produces markdown. A styled standalone digest is `/artifact`'s job — it owns the house style and reads the design system. Do not render HTML here, and do not create `digests/TEMPLATE.html`.

---

## Handing off

The day's snapshot (`activity/YYYY-MM-DD.json`) is the expensive part and it is now on disk. The deep projection over the same snapshot — the durable-knowledge candidates — is a separate lens with its own gate, so offer it rather than running it:

> Run `/kb-mine` against the same snapshot? It reads each item's deep `payload` for knowledge worth keeping, and stages candidates for the `/kb-synthesize` gate. Nothing lands in the knowledge base without your approval.

Offer once. If the user declines, or if this run produced no snapshot, say nothing further.
