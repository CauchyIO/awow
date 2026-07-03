---
name: mlflow-export
description: "Export all traces and grouped chat sessions from a Databricks MLflow experiment to local JSON files. This skill should be used when the user asks to export, dump, download, or back up MLflow traces, sessions, or chat-sessions from a Databricks experiment (often given as an MLflow experiment URL or numeric experiment id)."
---

# MLflow Experiment Export

> **One example backend.** This skill ships as a starter for teams whose agent sessions land in **Databricks MLflow**. Teams on a different tracing backend (LangSmith, Helicone, OpenTelemetry, raw session JSONL on disk, etc.) should swap this skill for their backend's equivalent during `/setup-awow` Step 8 (Skills review). The downstream skills (`prompt-skill-analysis`, `awow-usage-coach`) consume the JSON layout this skill produces, so any replacement should match the output shape documented below.

Exports every trace in a Databricks MLflow experiment, including full spans, plus a per-session view that groups traces by their `mlflow.trace.session` metadata (this is what powers the "Chat sessions" tab in the Databricks MLflow UI).

> **The export is private session data — never commit it.** Traces contain verbatim prompts, real names, private issue IDs, infra details, and secrets users pasted. The default output dir `mlflow_export/` is gitignored; keep it that way. Do not move the export, or any report derived from it, into a tracked path (`proposals/`, `context/`, …) — if the repo is public, that leaks customer data.

## Inputs to collect from the user

- **Experiment id** — required. Either a numeric id (e.g. `1727480765814570`) or an MLflow URL like `https://adb-XYZ.azuredatabricks.net/ml/experiments/<id>/...`. The script extracts the id from a URL automatically.
- **Databricks profile** — the CLI profile authenticated against the target workspace. If unsure, run `databricks auth profiles` and pick one whose host matches the workspace in the URL. Default is `DEFAULT`.
- **Output directory** — optional, defaults to `./mlflow_export`.

If any are missing and not obvious from context, ask the user before running.

## Prerequisites

1. The user is authenticated with `databricks auth login --profile <name>` for the workspace that owns the experiment.
2. Python 3.10+ available, ideally a `.venv` in the working directory. If not present, create one with `uv venv` (or use the system Python).
3. Install dependencies into that environment:
   ```bash
   uv pip install 'mlflow[databricks]>=3.0' databricks-sdk
   ```
   (Use `pip install` instead if `uv` is not available.)

## Run the export

The script lives next to this skill at `scripts/mlflow_export.py`. Invoke it with the chosen Python interpreter:

```bash
.venv/bin/python .agents/skills/mlflow-export/scripts/mlflow_export.py \
    --experiment-id <ID> \
    --profile <PROFILE> \
    --out ./mlflow_export
```

Or with a URL:

```bash
.venv/bin/python .agents/skills/mlflow-export/scripts/mlflow_export.py \
    --url 'https://adb-XYZ.azuredatabricks.net/ml/experiments/<ID>/chat-sessions?...' \
    --profile <PROFILE>
```

The script paginates `MlflowClient.search_traces` (page size 100), so very large experiments may take a few minutes. Connection-pool warnings from urllib3 during span fetches are benign and can be ignored.

## Output layout

```
<out>/
├── traces.jsonl              # one JSON per trace (info + request + response + spans)
├── sessions/
│   └── <session-id>.json     # one file per session with traces sorted chronologically
└── manifest.json             # summary: counts, time range, per-session index
```

Each trace JSON contains:
- `info` — trace_id, request_time, execution_duration, state, tags, trace_metadata
- `request`, `response` — full (untruncated) prompt and response
- `spans` — full span tree for that trace

## After running

Print a brief summary using `manifest.json`:
- total trace and session counts
- date range covered
- first/last few sessions with their working directory and trace count

If the user wants a different shape (CSV, per-user grouping, only specific date ranges, etc.), adapt the script — it is short and self-contained.

## Troubleshooting

- **`Invalid run id` or `No API found`** — you hit the wrong REST endpoint. Use the bundled script (which calls the MLflow Python client), not raw `databricks api ...` calls.
- **Auth errors** — run `databricks --profile <name> current-user me` to verify the profile works against the right workspace.
- **Empty result** — confirm the experiment id is correct via `databricks --profile <name> experiments get-experiment <id>`.
