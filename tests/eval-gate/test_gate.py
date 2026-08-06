#!/usr/bin/env python3
"""Behavior tests for model-pinned capability baselines and gating."""
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
FLOW = "setup-awow-walkthrough"
CALIB = "abc123"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


eval_run = load_module(
    "eval_run_gate", REPO / ".github" / "actions" / "eval-run" / "run.py")
derive_gate = load_module("derive_gate", REPO / "evals" / "derive_gate.py")


def rubric_text(capability: str = "setup-awow") -> str:
    return (
        f"Capability: `{capability}`\n\nCritical: `Q1`, `Q2`, `Q5`\n\n"
        "## Outcome\n\n"
        "- **Q1** — one?\n- **Q2** — two?\n"
        "- **Q3** — three?\n- **Q4** — four?\n\n"
        "## Process\n\n- **Q5** — five?\n- **Q6** — six?\n"
    )


def scorecard_cell(rep: int, answers, verdict: str = "pass",
                   flow: str = FLOW) -> dict:
    return {
        "id": f"eval-{flow}-glm-5-2-r{rep}",
        "verdict": verdict,
        "outcome": {
            "rubric_yes": sum(answers),
            "rubric_total": len(answers),
            "rubric": [
                {"question": f"**Q{i}** — question {i}?",
                 "answer": answer, "evidence": "fixture"}
                for i, answer in enumerate(answers, 1)
            ],
        },
        "process": {"scope_violations": [], "gate_violation": False,
                    "stop_reason": "persona-done"},
        "checks": {"post": {"rc": 0, "log": ""}},
    }


def scorecard_response(cells, model_id: str = "z-ai/glm-5.2",
                       calibration=None) -> dict:
    return {
        "judge": {"tier": "worker",
                  "calibration": calibration or {FLOW: CALIB}},
        "seat": {"id": "glm-5-2", "model_id": model_id,
                 "harness": "Pi", "effort": "pinned"},
        "eval_version": "1",
        "data": [{"cell": cell} for cell in cells],
    }


class TemporaryContract(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "scenarios" / FLOW).mkdir(parents=True)
        (self.tmp / "rubrics").mkdir()
        (self.tmp / "rubrics" / f"{FLOW}.md").write_text(rubric_text())
        self.old_rubrics = derive_gate.RUBRIC_DIR
        self.old_scenarios = derive_gate.SCENARIO_DIR
        derive_gate.RUBRIC_DIR = self.tmp / "rubrics"
        derive_gate.SCENARIO_DIR = self.tmp / "scenarios"
        self.addCleanup(setattr, derive_gate, "RUBRIC_DIR", self.old_rubrics)
        self.addCleanup(setattr, derive_gate, "SCENARIO_DIR", self.old_scenarios)

    def baseline(self, reps: int = 3) -> dict:
        answers = [
            [True, True, True, True, True, True],
            [True, True, False, True, True, True],
            [True, True, True, False, True, True],
        ][:reps]
        response = scorecard_response(
            [scorecard_cell(i, values) for i, values in enumerate(answers, 1)])
        return derive_gate.derive_baseline(
            response, response["seat"], eval_version="1", requested_reps=reps)


class TestCapabilityBaseline(TemporaryContract):
    def test_schema_two_pins_seat_and_capability_scores(self):
        baseline = self.baseline()
        self.assertEqual(baseline["schema"], 2)
        self.assertEqual(baseline["automated_regression_seat"]["id"], "glm-5-2")
        self.assertEqual(baseline["capabilities"]["setup-awow"]["outcome"], 83.33)
        self.assertEqual(
            baseline["capabilities"]["setup-awow"]["questions"]["Q1"]["pass_rate"],
            1.0,
        )

    def test_derivation_refuses_incomplete_repetitions(self):
        response = scorecard_response([
            scorecard_cell(1, [True] * 6),
            scorecard_cell(2, [True] * 6),
        ])
        with self.assertRaisesRegex(ValueError, "valid repetitions"):
            derive_gate.derive_baseline(
                response, response["seat"], eval_version="1", requested_reps=3)


class TestGateErrors(TemporaryContract):
    def gate(self) -> dict:
        return {
            **self.baseline(reps=2),
            "calibration": {FLOW: CALIB},
            "sabotage_pass": {FLOW: {"flow": FLOW, "calibration": CALIB}},
            "max_indeterminate": 0,
        }

    def test_clean_compatible_run_has_no_errors(self):
        current = scorecard_response([
            scorecard_cell(1, [True] * 6),
            scorecard_cell(2, [True] * 6),
        ])
        cells = [item["cell"] for item in current["data"]]
        self.assertEqual(eval_run.gate_errors(current, cells, self.gate()), [])

    def test_process_regression_is_reported(self):
        current = scorecard_response([
            scorecard_cell(1, [True, True, True, True, False, False], "fail"),
            scorecard_cell(2, [True, True, True, True, False, False], "fail"),
        ])
        errors = eval_run.gate_errors(
            current, [item["cell"] for item in current["data"]], self.gate())
        self.assertTrue(any("lowered process" in error for error in errors), errors)

    def test_indeterminate_run_is_unmeasured_not_a_regression(self):
        current = scorecard_response([
            scorecard_cell(1, [True] * 6),
            scorecard_cell(2, [], "indeterminate"),
        ])
        errors = eval_run.gate_errors(
            current, [item["cell"] for item in current["data"]], self.gate())
        self.assertTrue(any("unmeasured" in error for error in errors), errors)

    def test_model_mismatch_is_unmeasured(self):
        current = scorecard_response(
            [scorecard_cell(i, [True] * 6) for i in (1, 2)],
            model_id="z-ai/glm-5.2-revision-2",
        )
        errors = eval_run.gate_errors(
            current, [item["cell"] for item in current["data"]], self.gate())
        self.assertTrue(any("unmeasured" in error for error in errors), errors)

    def test_calibration_drift_refuses_before_scoring(self):
        current = scorecard_response(
            [scorecard_cell(i, [True] * 6) for i in (1, 2)],
            calibration={FLOW: "other"},
        )
        errors = eval_run.gate_errors(
            current, [item["cell"] for item in current["data"]], self.gate())
        self.assertEqual(len(errors), 1)
        self.assertIn("re-baseline", errors[0])

    def test_unqualified_judge_refuses_before_scoring(self):
        gate = self.gate()
        gate["sabotage_pass"] = None
        current = scorecard_response(
            [scorecard_cell(i, [True] * 6) for i in (1, 2)])
        errors = eval_run.gate_errors(
            current, [item["cell"] for item in current["data"]], gate)
        self.assertEqual(len(errors), 1)
        self.assertIn("unqualified", errors[0])


class TestDeriveGateCli(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        (self.tmp / "evals" / "scenarios" / FLOW).mkdir(parents=True)
        (self.tmp / "evals" / "rubrics").mkdir()
        (self.tmp / "evals" / "rubrics" / f"{FLOW}.md").write_text(rubric_text())
        shutil.copy(REPO / "evals" / "derive_gate.py",
                    self.tmp / "evals" / "derive_gate.py")
        runner_dir = self.tmp / ".github" / "actions" / "eval-run"
        runner_dir.mkdir(parents=True)
        shutil.copy(REPO / ".github" / "actions" / "eval-run" / "run.py",
                    runner_dir / "run.py")
        (self.tmp / "sab.json").write_text(json.dumps(
            {"calibration": CALIB, "flow": FLOW}))

    def derive(self, cells, calibration=None, stamps=("sab.json",), reps=2):
        response = scorecard_response(cells, calibration=calibration)
        (self.tmp / "items.json").write_text(json.dumps(response))
        args = [
            sys.executable, str(self.tmp / "evals" / "derive_gate.py"),
            str(self.tmp / "items.json"),
            "--seat-id", "glm-5-2", "--model-id", "z-ai/glm-5.2",
            "--harness", "Pi", "--effort", "pinned",
            "--eval-version", "1", "--reps", str(reps),
        ]
        for stamp in stamps:
            args += ["--sabotage", str(self.tmp / stamp)]
        return subprocess.run(args, cwd=self.tmp, capture_output=True, text=True)

    def test_happy_path_writes_model_pinned_gate(self):
        result = self.derive([
            scorecard_cell(1, [True] * 6),
            scorecard_cell(2, [True] * 6),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        gate = json.loads((self.tmp / "evals" / "gate.json").read_text())
        self.assertEqual(gate["schema"], 2)
        self.assertEqual(gate["automated_regression_seat"]["model_id"],
                         "z-ai/glm-5.2")
        self.assertEqual(gate["calibration"], {FLOW: CALIB})

    def test_calibration_mismatch_refuses(self):
        result = self.derive(
            [scorecard_cell(i, [True] * 6) for i in (1, 2)],
            calibration={FLOW: "other"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("recalibrate", result.stderr)
        self.assertFalse((self.tmp / "evals" / "gate.json").exists())

    def test_legacy_string_calibration_refuses(self):
        result = self.derive(
            [scorecard_cell(i, [True] * 6) for i in (1, 2)],
            calibration=CALIB,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("per-flow", result.stderr)

    def test_missing_scenario_data_refuses(self):
        missing = "daily-digest-review-gate"
        (self.tmp / "evals" / "scenarios" / missing).mkdir()
        (self.tmp / "evals" / "rubrics" / f"{missing}.md").write_text(
            rubric_text("daily-digest"))
        result = self.derive(
            [scorecard_cell(i, [True] * 6) for i in (1, 2)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(missing, result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
