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


def md_cell(text: str) -> str:
    """One markdown table cell: no pipes, no newlines."""
    return text.replace("|", "\\|").replace("\n", " ")


def verdict_note(c: dict) -> str:
    v = c.get("verdict")
    if v in (None, "pass"):
        return ""
    stage = f" ({c['stage']})" if c.get("stage") else ""
    return f" — **{v}**{stage}"


def render_scores(record: dict, cells: list[dict]) -> list[str]:
    lines = ["### Eval scores", *(
        f"- `{c['id']}`: **{c['outcome']['rubric_yes']}"
        f"/{c['outcome']['rubric_total']}**{verdict_note(c)} "
        f"(stop: {c['process']['stop_reason']}; "
        f"scope violations: {len(c['process']['scope_violations'])})"
        for c in cells)]

    branch = record["metadata"]["result_branch"]
    repo = record["data_source"]["repo"]
    lines += ["", f"Transcripts + judge output: [`{branch}`]"
              f"(https://github.com/{repo}/tree/{branch})" if branch else
              "Transcripts: result branch missing from the run record"]

    for c in cells:
        lines += ["", "<details><summary><code>"
                  f"{c['id']}</code> — {c['outcome']['rubric_yes']}"
                  f"/{c['outcome']['rubric_total']}</summary>", "",
                  "| rubric question | answer | judge's evidence |",
                  "|---|---|---|", *(
                  f"| {md_cell(a['question'])} "
                  f"| {'yes' if a['answer'] else '**no**'} "
                  f"| {md_cell(a['evidence'])} |"
                  for a in c["outcome"]["rubric"])]
        post = (c.get("checks") or {}).get("post")
        if post and post.get("rc") not in (0, None):
            lines += ["", f"Deterministic witness (rc={post['rc']}):", "",
                      *(f"> {md_cell(l)}" for l in post["log"].splitlines() if l)]
        lines += ["", "</details>"]
    return lines


def gate_errors(resp: dict, cells: list[dict], gate: dict) -> list[str]:
    """Regression is a score below the baselined floor; indeterminate is
    no-data and trips its own cap, never a fail. An unqualified or drifted
    calibration refuses to gate at all (spec §8/§9)."""
    run_calib = (resp.get("judge") or {}).get("calibration")
    if not gate.get("sabotage_pass"):
        return ["gate.json has no sabotage_pass — the judge is unqualified; "
                "refusing to gate"]
    if run_calib != gate["calibration"]:
        return [f"run calibration {run_calib!r} != gate {gate['calibration']!r}"
                " — re-baseline before gating"]
    per, indeterminate = {}, 0
    for c in cells:
        scen = c["id"].removeprefix("eval-").rsplit("-", 2)[0]
        if c.get("verdict") == "indeterminate":
            indeterminate += 1
        else:
            per.setdefault(scen, []).append(c["outcome"]["rubric_yes"])
    errs = []
    if indeterminate > gate["max_indeterminate"]:
        errs.append(f"{indeterminate} indeterminate cell(s) > cap "
                    f"{gate['max_indeterminate']} — no-data, not regression")
    for scen, g in gate["scenarios"].items():
        scores = per.get(scen)
        if scores:
            mean = sum(scores) / len(scores)
            if mean < g["min_mean"]:
                errs.append(f"{scen}: mean {mean:.2f} < gate {g['min_mean']}")
    return errs


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
        record = api("GET", f"/runs/{run_id}")
        status = record["status"]
        print(f"[{attempt}] {status}", flush=True)

        if status == "completed":
            resp = api("GET", f"/runs/{run_id}/output-items")
            cells = [item["cell"] for item in resp["data"]]
            summary(*render_scores(record, cells))
            gate_path = Path("evals/gate.json")
            if gate_path.is_file():
                errs = gate_errors(resp, cells, json.loads(gate_path.read_text()))
                if errs:
                    summary("### Gate", *(f"- {e}" for e in errs))
                    print("::error::eval gate failed — see summary")
                    return 1
                summary("", "Gate: **clean** vs baseline "
                        f"`{json.loads(gate_path.read_text())['calibration']}`")
            return 0

        if status == "failed":
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
