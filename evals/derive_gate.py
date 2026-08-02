#!/usr/bin/env python3
"""Derive evals/gate.json from a baseline run (content spec §8). Operator
ceremony, not CI: dump GET /runs/<id>/output-items to a file, run the
sabotage calibration (harness/eval_sabotage.py), then:
  python3 evals/derive_gate.py items.json --sabotage sabotage-pass.json
Margin defaults to 1.0 rubric point below the baseline mean. Indeterminate
cells never enter a mean; a baseline with no judged cells refuses."""
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
    ap.add_argument("--sabotage", type=Path, required=True)
    ap.add_argument("--margin", type=float, default=1.0)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--max-indeterminate", type=int, default=1)
    a = ap.parse_args()
    resp = json.loads(a.items.read_text())
    sab = json.loads(a.sabotage.read_text())
    run_calib = (resp.get("judge") or {}).get("calibration")
    if run_calib != sab["calibration"]:
        sys.exit(f"derive_gate: baseline calibration {run_calib!r} != "
                 f"sabotage-pass {sab['calibration']!r} — recalibrate first")
    per = {}
    for item in resp["data"]:
        c = item["cell"]
        scen = c["id"].removeprefix("eval-").rsplit("-", 2)[0]
        if c.get("verdict") != "indeterminate":
            per.setdefault(scen, []).append(c["outcome"]["rubric_yes"])
    if not per:
        sys.exit("derive_gate: no judged cells in the baseline run")
    gate = {"calibration": sab["calibration"],
            "sabotage_pass": {**sab, "date":
                f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}"},
            "reps": a.reps, "max_indeterminate": a.max_indeterminate,
            "scenarios": {s: {"min_mean": round(statistics.mean(v) - a.margin, 2),
                              "baseline_scores": sorted(v)}
                          for s, v in sorted(per.items())}}
    Path(__file__).resolve().parent.joinpath("gate.json").write_text(
        json.dumps(gate, indent=1) + "\n")
    print(f"wrote evals/gate.json @ {gate['calibration']} "
          f"({len(per)} scenario(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
