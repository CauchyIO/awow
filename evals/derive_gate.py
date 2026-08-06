#!/usr/bin/env python3
"""Derive evals/gate.json from a baseline run (content spec §8). Operator
ceremony, not CI: dump GET /runs/<id>/output-items to a file, run the
sabotage calibration (harness/eval_sabotage.py) once per flow, then:
  python3 evals/derive_gate.py items.json --sabotage sab-flow-a.json \
      --sabotage sab-flow-b.json
Calibration is per flow (run's judge.calibration is a {flow: hash} map,
AWO-72): every flow in the baseline needs a matching stamp — a rubric edit
recalibrates only its own flow. Margin defaults to 1.0 rubric point below
the baseline mean. Indeterminate cells never enter a mean; a baseline with
no judged cells refuses."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("items", type=Path, help="saved output-items response")
    ap.add_argument("--sabotage", type=Path, required=True, action="append",
                    help="sabotage-pass stamp; repeat once per flow")
    ap.add_argument("--margin", type=float, default=1.0)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--max-indeterminate", type=int, default=1)
    a = ap.parse_args()
    resp = json.loads(a.items.read_text())
    stamps = {}
    for p in a.sabotage:
        sab = json.loads(p.read_text())
        if sab["flow"] in stamps:
            sys.exit(f"derive_gate: duplicate sabotage stamp for flow {sab['flow']!r}")
        stamps[sab["flow"]] = sab
    run_calib = (resp.get("judge") or {}).get("calibration")
    if not isinstance(run_calib, dict):
        sys.exit(f"derive_gate: baseline judge.calibration is {run_calib!r}, not a "
                 "per-flow map — re-run the baseline on a per-flow runner (AWO-72)")
    missing = sorted(set(run_calib) - set(stamps))
    if missing:
        sys.exit(f"derive_gate: no sabotage stamp for flow(s) "
                 f"{', '.join(missing)} — recalibrate first")
    stale = sorted(set(stamps) - set(run_calib))
    if stale:
        sys.exit(f"derive_gate: sabotage stamp(s) for flow(s) {', '.join(stale)} "
                 "not in the baseline run — stale stamp?")
    drifted = sorted(f for f in run_calib if stamps[f]["calibration"] != run_calib[f])
    if drifted:
        sys.exit("derive_gate: baseline calibration != sabotage-pass for flow(s) "
                 f"{', '.join(drifted)} — recalibrate first")
    per = {}
    for item in resp["data"]:
        c = item["cell"]
        scen = c["id"].removeprefix("eval-").rsplit("-", 2)[0]
        if c.get("verdict") != "indeterminate":
            per.setdefault(scen, []).append(c["outcome"]["rubric_yes"])
    if not per:
        sys.exit("derive_gate: no judged cells in the baseline run")
    scen_root = Path(__file__).resolve().parent / "scenarios"
    missing = sorted(p.name for p in scen_root.iterdir()
                     if p.is_dir() and p.name not in per)
    if missing:
        sys.exit(f"derive_gate: no judged cells for {', '.join(missing)} — "
                 "a flaky scenario must not silently drop out of the gate; "
                 "rerun the baseline")
    stamped = f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
    gate = {"calibration": run_calib,
            "sabotage_pass": {f: {**stamps[f], "date": stamped}
                              for f in sorted(stamps)},
            "reps": a.reps, "max_indeterminate": a.max_indeterminate,
            "scenarios": {s: {"min_mean": round(statistics.mean(v) - a.margin, 2),
                              "baseline_scores": sorted(v)}
                          for s, v in sorted(per.items())}}
    Path(__file__).resolve().parent.joinpath("gate.json").write_text(
        json.dumps(gate, indent=1) + "\n")
    calib = ", ".join(f"{f}={h}" for f, h in sorted(run_calib.items()))
    print(f"wrote evals/gate.json @ {calib} ({len(per)} scenario(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
