---
phase: spread
prerequisites:
  - "The project has been worked in Claude Code (sessions exist under ~/.claude/projects/<encoded-path>/)"
removes_pain: "the I-can't-see-how-this-project-actually-got-built problem"
consumes: claude-code-session-logs
when-to-use: "You want a visual, whole-project read of how a repo was built across many Claude Code sessions — the fan-out/contract rhythm, handoffs, idle time, context load, and per-session coaching — with no tracing stack required."
when-not-to-use: "You need board-linked trace analysis or cross-team prose reports — use mlflow-export + awow-usage-coach / the digests instead. Copilot-only projects have no local session log to read."
---

# /project-retrospective — visual timeline + meta-analysis of a project's sessions

Build an interactive timeline of how a repo was actually built across its Claude Code sessions, and turn it into a whole-project read plus optional per-session coaching. This is the **visual, zero-setup entry** to awow's session analysis: it reads the raw Claude Code logs under `~/.claude/projects/`, so it needs no MLflow/Databricks tracing wired up (that path is `mlflow-export` → `awow-usage-coach`). Claude Code only — Copilot keeps no equivalent local log.

Read [`.agents/skills/awow-usage-coach/SKILL.md`](../skills/awow-usage-coach/SKILL.md) before coaching; it owns the intent taxonomy and the Mode B voice. Read [`guides/guide-session-timeline.html`](../../guides/guide-session-timeline.html) if you need to explain what the view shows.

## Inputs

- The target repo path (default: the current repo root).
- Optional: a transcripts dir of `<session-id>.txt` exports, a `--tz-offset` for display, and whether to produce per-session coaching + an overview panel.

## What you do

1. **Confirm scope.** Resolve the repo path and ask the user for their UTC offset if you do not already know it (the logs are UTC; the view must display local time). Do not assume.
2. **Build the timeline.** Run the tool and report the session count:
   ```
   python tools/session_timeline.py --project-path <repo> --out <out-dir> --tz-offset <hours>
   ```
   Add `--transcripts <dir>` to scope the view to an exported snapshot and link transcripts, and `--context-window <n>` if the team's window is not 200000.
3. **Read the picture, then write the overview.** Read `sessions.json` (not the raw logs) for the aggregate shape: session count, concurrency peak, idle gaps, per-session peak context, functional-area mix. Draft a whole-project meta-analysis to `coach_reviews/<repo>-retrospective.md` first; pass it to the tool as `--overview` once approved so it renders as the default panel. The overview is **private session-derived data** — write it to `coach_reviews/` (gitignored), never to `proposals/` or any tracked path; committing it to a public repo leaks customer data.
4. **Coach per session only if asked.** When the user wants per-session reviews, follow `awow-usage-coach` Mode B per transcript and write one `<short-id>.md` per session into the gitignored `coach_reviews/` dir, then rebuild with `--coach-dir`. Reviews and the timeline outputs (`sessions.json`, `timeline.html`) are team session data — keep them out of `proposals/` and every tracked path.
5. **Open it.** Tell the user the path to `timeline.html`; it is self-contained (open by double-clicking).

## Rules

- Treat the idle gaps the tool reports (no event logged anywhere) as elapsed-not-active time; lead the overview with active time and the parallel-compression factor, not the raw span.
- Never embed secrets, keys, or private credentials a session pasted into a prompt into the overview or a coach review; flag them to the user out-of-band instead.
- Scope to an exported snapshot (`--transcripts`) when sessions are still being written, so the view stays stable while work continues.
