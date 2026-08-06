#!/usr/bin/env python3
"""Derive the small, model-pinned capability baseline from saved eval output."""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path


EVALS_DIR = Path(__file__).resolve().parent
RUBRIC_DIR = EVALS_DIR / "rubrics"
SCENARIO_DIR = EVALS_DIR / "scenarios"
RUNNER_PATH = EVALS_DIR.parent / ".github" / "actions" / "eval-run" / "run.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("eval_run_for_gate", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load eval runner at {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_baseline(resp: dict, seat: dict, eval_version: str,
                    requested_reps: int) -> dict:
    """Pure baseline derivation; identity and repetition completeness are pinned."""
    if requested_reps < 1:
        raise ValueError("requested repetitions must be positive")
    cells = [item["cell"] for item in resp.get("data", [])]
    scored = _load_runner().score_run(cells, RUBRIC_DIR, requested_reps)
    expected = {p.name for p in SCENARIO_DIR.iterdir() if p.is_dir()}
    missing = sorted(expected - scored["scenarios"].keys())
    if missing:
        raise ValueError(f"no judged cells for {', '.join(missing)}")
    incomplete = [
        f"{name} ({result['valid_runs']}/{requested_reps})"
        for name, result in scored["scenarios"].items()
        if result["valid_runs"] != requested_reps
    ]
    if incomplete:
        raise ValueError("incomplete valid repetitions: " + ", ".join(incomplete))
    return {
        "schema": 2,
        "eval_version": eval_version,
        "automated_regression_seat": dict(seat),
        "requested_reps": requested_reps,
        "capabilities": scored["capabilities"],
    }


def _sabotage_stamps(paths: list[Path], run_calib: dict) -> dict:
    stamps = {}
    for path in paths:
        stamp = json.loads(path.read_text())
        flow = stamp["flow"]
        if flow in stamps:
            raise ValueError(f"duplicate sabotage stamp for flow {flow!r}")
        stamps[flow] = stamp
    missing = sorted(set(run_calib) - set(stamps))
    if missing:
        raise ValueError(f"no sabotage stamp for flow(s) {', '.join(missing)} — "
                         "recalibrate first")
    stale = sorted(set(stamps) - set(run_calib))
    if stale:
        raise ValueError(f"sabotage stamp(s) for flow(s) {', '.join(stale)} "
                         "not in the baseline run — stale stamp?")
    drifted = sorted(flow for flow in run_calib
                     if stamps[flow]["calibration"] != run_calib[flow])
    if drifted:
        raise ValueError("baseline calibration != sabotage-pass for flow(s) "
                         f"{', '.join(drifted)} — recalibrate first")
    return stamps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("items", type=Path, help="saved output-items response")
    parser.add_argument("--sabotage", type=Path, required=True, action="append",
                        help="sabotage-pass stamp; repeat once per flow")
    parser.add_argument("--seat-id", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--eval-version", required=True)
    parser.add_argument("--reps", type=int, required=True)
    parser.add_argument("--max-indeterminate", type=int, default=0)
    args = parser.parse_args()

    response = json.loads(args.items.read_text())
    run_calib = (response.get("judge") or {}).get("calibration")
    if not isinstance(run_calib, dict):
        sys.exit(f"derive_gate: baseline judge.calibration is {run_calib!r}, not "
                 "a per-flow map — re-run the baseline")
    try:
        stamps = _sabotage_stamps(args.sabotage, run_calib)
        gate = derive_baseline(
            response,
            {"id": args.seat_id, "model_id": args.model_id,
             "harness": args.harness, "effort": args.effort},
            args.eval_version,
            args.reps,
        )
    except ValueError as error:
        sys.exit(f"derive_gate: {error}")

    stamped = f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
    gate.update({
        "calibration": run_calib,
        "sabotage_pass": {flow: {**stamps[flow], "date": stamped}
                          for flow in sorted(stamps)},
        "max_indeterminate": args.max_indeterminate,
    })
    EVALS_DIR.joinpath("gate.json").write_text(json.dumps(gate, indent=1) + "\n")
    calibration = ", ".join(f"{flow}={value}"
                            for flow, value in sorted(run_calib.items()))
    print(f"wrote evals/gate.json @ {calibration} "
          f"({len(gate['capabilities'])} capability(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
