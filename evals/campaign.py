#!/usr/bin/env python3
"""Run and combine the fixed local awow model campaign. Stdlib only."""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SEATS_PATH = ROOT / "evals" / "model-seats.json"
RUBRICS = ROOT / "evals" / "rubrics"
RUNNER_PATH = ROOT / ".github" / "actions" / "eval-run" / "run.py"
PROFILES = {
    "establishment": {"scenarios": ["setup-awow-walkthrough"], "reps": 10},
    "snapshot": {"scenarios": ["setup-awow-walkthrough"], "reps": 5},
}
HARNESS_IDS = {"Codex": "codex", "Claude Code": "claude-code", "Pi": "pi"}


def load_seats(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if data.get("schema") != 1 or not data.get("eval_version"):
        raise ValueError(f"{path}: unsupported model-seat contract")
    seats = data.get("seats")
    if not isinstance(seats, list) or not seats:
        raise ValueError(f"{path}: seats must be a non-empty list")
    required = {"id", "name", "model", "effort", "harness", "manual",
                "weekly", "baseline_eligible"}
    for seat in seats:
        missing = required - seat.keys()
        if missing or seat.get("harness") not in HARNESS_IDS:
            raise ValueError(f"{path}: malformed seat {seat!r}; missing={sorted(missing)}")
        if any(key in seat for key in ("endpoint", "base_url", "provider_url")):
            raise ValueError(f"{path}: serving endpoints do not belong in model seats")
    ids = [seat["id"] for seat in seats]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate seat ID")
    return seats


def _load_runner():
    spec = importlib.util.spec_from_file_location("eval_run_for_campaign", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer at {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _subject_sha(subject_root: Path) -> str:
    status = subprocess.run(
        ["git", "-C", str(subject_root), "status", "--porcelain"],
        check=True, capture_output=True, text=True).stdout
    if status.strip():
        raise RuntimeError("subject checkout is dirty; commit or move changes before a campaign")
    return subprocess.run(
        ["git", "-C", str(subject_root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()


def _metrics(cells: list[dict]) -> dict:
    processes = [cell.get("process") or {} for cell in cells]
    tokens = [p["tokens"] for p in processes if isinstance(p.get("tokens"), (int, float))]
    costs = [p["cost_usd"] for p in processes
             if isinstance(p.get("cost_usd"), (int, float))]
    return {
        "tokens": sum(tokens) if tokens else None,
        "cost_usd": round(sum(costs), 8) if costs else None,
        "wall_s": round(sum(p.get("wall_s", 0) for p in processes), 1),
    }


def _resolution(args, seat_id: str) -> str:
    resolved = args.model_resolution.get(seat_id)
    if not isinstance(resolved, str) or not resolved.strip():
        raise ValueError(f"model resolution missing for {seat_id}")
    return resolved


def validate_model_resolution(seats: list[dict], resolution: dict) -> dict:
    if not isinstance(resolution, dict):
        raise ValueError("model resolution must be a seat-ID-to-model-ID object")
    missing = [seat["id"] for seat in seats
               if not isinstance(resolution.get(seat["id"]), str)
               or not resolution[seat["id"]].strip()]
    if missing:
        raise ValueError("model resolution missing: " + ", ".join(missing))
    return resolution


def _evaluator_python() -> str:
    executable = shutil.which("python3.12")
    if executable is None:
        raise RuntimeError("the overnight evaluator requires python3.12")
    return executable


def run_seat(seat: dict, args) -> Path:
    """Generate existing bundles, invoke the existing evaluator, compact once."""
    seat_dir = args.out / seat["id"]
    compact_path = seat_dir / "eval-result.json"
    if compact_path.is_file():
        existing = json.loads(compact_path.read_text())
        expected_runs = len(args.scenarios) * args.reps
        compatible = (existing.get("subject_sha") == args.subject_sha
                      and existing.get("eval_version") == args.eval_version
                      and existing.get("seat", {}).get("id") == seat["id"]
                      and existing.get("coverage", {}).get(
                          "requested_repetitions") == expected_runs)
        if not compatible:
            raise RuntimeError(f"{compact_path}: existing result is for another campaign")
        return compact_path  # a terminal low score is data, never a retry reason
    seat_dir.mkdir(parents=True, exist_ok=True)
    request_path = seat_dir / "request.yaml"
    scenarios = ", ".join(args.scenarios)
    request_path.write_text(
        "contract: eval/v1\n"
        "suite: evals\n"
        f"scenarios: [{scenarios}]\n"
        "tiers: [bulk]\n"
        f"reps: {args.reps}\n"
        f"budget_tokens_total: {400000 * len(args.scenarios) * args.reps}\n")

    bundles = seat_dir / "bundles"
    local_result = seat_dir / "run" / "result.json"
    if not local_result.is_file():
        python = _evaluator_python()
        subprocess.run([
            python, str(args.evaluator_root / "make_eval_bundles.py"),
            str(request_path), "--sha", args.subject_sha, "--repo", "CauchyIO/awow",
            "--out", str(bundles), "--root", str(seat_dir / "box"),
            "--clone", str(args.subject_root),
        ], check=True)
        entry = {"seat": HARNESS_IDS[seat["harness"]], "model": seat["model"]}
        if seat["harness"] in ("Codex", "Claude Code"):
            entry["effort"] = seat["effort"]
        seatmap = seat_dir / "seatmap.json"
        seatmap.write_text(json.dumps({"bulk": entry}, indent=1) + "\n")
        subprocess.run([
            python, str(args.evaluator_root / "eval_run_local.py"),
            str(bundles), "--suite-root", str(args.subject_root),
            "--out", str(seat_dir / "run"), "--seatmap", str(seatmap),
        ], check=True)

    local = json.loads(local_result.read_text())
    if local.get("request_sha") not in (None, args.subject_sha):
        raise RuntimeError(f"{local_result}: result is for another subject")
    cells = local.get("cells") or []
    resolved_model_id = _resolution(args, seat["id"])
    reported = {cell.get("process", {}).get("resolved_model_id") for cell in cells}
    reported.discard(None)
    if reported and reported != {resolved_model_id}:
        raise RuntimeError(
            f"{seat['id']}: evaluator reported {sorted(reported)}, "
            f"expected {resolved_model_id!r}")
    scored = _load_runner().score_run(cells, RUBRICS, args.reps)
    identity = {"id": seat["id"], "name": seat["name"],
                "model_id": resolved_model_id, "harness": seat["harness"],
                "effort": seat["effort"]}
    compact = {
        "contract": "awow.eval-scorecard/v1",
        "subject_sha": args.subject_sha,
        "eval_version": args.eval_version,
        "seat": identity,
        "requested_model": seat["model"],
        "coverage": scored["coverage"],
        "capabilities": scored["capabilities"],
        "metrics": _metrics(cells),
    }
    compact_path.write_text(json.dumps(compact, indent=1) + "\n")
    return compact_path


def merge_campaign(paths: list[Path]) -> dict:
    if not paths:
        raise ValueError("campaign has no results")
    runs = [json.loads(path.read_text()) for path in paths]
    if any(run.get("contract") != "awow.eval-scorecard/v1" for run in runs):
        raise ValueError("campaign input has an unknown contract")
    subjects = {run.get("subject_sha") for run in runs}
    versions = {run.get("eval_version") for run in runs}
    ids = [run.get("seat", {}).get("id") for run in runs]
    if len(subjects) != 1 or len(versions) != 1:
        raise ValueError("campaign inputs mix subject SHA or eval version")
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError("campaign inputs have a missing or duplicate seat ID")
    order = {seat["id"]: index for index, seat in enumerate(load_seats(SEATS_PATH))}
    runs.sort(key=lambda run: order.get(run["seat"]["id"], len(order)))
    return {"contract": "awow.eval-campaign/v1",
            "subject_sha": subjects.pop(), "eval_version": versions.pop(),
            "runs": runs}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--evaluator-root", required=True, type=Path)
    run.add_argument("--model-resolution", required=True, type=Path)
    run.add_argument("--profile", choices=sorted(PROFILES), required=True)
    run.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    profile = PROFILES[args.profile]
    args.subject_root = ROOT
    args.subject_sha = _subject_sha(ROOT)
    args.scenarios = profile["scenarios"]
    args.reps = profile["reps"]
    args.model_resolution = json.loads(args.model_resolution.read_text())
    config = json.loads(SEATS_PATH.read_text())
    args.eval_version = config["eval_version"]
    seats = [seat for seat in load_seats(SEATS_PATH) if seat["manual"]]
    validate_model_resolution(seats, args.model_resolution)
    paths = [run_seat(seat, args) for seat in seats]
    merged = merge_campaign(paths)
    merged.update({"profile": args.profile,
                   "run_date": dt.datetime.now(dt.timezone.utc).date().isoformat()})
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out / "campaign.json"
    output.write_text(json.dumps(merged, indent=1) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
