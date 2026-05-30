---
phase: spread
prerequisites:
  - "The project has been worked in an agent (Claude Code sessions under ~/.claude/projects/<encoded-path>/, OR an mlflow_export dir from the mlflow-export skill)"
removes_pain: "the I-can't-see-how-this-project-actually-got-built problem"
consumes: claude-code-session-logs OR mlflow-export-traces
when-to-use: "You want a visual, whole-project read of how a repo was built across many agent sessions — the fan-out/contract rhythm, handoffs, idle time, context load, per-user split, and per-session coaching. Works from raw Claude Code logs (zero setup) or an mlflow_export of Databricks traces (multi-user)."
when-not-to-use: "You only need board-linked prose reports or cross-team digests — use awow-usage-coach / the digests directly. For deep prompt-craft scoring, use prompt-skill-analysis."
---

# /project-retrospective — visual timeline + meta-analysis of a project's sessions

Build an interactive timeline of how a repo was actually built across its agent sessions, and turn it into a whole-project read plus optional per-session coaching. This is the **visual entry** to awow's session analysis. It reads **two sources**:
- **Claude Code logs** under `~/.claude/projects/` (`--project-path`) — zero setup, richest detail (file edits, per-turn context, handoffs).
- **An `mlflow_export/` dir** of Databricks traces (`--mlflow-export`) from the `mlflow-export` skill — supports **multiple users**; bars colour by working directory (traces carry no file paths), and there is no per-turn context.

When sessions span **more than one day**, the view automatically switches to a **calendar mode**: a day-navigator strip (empty calendar gaps collapsed) sits above a per-day detail timeline — click a day or press ←/→ to page through days.

Read [`.agents/skills/awow-usage-coach/SKILL.md`](../skills/awow-usage-coach/SKILL.md) before coaching; it owns the intent taxonomy and the Mode B voice. Read [`guides/guide-session-timeline.html`](../../guides/guide-session-timeline.html) if you need to explain what the view shows.

## Inputs

- The target repo path (default: the current repo root) **or** an `mlflow_export` directory.
- Optional: a transcripts dir of `<session-id>.txt` exports (Claude logs only — from the `session-export` skill), a `--tz-offset` for display, `--user <name>` to scope an MLflow export to one person, and whether to produce per-session coaching + an overview panel.

## What you do

1. **Confirm scope + source.** Resolve the repo path or the `mlflow_export` dir. Ask the user for their UTC offset if you do not already know it (logs/traces are UTC; the view must display local time). Do not assume. If an MLflow export has more than one user, ask whether to analyse the whole team or one user.
2. **Pick the coaching degree (gate the cost).** Before reading transcripts, tell the user the cost and let them choose: **(1) Timeline only** (~0 tokens) · **(2) Overview + lessons** · **(3) + per-session reviews** (scales with session count — and on MLflow data each review is necessarily thin, since only the first prompt, final response, and tool names survive per conversation).
3. **Build the timeline.** Run the tool and report the session count:
   ```
   # Claude Code logs:
   python tools/session_timeline.py --project-path <repo> --out <out-dir> --tz-offset <hours>
   # MLflow export (optionally one user):
   python tools/session_timeline.py --mlflow-export <mlflow_export-dir> --out <out-dir> --tz-offset <hours> [--user <name>]
   ```
   Add `--transcripts <dir>` (Claude logs) to scope the view and link transcripts, and `--context-window <n>` if the team's window is not 200000.
4. **Read the picture, then write the overview.** Read `sessions.json` (not the raw logs) for the aggregate shape: session count, peak parallel/day, idle gaps, per-session peak context (Claude logs only), functional-area / working-dir mix, per-user split, token cost. For a multi-day dataset, lead with the **cadence over the calendar** (quiet stretches vs. crunch days), not a single-evening rhythm. Draft a whole-project meta-analysis to `coach_reviews/<repo>-retrospective/OVERVIEW.md` first; pass it as `--overview` once approved so it renders as the default panel. The overview is **private session-derived data** — write it to `coach_reviews/` (gitignored), never to `proposals/` or any tracked path; committing it to a public repo leaks customer data.
5. **Coach per session only if degree 3.** Follow `awow-usage-coach` Mode B per session and write one `<short-id>.md` into the gitignored `coach_reviews/` dir, then rebuild with `--coach-dir`. Reviews and the timeline outputs (`sessions.json`, `timeline.html`) are team session data — keep them out of `proposals/` and every tracked path. For deep prompt-craft scoring, defer to `prompt-skill-analysis`.
6. **Open it.** Tell the user the path to `timeline.html`; it is self-contained (open by double-clicking).

## Rules

- Treat the idle gaps the tool reports (no event logged anywhere) as elapsed-not-active time; lead the overview with active time and the parallel-compression factor, not the raw span.
- Never embed secrets, keys, or private credentials a session pasted into a prompt into the overview or a coach review; flag them to the user out-of-band instead.
- Scope to an exported snapshot (`--transcripts`) when sessions are still being written, so the view stays stable while work continues.
