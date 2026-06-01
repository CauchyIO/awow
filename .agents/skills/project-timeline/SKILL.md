---
name: project-timeline
description: "Build an interactive visual timeline + whole-project read of how a repo was built across many agent sessions — the fan-out/contract rhythm, handoffs, idle time, context load, per-user split, token cost, and optional per-session coaching. Reads raw Claude Code logs (zero setup, richest detail) or an mlflow_export of Databricks traces (multi-user; auto-split into one dashboard per project, with an in-UI user filter). Use when the user wants to see how a project actually got built across sessions, asks for a visual project/session timeline, or wants a whole-project read to base coaching on. Not for board-linked prose digests (use the digests) or deep prompt-craft scoring (use prompt-skill-analysis)."
---

# Project Timeline — visual timeline + meta-analysis of a project's sessions

Build an interactive timeline of how a repo was actually built across its agent sessions, and turn it into a whole-project read plus optional per-session coaching. This is the **visual entry** to awow's session analysis. It reads **two sources**:
- **Claude Code logs** under `~/.claude/projects/` (`--project-path`) — zero setup, richest detail (file edits, per-turn context, handoffs).
- **An `mlflow_export/` dir** of Databricks traces (`--mlflow-export`) from the `mlflow-export` skill — supports **multiple users**, and is **split into one dashboard per project** (per working directory): the build emits an `index.html` landing page plus a `timeline-<slug>.html` per project. There is no cross-project aggregate.

The engine is `tools/session_timeline.py` (with `session_timeline_template.html` for the view and `tools/mlflow_reader.py` — the shared, schema-validated reader also used by `awow-usage-coach`). This skill is the judgment: scope, cost-gating, reading the picture, and coaching — the script never decides scope on its own.

When sessions span **more than one day**, each dashboard switches to a **calendar mode**: a day-navigator strip (empty gaps collapsed) above a per-day detail timeline — click a day or press ←/→ to page through. When a project has **more than one user**, each dashboard carries an in-UI **user** filter that re-scopes the whole view; you usually don't need `--user`.

Read [`.agents/skills/awow-usage-coach/SKILL.md`](../awow-usage-coach/SKILL.md) before coaching; it owns the intent taxonomy and the Mode B voice. Read [`guides/guide-session-timeline.html`](../../../guides/guide-session-timeline.html) if you need to explain what the view shows.

## Inputs

- The target repo path (default: the current repo root) **or** an `mlflow_export` directory.
- Optional: a transcripts dir of `<session-id>.txt` exports (Claude logs only — from the `session-export` skill), a `--tz-offset` for display, `--user <name>` to pre-scope an MLflow export to one person (the in-UI filter usually suffices), and whether to produce per-session coaching + an overview panel.

## What you do

1. **Confirm scope + source.** Resolve the repo path or the `mlflow_export` dir. Ask the user for their UTC offset if you do not already know it (logs/traces are UTC; the view must display local time). Do not assume. An MLflow export auto-splits per project, so you do not need to pick one project up front; mention the per-user in-UI filter rather than forcing a `--user` choice.
2. **Pick the coaching degree (gate the cost).** Before reading transcripts, tell the user the cost and let them choose: **(1) Timeline only** (~0 tokens) · **(2) Overview + lessons** · **(3) + per-session reviews** (scales with session count — and on MLflow data each review is necessarily thin, since only the first prompt, final response, and tool names survive per conversation).
3. **Build the timeline.** Run the tool and report the session count (and, for MLflow, the projects it split into):
   ```
   # Claude Code logs (one repo → one timeline.html):
   python tools/session_timeline.py --project-path <repo> --out <out-dir> --tz-offset <hours>
   # MLflow export (→ index.html + one timeline-<slug>.html per project; optionally pre-scope a user):
   python tools/session_timeline.py --mlflow-export <mlflow_export-dir> --out <out-dir> --tz-offset <hours> [--user <name>]
   ```
   Add `--transcripts <dir>` (Claude logs) to scope the view and link transcripts, and `--context-window <n>` if the team's window is not 200000. The build validates the emitted `sessions.json` schema and fails loud if the export format has drifted.
4. **Read the picture, then write the overview.** Read the `sessions.json` (or per-project `sessions-<slug>.json`), not the raw logs, for the aggregate shape: session count, peak parallel/day, idle gaps, per-session peak context (Claude logs only), functional-area / working-dir mix, per-user split, token cost. For a multi-day dataset, lead with the **cadence over the calendar** (quiet stretches vs. crunch days), not a single-evening rhythm. Draft a whole-project meta-analysis to `coach_reviews/<repo>-timeline/OVERVIEW.md` first; pass it as `--overview` once approved so it renders as the default panel. The overview is **private session-derived data** — write it to `coach_reviews/` (gitignored), never to `proposals/` or any tracked path; committing it to a public repo leaks customer data.
5. **Coach per session only if degree 3.** Follow `awow-usage-coach` Mode B per session and write one `<short-id>.md` into the gitignored `coach_reviews/` dir, then rebuild with `--coach-dir`. Reviews and the timeline outputs (`sessions.json`, `timeline.html`) are team session data — keep them out of `proposals/` and every tracked path. For deep prompt-craft scoring, defer to `prompt-skill-analysis`.
6. **Open it.** Tell the user the path to open: the `index.html` for a multi-project MLflow export (it links each project's dashboard), or `timeline.html` for a single project / Claude-logs run. Everything is self-contained (open by double-clicking).

## Rules

- Treat the idle gaps the tool reports (no event logged anywhere) as elapsed-not-active time; lead the overview with active time and the parallel-compression factor, not the raw span. Idle is only shown for Claude logs — MLflow traces lack the per-turn events to tell idle from active.
- Never embed secrets, keys, or private credentials a session pasted into a prompt into the overview or a coach review; flag them to the user out-of-band instead.
- Scope to an exported snapshot (`--transcripts`) when sessions are still being written, so the view stays stable while work continues.
