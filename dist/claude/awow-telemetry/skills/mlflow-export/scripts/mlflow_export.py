"""Export all traces + grouped chat sessions for a Databricks MLflow experiment.

Usage:
    python mlflow_export.py --experiment-id <id> [--profile <name>] [--out <dir>]

Or pass an MLflow chat-sessions URL and the script extracts the experiment id:
    python mlflow_export.py --url 'https://adb-XYZ.azuredatabricks.net/ml/experiments/<id>/...' \\
                            --profile <name>

Writes into <out>/ (default: ./mlflow_export):
  - traces.jsonl              one JSON per trace (info + request/response + spans)
  - sessions/<sid>.json       one file per chat session, traces sorted chronologically
  - manifest.json             counts, time ranges, per-session index

Requires: mlflow>=3.0, databricks-sdk. Install with:
    uv pip install 'mlflow[databricks]>=3.0' databricks-sdk
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--experiment-id", help="MLflow experiment id (numeric).")
    p.add_argument("--url", help="Databricks MLflow experiment URL — id will be extracted.")
    p.add_argument("--profile", default=os.environ.get("DATABRICKS_CONFIG_PROFILE", "DEFAULT"),
                   help="Databricks CLI profile (default: DEFAULT or $DATABRICKS_CONFIG_PROFILE).")
    p.add_argument("--out", default="mlflow_export", help="Output directory (default: ./mlflow_export).")
    p.add_argument("--page-size", type=int, default=100, help="Traces per page (default: 100).")
    args = p.parse_args()

    if args.url and not args.experiment_id:
        m = re.search(r"/experiments/(\d+)", args.url)
        if not m:
            p.error("could not extract experiment id from --url")
        args.experiment_id = m.group(1)
    if not args.experiment_id:
        p.error("provide --experiment-id or --url")
    return args


def trace_to_dict(t) -> dict:
    info = t.info
    data = t.data
    spans = []
    for s in data.spans:
        try:
            spans.append(json.loads(s.to_json()))
        except Exception as e:
            spans.append({
                "span_id": getattr(s, "span_id", None),
                "name": getattr(s, "name", None),
                "_serialize_error": repr(e),
            })

    rt = getattr(info, "request_time", None)
    if isinstance(rt, datetime):
        rt = rt.astimezone(timezone.utc).isoformat()

    return {
        "info": {
            "trace_id": info.trace_id,
            "client_request_id": getattr(info, "client_request_id", None),
            "experiment_id": getattr(info, "experiment_id", None),
            "request_time": rt,
            "execution_duration": getattr(info, "execution_duration", None),
            "state": str(getattr(info, "state", None)),
            "tags": dict(getattr(info, "tags", {}) or {}),
            "trace_metadata": dict(getattr(info, "trace_metadata", {}) or {}),
        },
        "request": data.request,
        "response": data.response,
        "spans": spans,
    }


def fmt_time(t) -> str:
    if t is None:
        return "-"
    if isinstance(t, int):
        return datetime.fromtimestamp(t / 1000, tz=timezone.utc).isoformat()
    return str(t)


def main() -> int:
    args = parse_args()
    os.environ["DATABRICKS_CONFIG_PROFILE"] = args.profile
    mlflow.set_tracking_uri(f"databricks://{args.profile}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sessions").mkdir(exist_ok=True)

    client = MlflowClient()
    print(f"Profile: {args.profile}", flush=True)
    print(f"Experiment: {args.experiment_id}", flush=True)
    print(f"Output: {out.resolve()}", flush=True)

    traces_path = out / "traces.jsonl"
    by_session: dict[str, list[dict]] = defaultdict(list)
    total = 0
    page_token = None
    page = 0

    with traces_path.open("w") as fh:
        while True:
            page += 1
            results = client.search_traces(
                experiment_ids=[args.experiment_id],
                max_results=args.page_size,
                page_token=page_token,
            )
            print(f"  page {page}: {len(results)} traces", flush=True)
            for t in results:
                d = trace_to_dict(t)
                fh.write(json.dumps(d, default=str) + "\n")
                sid = d["info"]["trace_metadata"].get("mlflow.trace.session") or "no-session"
                by_session[sid].append(d)
                total += 1
            page_token = getattr(results, "token", None)
            if not page_token:
                break

    manifest = {
        "experiment_id": args.experiment_id,
        "profile": args.profile,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_traces": total,
        "total_sessions": len(by_session),
        "sessions": [],
    }
    for sid, traces in by_session.items():
        traces_sorted = sorted(traces, key=lambda x: fmt_time(x["info"].get("request_time")))
        first = traces_sorted[0]["info"].get("request_time")
        last = traces_sorted[-1]["info"].get("request_time")
        users = sorted({tr["info"]["trace_metadata"].get("mlflow.user", "") for tr in traces_sorted})
        wd = sorted({tr["info"]["trace_metadata"].get("mlflow.trace.working_directory", "") for tr in traces_sorted})
        sess_path = out / "sessions" / f"{sid}.json"
        with sess_path.open("w") as fh:
            json.dump(
                {
                    "session_id": sid,
                    "trace_count": len(traces_sorted),
                    "first_request_time": first,
                    "last_request_time": last,
                    "users": users,
                    "working_directories": wd,
                    "traces": traces_sorted,
                },
                fh,
                default=str,
            )
        manifest["sessions"].append(
            {
                "session_id": sid,
                "trace_count": len(traces_sorted),
                "first_request_time": first,
                "last_request_time": last,
                "users": users,
                "working_directories": wd,
                "file": str(sess_path),
            }
        )

    manifest["sessions"].sort(key=lambda s: fmt_time(s.get("first_request_time")))
    with (out / "manifest.json").open("w") as fh:
        json.dump(manifest, fh, indent=2, default=str)

    print(f"Done. {total} traces across {len(by_session)} sessions.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
