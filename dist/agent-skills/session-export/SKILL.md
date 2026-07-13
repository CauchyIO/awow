---
name: session-export
description: "Export a project's Claude Code sessions into a readable transcript dump (the input the project-timeline skill needs). Walks the user through choosing the project, scoping which sessions to include (date window, excluding meta/plugin runs), and warns about secrets before writing. Use when the user wants to export, dump, collect, or back up their Claude Code sessions for a project so they can be analysed or coached. Produces <out>/<session-id>.txt transcripts + INDEX.md + manifest.json. Reads ~/.claude/projects/<encoded-path>/*.jsonl."
---

# Session Export

Turns the per-session JSONL logs Claude Code keeps under
`~/.claude/projects/<encoded-path>/` into a human-readable transcript dump: one
`<session-id>.txt` per session (a readable USER/ASSISTANT transcript),
plus `INDEX.md` and `manifest.json`. That dump is the input `project-timeline`
reads to produce a timeline + coaching report.

The judgment in this skill is the *guidance* — helping the user scope a sensible
dump and not leak secrets. The script (`scripts/export_sessions.py`, stdlib only)
does the discovery, rendering, and secret scanning; it never decides scope on its
own.

`<skill-dir>` below is this skill's base directory, announced when the skill loads.

Run everything from the repo root. The script lives at
`<skill-dir>/scripts/export_sessions.py`.

> **This skill is Claude-Code-only.** It reads local `~/.claude/projects` logs. If
> the user instead has an **MLflow trace export** (from awow's `mlflow-export`
> skill — a Databricks experiment dumped to `traces.jsonl`), they don't need this
> skill: `project-timeline` consumes that `mlflow_export` directory directly. Use
> this skill only to turn local Claude Code sessions into a transcript dump.

## Walk the user through it

Do **not** dump everything blindly. Go step by step:

### 1. Find the project
If the user named a project path, use it. Otherwise list what's available:

```bash
python3 <skill-dir>/scripts/export_sessions.py list-projects
```

This prints each project's session directory, session count, and date range.
Confirm the real project path with the user (the `~path` shown is a lossy guess —
prefer the actual repo path they give you). You'll pass it as `--project-path`.

### 2. Show the session menu and scope it
```bash
python3 <skill-dir>/scripts/export_sessions.py list-sessions \
    --project-path <path> [--since YYYY-MM-DD] [--until YYYY-MM-DD]
```

This lists every in-scope session with its short id, start time, prompt count,
size, and title, then a **total token-read estimate**. Use it to help the user
decide scope. Good scoping questions:

- **Time window** — one build session? a week? Use `--since` / `--until`.
- **Exclude meta/plugin noise** — sessions that were tooling experiments rather
  than real project work (the example excluded `/awow:` plugin-testing runs).
  Use `--exclude <substr>` (matches the title) or `--exclude ~<substr>` (matches
  the transcript body), repeatable. The retrospective can later move these to a
  `coach_reviews/excluded/` subfolder.
- **Size awareness** — read out the total estimate. A large dump means a costly
  full-coaching pass later; mention it now so the user isn't surprised.

If the menu is large, summarize it for the user rather than pasting all rows.

### 3. Warn about secrets, then export
Transcripts capture *everything* typed and every tool result — including any API
keys, tokens, or passwords that appeared in the session. **Tell the user this
before writing**, and that the dump should be treated as secret-bearing (the
`transcripts/` dir is gitignored for that reason).

Export with the scanner on. Default to `--redact` unless the user wants to review
the raw secrets first:

```bash
python3 <skill-dir>/scripts/export_sessions.py export \
    --project-path <path> \
    --out transcripts/<project-slug> \
    [--since …] [--until …] [--exclude …] \
    --redact
```

- Without `--redact`, the script **warns** and lists any detected secrets so the
  user can decide. Re-run with `--redact` to replace them with
  `«REDACTED-SECRET»`.
- The scanner catches known key shapes (AWS, OpenAI/Anthropic `sk-…`, Slack,
  Google, GitHub, `KEY=value` assignments, PEM blocks). It is not exhaustive —
  if the user knows a real secret was pasted, have them **rotate it** regardless.

To re-check or scrub an existing dump without re-exporting:

```bash
python3 <skill-dir>/scripts/export_sessions.py scan transcripts/<slug> [--redact]
```

## Output

```
transcripts/<project-slug>/
├── <session-id>.txt     # one readable transcript per session
├── INDEX.md             # dated list linking every transcript
└── manifest.json        # project_path, session list, sizes, est_read_tokens
```

`manifest.json` is what lets `project-timeline` run without re-asking for
the project path or re-estimating cost — keep it with the dump.

## After exporting

Tell the user, in 2-3 lines:
- where the dump landed and how many sessions / how much it is,
- whether any secrets were flagged or redacted (and to rotate real ones),
- that the next step is `project-timeline` on `transcripts/<project-slug>`.

## Troubleshooting

- **`list-projects` shows nothing** — the user hasn't run Claude Code from inside
  that project, or `~/.claude/projects` is elsewhere. Confirm the path.
- **Session dir not found** — the encoded name must match exactly; use
  `--project-dir <name>` with a dir from `list-projects` if `--project-path`
  doesn't resolve.
- **Wrong sessions included** — tighten `--since`/`--until` or add `--exclude`
  terms; re-run `list-sessions` to preview before exporting.
- **Transcript looks truncated** — extended-thinking blocks are intentionally
  dropped from the readable dump; tool calls and results are kept in full.
