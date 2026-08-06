#!/usr/bin/env python3
"""Submit the checked-out eval suite to the night eval service, poll the run
to a terminal status, and write scores to the step summary. Stdlib only —
inputs arrive as EVAL_* env vars (see action.yml). Fail loud: any unexpected
API response raises and fails the step with the real error visible.

Gateway and network faults are the one exception, and they are retried rather
than swallowed. The control plane is a consumption-plan function that scales to
zero between 30-second polls, so an occasional 5xx from the gateway says
nothing about the run itself — a poll loop that dies on the first one throws
away an eval that has already been paid for. A retry that runs out still
raises, with the real error and the count of what was tolerated."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

POLL_SECONDS = 30
POLL_LIMIT = 120  # 60 minutes — cold starts have run 25-28 min; 30 was too thin a margin
TRANSIENT_STATUS = {500, 502, 503, 504}
RETRY_BACKOFF = (2, 5, 15)  # seconds before retry 1, 2, 3+
MAX_CONSECUTIVE_POLL_FAILURES = 5


class Transient(Exception):
    """A gateway or network fault, which says nothing about the run itself."""


def request(method: str, path: str, body: dict | None = None) -> dict:
    """One HTTP call. Raises Transient for gateway/network faults; anything
    the service itself said propagates unchanged."""
    req = urllib.request.Request(
        os.environ["EVAL_BASE_URL"] + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Ocp-Apim-Subscription-Key": os.environ["EVAL_API_KEY"],
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in TRANSIENT_STATUS:
            raise Transient(f"HTTP {e.code} {e.reason}") from e
        raise
    except urllib.error.URLError as e:
        raise Transient(f"network: {e.reason}") from e


def api(method: str, path: str, body: dict | None = None,
        attempts: int = 1) -> dict:
    """request() with backoff across `attempts` tries. attempts=1 is a single
    shot, which is what POST /runs needs: it is not idempotent, so retrying it
    risks creating a second run and billing the tenant for both."""
    for i in range(1, attempts + 1):
        try:
            return request(method, path, body)
        except Transient as e:
            if i == attempts:
                raise
            delay = RETRY_BACKOFF[min(i - 1, len(RETRY_BACKOFF) - 1)]
            print(f"transient on {method} {path}: {e} — "
                  f"retry {i}/{attempts - 1} in {delay}s", flush=True)
            time.sleep(delay)


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


def calib_str(calib) -> str:
    """Per-flow calibration map ({flow: hash}, AWO-72) rendered for messages."""
    return (", ".join(f"{f}={h}" for f, h in sorted(calib.items()))
            if isinstance(calib, dict) else repr(calib))


def gate_errors(resp: dict, cells: list[dict], gate: dict) -> list[str]:
    """Regression is a score below the baselined floor; indeterminate is
    no-data and trips its own cap, never a fail. An unqualified or drifted
    calibration refuses to gate at all (spec §8/§9). Calibration compares as
    a whole per-flow map: any rubric edit or flow addition re-baselines."""
    run_calib = (resp.get("judge") or {}).get("calibration")
    if not gate.get("sabotage_pass"):
        return ["gate.json has no sabotage_pass — the judge is unqualified; "
                "refusing to gate"]
    if run_calib != gate["calibration"]:
        return [f"run calibration {calib_str(run_calib)} != gate "
                f"{calib_str(gate['calibration'])} — re-baseline before gating"]
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
        else:
            errs.append(f"{scen}: 0 judged cells in this run — every "
                        "baselined scenario must produce data to gate")
    return errs


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    scenarios = sorted(p.name for p in Path("evals/scenarios").iterdir()
                       if p.is_dir())
    reps = int(os.environ["EVAL_REPS"])
    budget = int(os.environ["EVAL_BUDGET_PER_SCENARIO"]) * len(scenarios) * reps

    try:
        run = api("POST", "/runs", {
            "model": os.environ["EVAL_MODEL"],
            "scenarios": scenarios,
            "data_source": {"sha": sha},
            "reps": reps,
            "budget_tokens_total": budget,
        })
    except Transient as e:
        # Deliberately not retried: the gateway can fail after the backend has
        # already committed the run, so a retry risks a second billed run.
        print(f"::error::submission failed on a transient fault ({e}). The run "
              f"may still have been created for {sha} — check before "
              "resubmitting, or it becomes an orphan nobody collects")
        raise

    run_id = run["id"]
    summary(f"submitted `{run_id}` for `{sha}` "
            f"({len(scenarios)} scenario(s), {reps} rep(s))")

    consecutive = 0
    for attempt in range(1, POLL_LIMIT + 1):
        try:
            record = api("GET", f"/runs/{run_id}")
        except Transient as e:
            consecutive += 1
            print(f"[{attempt}] transient: {e} "
                  f"({consecutive}/{MAX_CONSECUTIVE_POLL_FAILURES})",
                  flush=True)
            if consecutive >= MAX_CONSECUTIVE_POLL_FAILURES:
                print(f"::error::eval service unreachable for {consecutive} "
                      f"consecutive polls; run `{run_id}` may still be running")
                raise
            time.sleep(POLL_SECONDS)
            continue
        consecutive = 0
        status = record["status"]
        print(f"[{attempt}] {status}", flush=True)

        if status == "completed":
            # Idempotent, and the eval is already paid for by this point —
            # losing the scores to one blip here would be the worst trade.
            resp = api("GET", f"/runs/{run_id}/output-items",
                       attempts=len(RETRY_BACKOFF) + 1)
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
                        f"`{calib_str(json.loads(gate_path.read_text())['calibration'])}`")
            return 0

        if status == "failed":
            summary("### Eval run failed",
                    "```json", json.dumps(record, indent=2), "```")
            print("::error::eval run failed — see summary")
            return 1

        time.sleep(POLL_SECONDS)

    print(f"::error::run not terminal after {POLL_LIMIT * POLL_SECONDS // 60} "
          "minutes — the request record is durable; the next submission "
          "drains it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
