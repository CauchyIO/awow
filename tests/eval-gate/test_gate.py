#!/usr/bin/env python3
"""Synthetic-record tests for the eval gate: every gate_errors branch in
.github/actions/eval-run/run.py and the derive_gate.py ceremony, per the
gate/trend/sabotage plan (Task 6 step 3). Real code paths throughout —
derive_gate runs as a subprocess against a temp copy, no mocks."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

spec = importlib.util.spec_from_file_location(
    "eval_run", REPO / ".github" / "actions" / "eval-run" / "run.py")
eval_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_run)

CALIB = "abc123"
FLOW = "setup-awow-walkthrough"

GATE = {"calibration": {FLOW: CALIB},
        "sabotage_pass": {FLOW: {"calibration": CALIB, "flow": FLOW}},
        "max_indeterminate": 1,
        "scenarios": {FLOW: {"min_mean": 4.0, "baseline_scores": [4, 5, 5]}}}


def cell(scen: str, rep: int, yes: int, verdict: str = "pass") -> dict:
    return {"id": f"eval-{scen}-1-{rep}", "verdict": verdict,
            "outcome": {"rubric_yes": yes, "rubric_total": 6}}


def resp(calib: str | None = CALIB) -> dict:
    return {"judge": {"tier": "worker", "calibration": {FLOW: calib}}
            if calib else None}


class TestGateErrors(unittest.TestCase):
    def test_clean_run_gates_clean(self):
        cells = [cell("setup-awow-walkthrough", r, 5) for r in (1, 2)]
        self.assertEqual(eval_run.gate_errors(resp(), cells, GATE), [])

    def test_no_sabotage_pass_refuses(self):
        gate = {**GATE, "sabotage_pass": None}
        errs = eval_run.gate_errors(resp(), [cell("setup-awow-walkthrough", 1, 5)], gate)
        self.assertEqual(len(errs), 1)
        self.assertIn("unqualified", errs[0])

    def test_calibration_drift_refuses(self):
        errs = eval_run.gate_errors(resp("other"), [cell("setup-awow-walkthrough", 1, 5)], GATE)
        self.assertEqual(len(errs), 1)
        self.assertIn("re-baseline", errs[0])

    def test_mean_below_floor_fails(self):
        cells = [cell("setup-awow-walkthrough", r, 3) for r in (1, 2)]
        errs = eval_run.gate_errors(resp(), cells, GATE)
        self.assertEqual(len(errs), 1)
        self.assertIn("mean 3.00 < gate 4.0", errs[0])

    def test_indeterminate_over_cap_fails_without_entering_mean(self):
        cells = [cell("setup-awow-walkthrough", 1, 5),
                 cell("setup-awow-walkthrough", 2, 0, verdict="indeterminate"),
                 cell("setup-awow-walkthrough", 3, 0, verdict="indeterminate")]
        errs = eval_run.gate_errors(resp(), cells, GATE)
        self.assertEqual(len(errs), 1)
        self.assertIn("indeterminate", errs[0])

    def test_baselined_scenario_with_no_cells_fails(self):
        """A baselined scenario that produced no data must not read as clean."""
        errs = eval_run.gate_errors(resp(), [], GATE)
        self.assertEqual(len(errs), 1)
        self.assertIn("0 judged cells", errs[0])

    def test_all_indeterminate_scenario_under_global_cap_still_fails(self):
        """One indeterminate cell is under the cap, but the scenario then has
        zero judged cells — that is missing coverage, not a clean gate."""
        cells = [cell("setup-awow-walkthrough", 1, 0, verdict="indeterminate")]
        errs = eval_run.gate_errors(resp(), cells, GATE)
        self.assertTrue(any("0 judged cells" in e for e in errs), errs)

    def test_two_flow_run_gates_clean(self):
        """AWO-72 AC: a two-scenario suite gates without a spurious drift
        refusal — the per-flow maps compare equal when no rubric changed."""
        calib = {FLOW: CALIB, "daily-digest": "def456"}
        gate = {"calibration": calib,
                "sabotage_pass": {
                    FLOW: {"calibration": CALIB, "flow": FLOW},
                    "daily-digest": {"calibration": "def456",
                                     "flow": "daily-digest"}},
                "max_indeterminate": 1,
                "scenarios": {FLOW: {"min_mean": 4.0},
                              "daily-digest": {"min_mean": 3.0}}}
        r = {"judge": {"tier": "worker", "calibration": calib}}
        cells = [cell(FLOW, 1, 5), cell(FLOW, 2, 5),
                 cell("daily-digest", 1, 4), cell("daily-digest", 2, 4)]
        self.assertEqual(eval_run.gate_errors(r, cells, gate), [])


class TestDeriveGate(unittest.TestCase):
    """derive_gate.py as a subprocess against a temp evals/ copy — the real
    ceremony, pointed away from the repo's own gate.json."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        shutil.copy(REPO / "evals" / "derive_gate.py", self.tmp / "derive_gate.py")
        (self.tmp / "scenarios" / "setup-awow-walkthrough").mkdir(parents=True)
        (self.tmp / "sab.json").write_text(json.dumps(
            {"calibration": CALIB, "flow": FLOW}))

    def derive(self, cells: list[dict], calib=None, stamps=("sab.json",)):
        (self.tmp / "items.json").write_text(json.dumps(
            {"judge": {"tier": "worker",
                       "calibration": {FLOW: CALIB} if calib is None else calib},
             "data": [{"cell": c} for c in cells]}))
        args = [sys.executable, str(self.tmp / "derive_gate.py"),
                str(self.tmp / "items.json")]
        for s in stamps:
            args += ["--sabotage", str(self.tmp / s)]
        return subprocess.run(args, capture_output=True, text=True)

    def test_happy_path_writes_gate(self):
        r = self.derive([cell("setup-awow-walkthrough", i, s)
                         for i, s in enumerate((4, 5, 5))])
        self.assertEqual(r.returncode, 0, r.stderr)
        gate = json.loads((self.tmp / "gate.json").read_text())
        scen = gate["scenarios"]["setup-awow-walkthrough"]
        self.assertEqual(scen["baseline_scores"], [4, 5, 5])
        self.assertAlmostEqual(scen["min_mean"], 4.67 - 1.0, places=2)
        self.assertEqual(gate["calibration"], {FLOW: CALIB})
        self.assertEqual(gate["sabotage_pass"][FLOW]["flow"], FLOW)

    def test_calibration_mismatch_refuses(self):
        r = self.derive([cell(FLOW, 1, 5)], calib={FLOW: "other"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("recalibrate", r.stderr)
        self.assertFalse((self.tmp / "gate.json").exists())

    def test_two_flow_baseline_with_both_stamps_writes_gate(self):
        """AWO-72 AC: scenario #2 + its own stamp derive cleanly — no
        spurious drift refusal from the old suite-level digest."""
        (self.tmp / "scenarios" / "daily-digest").mkdir()
        (self.tmp / "sab2.json").write_text(json.dumps(
            {"calibration": "def456", "flow": "daily-digest"}))
        r = self.derive(
            [cell(FLOW, i, 5) for i in (1, 2)] +
            [cell("daily-digest", i, 4) for i in (1, 2)],
            calib={FLOW: CALIB, "daily-digest": "def456"},
            stamps=("sab.json", "sab2.json"))
        self.assertEqual(r.returncode, 0, r.stderr)
        gate = json.loads((self.tmp / "gate.json").read_text())
        self.assertEqual(gate["calibration"],
                         {FLOW: CALIB, "daily-digest": "def456"})
        self.assertEqual(sorted(gate["sabotage_pass"]), ["daily-digest", FLOW])

    def test_missing_stamp_for_second_flow_refuses(self):
        (self.tmp / "scenarios" / "daily-digest").mkdir()
        r = self.derive([cell(FLOW, 1, 5), cell("daily-digest", 1, 4)],
                        calib={FLOW: CALIB, "daily-digest": "def456"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no sabotage stamp for flow(s) daily-digest", r.stderr)
        self.assertFalse((self.tmp / "gate.json").exists())

    def test_stale_stamp_for_absent_flow_refuses(self):
        (self.tmp / "sab2.json").write_text(json.dumps(
            {"calibration": "def456", "flow": "daily-digest"}))
        r = self.derive([cell(FLOW, 1, 5)], stamps=("sab.json", "sab2.json"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("stale", r.stderr)
        self.assertFalse((self.tmp / "gate.json").exists())

    def test_legacy_string_calibration_refuses(self):
        """A pre-AWO-72 items.json (suite-level string) must refuse loudly,
        not false-match a stamp."""
        r = self.derive([cell(FLOW, 1, 5)], calib=CALIB)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("per-flow", r.stderr)
        self.assertFalse((self.tmp / "gate.json").exists())

    def test_no_judged_cells_refuses(self):
        r = self.derive([cell("setup-awow-walkthrough", 1, 0, verdict="indeterminate")])
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.tmp / "gate.json").exists())

    def test_scenario_missing_from_baseline_refuses(self):
        """A scenario dir whose cells are absent (or all indeterminate) must
        refuse the baseline, not silently vanish from gate.json forever."""
        (self.tmp / "scenarios" / "daily-digest").mkdir()
        r = self.derive([cell("setup-awow-walkthrough", i, 5) for i in (1, 2)])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("daily-digest", r.stderr)
        self.assertFalse((self.tmp / "gate.json").exists())


if __name__ == "__main__":
    unittest.main()
