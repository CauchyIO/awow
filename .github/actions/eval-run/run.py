#!/usr/bin/env python3
"""Submit the checked-out eval suite to the night eval service, poll the run
to a terminal status, and write scores to the step summary. Stdlib only —
inputs arrive as EVAL_* env vars (see action.yml). Fail loud: any unexpected
API response raises and fails the step with the real error visible."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

POLL_SECONDS = 30
POLL_LIMIT = 60  # 30 minutes


def api(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        os.environ["EVAL_BASE_URL"] + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Ocp-Apim-Subscription-Key": os.environ["EVAL_API_KEY"],
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def summary(*lines: str) -> None:
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    scenarios = sorted(p.name for p in Path("evals/scenarios").iterdir()
                       if p.is_dir())
    reps = int(os.environ["EVAL_REPS"])
    budget = int(os.environ["EVAL_BUDGET_PER_SCENARIO"]) * len(scenarios) * reps

    run = api("POST", "/runs", {
        "model": os.environ["EVAL_MODEL"],
        "scenarios": scenarios,
        "data_source": {"sha": sha},
        "reps": reps,
        "budget_tokens_total": budget,
    })
    run_id = run["id"]
    summary(f"submitted `{run_id}` for `{sha}` "
            f"({len(scenarios)} scenario(s), {reps} rep(s))")

    for attempt in range(1, POLL_LIMIT + 1):
        status = api("GET", f"/runs/{run_id}")["status"]
        print(f"[{attempt}] {status}", flush=True)

        if status == "completed":
            items = api("GET", f"/runs/{run_id}/output-items")["data"]
            summary("### Eval scores", *(
                f"- `{c['id']}`: **{c['outcome']['rubric_yes']}"
                f"/{c['outcome']['rubric_total']}** "
                f"(stop: {c['process']['stop_reason']}; "
                f"scope violations: {len(c['process']['scope_violations'])})"
                for c in (item["cell"] for item in items)))
            return 0

        if status == "failed":
            record = api("GET", f"/runs/{run_id}")
            summary("### Eval run failed",
                    "```json", json.dumps(record, indent=2), "```")
            print("::error::eval run failed — see summary")
            return 1

        time.sleep(POLL_SECONDS)

    print("::error::run not terminal after 30 minutes — the request record "
          "is durable; the next submission drains it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
