# Standardise reporting

The read-only synthesis layer: a day, then a week — each a different altitude on the same activity.

> **TL;DR** — The board *lists* what changed; nobody can see the shape of it. `/daily-digest`
> answers the harder question — what happened, where is it heading, what connects, and what
> should someone know that they don't. One command, two windows: a day, or `--week` for a
> Mon–Fri altitude that reads the dailies as input. It reads board, code, and optional chat,
> writes one markdown file, and opens a PR only after you approve. Nothing else is mutated.

## When this layer makes sense

Reporting earns its keep only once there is a steady stream of activity to synthesise: at least
three Seed cycles shipped, most of the team actively committing, and Step 0 of `/setup-awow`
complete. The week window adds one prerequisite — dailies covering at least four working days of
it, because they are its richest input.

## The two altitudes

The week is not a stack of dailies. It reuses their collection and synthesis machinery to ask
different questions.

```mermaid
flowchart LR
  act["Activity — board · commits & PRs · chat (optional)"] --> day["day window: 'what happened today?'"]
  day -->|the week's dailies, read in full| week["week window: 'what shifted Mon→Fri?'"]
  prev["Last week's digest"] -->|compare → dropped connections, trajectory| week
```

| Window | Argument | Output | Extra prerequisite |
| --- | --- | --- | --- |
| One day | none, or `YYYY-MM-DD` | `digests/YYYY-MM-DD.md` | — |
| Mon–Fri | `--week`, or `YYYY-Www` | `digests/weekly/YYYY-Www.md` | dailies for ≥4 working days |

The resolved window is stated back to you in one line before any collection, so a misparsed
argument is caught early. Department-level cross-team visibility is a layer up and not a
Standardise digest — see `/okr-cascade`; the old cross-team stub was retired into it.

## Synthesis, not aggregation

Re-listing what the board already lists adds nothing. The job is four questions:

- **What actually happened?** A narrative, not bullets.
- **What's the trajectory?** Which projects are moving, stalling, or blocked.
- **What connects?** Work by one person that bears on another's — dependencies and overlaps
  nobody tracked formally.
- **What should someone know that they don't?** Cross-relevance the board never surfaces.

Be specific or stay silent. *"A's rate-limit work could inform B's gateway redesign"* is useful;
*"everyone should stay aligned"* is noise. Per-person sections follow the same rule — an empty one
is fine, don't force relevance.

## The pipeline

```
Phase 0 ─ Window & reuse check
Phase 1 ─ Data collection      (board + code + optional chat)
Phase 2 ─ Synthesis            (the four questions)
Phase 3 ─ Write                → digests/…
Phase 4 ─ Review gate          — mandatory: "ship" · "edit <what>" · "stop"
Phase 5 ─ Open the PR          — only after "ship"
```

### What it collects

| Source | What lands, and the catch |
| --- | --- |
| Board | Every issue touched in the window: who, what changed, which project. A private surface (e.g. a leadership-only board) is read to inform per-person sections but **excluded from anything shared**. |
| Code | Commits, PRs, reviews, mapped back to issues where a branch or message names one. A repo active with no ticket is a gap signal worth naming. |
| Chat (optional) | Channel messages only, where a channel→project mapping exists. **Meeting transcripts are always excluded** — they carry personal data and belong to `/process-transcript`. |

An empty result on a day you know was busy is treated as a probable query fault — wrong team name,
stale credentials — not as truth. `skip chat` and `skip code` are honoured; the digest produces
from whatever returned.

### What the week window adds

- **The week's dailies**, read in full — already-synthesised narratives, snapshots, connections. A
  *missing* daily is a data-coverage gap to name, never a day to silently skip.
- **Last week's digest**, if `digests/weekly/YYYY-W(ww-1).md` exists — to detect **dropped**
  connections and compare trajectories. Absent, it says so once and omits the subsection.
- **Weekly shapes:** weekly counts (created, completed, stale, active projects, PRs merged);
  collaborations classified **active** (3+ days), **emerging** (first this week), or **dropped**
  (active last week, absent now); a project trajectory report (Monday vs Friday plus direction); a
  team activity heatmap of relative effort; and a personalised week-in-review.

### The gate and the PR

Phase 4 is mandatory and never skipped: you get the file path, the window, the item count, the
sources and their status, and any coverage gaps, then choose. On `ship` it branches
(`digest/YYYY-MM-DD` or `digest/YYYY-Www`), commits **only** the digest file, and opens the PR with
the narrative as the body. No remote or no `gh` is not a silent failure — it commits on the branch
and tells you the literal command to finish it.

Afterwards it offers `/kb-mine` over the same snapshot once, and drops it if you decline.

## Boundaries that always hold

- **Read-only against every source.** The only writes are the digest file and its branch.
- **Data-grounded.** Every board identifier cited must be one actually seen during collection —
  counts and IDs are never invented. The wider week window makes invention easier and harder to
  spot.
- **Never evaluative.** No individual performance assessment, no strategic recommendations —
  surface connections and let humans decide.
- **Private stays private.** Private-team detail never reaches a shared digest.
- **No HTML.** This produces markdown. A styled standalone digest is `/artifact`'s job — it owns
  the house style and reads the design system.

## Sources of truth

- [`.agents/commands/daily-digest.md`](../.agents/commands/daily-digest.md) — both windows: the six phases, the collection surfaces, the review gate, and the behavioural boundaries
- [`.agents/commands/okr-cascade.md`](../.agents/commands/okr-cascade.md) — the department altitude that replaced the retired cross-team stub
- [`.agents/commands/kb-mine.md`](../.agents/commands/kb-mine.md) — the deep lens over the same snapshot, offered at hand-off
- [`.agents/commands/awow-add.md`](../.agents/commands/awow-add.md) — how a team opts into the Standardise commands
- Companion guides: [session correlation](guide-session-correlation.md) — the join that lets a digest name the session behind an item; [trace analysis](guide-trace-analysis.md) — the read side over the same sessions; [design systems & HTML artifacts](guide-design-system-and-artifacts.md) — where a styled digest gets its house style
