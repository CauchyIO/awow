#!/usr/bin/env python3
"""Behavior tests for the small outcome/process scorecard."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


eval_run = load_module(
    "eval_run_scorecard", REPO / ".github" / "actions" / "eval-run" / "run.py")
eval_validate = load_module("eval_validate", REPO / "evals" / "validate.py")


def write_rubric(path: Path, capability: str, outcome, process, critical):
    critical_text = ", ".join(f"`{q}`" for q in critical)
    outcome_text = "\n".join(f"- **{q}** — outcome {q}?" for q in outcome)
    process_text = "\n".join(f"- **{q}** — process {q}?" for q in process)
    path.write_text(
        f"# Rubric\n\nCapability: `{capability}`\n\n"
        f"Critical: {critical_text}\n\n"
        f"## Outcome\n\n{outcome_text}\n\n"
        f"## Process\n\n{process_text}\n"
    )


def cell(cell_id: str, answers, verdict: str = "pass") -> dict:
    questions = [
        {"question": f"**Q{i}** — question {i}?", "answer": answer,
         "evidence": "fixture"}
        for i, answer in enumerate(answers, 1)
    ]
    return {
        "id": cell_id,
        "verdict": verdict,
        "outcome": {"rubric": questions, "rubric_yes": sum(answers),
                    "rubric_total": len(answers)},
        "process": {"scope_violations": [], "gate_violation": False,
                    "stop_reason": "persona-done"},
        "checks": {"post": {"rc": 0, "log": ""}},
    }


def report(model_id: str, outcome: float, process: float,
           question_rate: float = 1.0) -> dict:
    return {
        "seat": {"id": "pi-seat", "model_id": model_id,
                 "harness": "Pi", "effort": "pinned"},
        "eval_version": "eval-1",
        "coverage": {"valid_repetitions": 5, "requested_repetitions": 5},
        "scenarios": {},
        "capabilities": {"flow": {
            "outcome": outcome,
            "process": process,
            "balanced": round((outcome + process) / 2, 2),
            "strict_pass": question_rate == 1.0,
            "valid_runs": 5,
            "requested_runs": 5,
            "questions": {
                "Q1": {"pass_rate": question_rate,
                       "dimension": "outcome", "critical": True},
            },
        }},
    }


class TestRubricContract(unittest.TestCase):
    def test_sections_capability_and_critical_ids_are_parsed(self):
        with tempfile.TemporaryDirectory() as td:
            rubric = Path(td) / "flow.md"
            rubric.write_text(
                "# Rubric\n\nCapability: `board-work`\n\n"
                "Critical: `Q1`, `Q3`\n\n"
                "## Outcome\n\n- **Q1** — shipped?\n- **Q2** — useful?\n\n"
                "## Process\n\n- **Q3** — gated?\n"
            )
            got = eval_run.parse_rubric(rubric)
        self.assertEqual(got["capability"], "board-work")
        self.assertEqual(got["critical"], {"Q1", "Q3"})
        self.assertEqual(got["questions"]["Q2"]["dimension"], "outcome")
        self.assertEqual(got["questions"]["Q3"]["dimension"], "process")

    def test_static_validator_requires_a_question_in_both_dimensions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scenario = root / "scenarios" / "flow"
            scenario.mkdir(parents=True)
            (scenario / "fixture").mkdir()
            for name in ("persona.md", "opening.md", "observe-writes.txt"):
                (scenario / name).write_text("fixture\n")
            rubrics = root / "rubrics"
            rubrics.mkdir()
            (rubrics / "flow.md").write_text(
                "Capability: `flow`\n\nCritical: `Q1`\n\n"
                "## Outcome\n\n- **Q1** — shipped?\n\n## Process\n"
            )
            errors, _ = eval_validate.validate(root)
        self.assertTrue(any("Process" in error for error in errors), errors)

    def test_vertical_suite_reports_every_required_capability(self):
        root = REPO / "evals"
        capabilities = {
            eval_run.parse_rubric(path)["capability"]
            for path in (root / "rubrics").glob("*.md")
        }
        self.assertEqual(capabilities, {
            "setup-awow", "workitem-write", "process-workitem", "daily-digest",
        })
        expected = {
            "setup-awow-walkthrough", "workitem-write-board-gate",
            "process-workitem-exit-ownership", "daily-digest-review-gate",
        }
        self.assertEqual(
            {p.name for p in (root / "scenarios").iterdir() if p.is_dir()},
            expected,
        )


class TestAggregation(unittest.TestCase):
    def test_indeterminate_is_excluded_and_scenarios_are_macro_averaged(self):
        with tempfile.TemporaryDirectory() as td:
            rubrics = Path(td)
            write_rubric(rubrics / "a.md", "digest",
                         outcome=("Q1",), process=("Q2",), critical=("Q2",))
            write_rubric(rubrics / "b.md", "digest",
                         outcome=("Q1", "Q2"), process=("Q3",), critical=("Q3",))
            cells = [
                cell("eval-a-deepseek-flash-v4-0731-r1", [True, True]),
                cell("eval-a-deepseek-flash-v4-0731-r2", [False, True], "fail"),
                cell("eval-b-deepseek-flash-v4-0731-r1", [True, True, False], "fail"),
                cell("eval-b-deepseek-flash-v4-0731-r2", [], "indeterminate"),
            ]
            got = eval_run.score_run(cells, rubrics, requested_reps=2)
        self.assertEqual(got["scenarios"]["a"]["outcome"], 50.0)
        self.assertEqual(got["scenarios"]["b"]["outcome"], 100.0)
        self.assertEqual(got["capabilities"]["digest"]["outcome"], 75.0)
        self.assertEqual(got["capabilities"]["digest"]["process"], 50.0)
        self.assertEqual(got["capabilities"]["digest"]["balanced"], 62.5)
        self.assertFalse(got["capabilities"]["digest"]["strict_pass"])
        self.assertEqual(got["coverage"]["valid_repetitions"], 3)
        self.assertEqual(got["coverage"]["requested_repetitions"], 4)


class TestComparison(unittest.TestCase):
    def test_model_pinned_five_point_readings_and_critical_override(self):
        baseline = report("provider/model@1", 80.0, 90.0)
        held = eval_run.compare_report(
            report("provider/model@1", 85.0, 86.0), baseline)
        self.assertEqual(held["capabilities"]["flow"]["reading"], "held")

        raised = eval_run.compare_report(
            report("provider/model@1", 85.1, 90.0), baseline)
        self.assertEqual(
            raised["capabilities"]["flow"]["outcome_reading"], "raised")

        regressed = eval_run.compare_report(
            report("provider/model@1", 99.0, 99.0, question_rate=0.8), baseline)
        self.assertEqual(regressed["capabilities"]["flow"]["reading"], "lowered")

        incompatible = eval_run.compare_report(
            report("provider/model@2", 99.0, 99.0), baseline)
        self.assertEqual(
            incompatible["capabilities"]["flow"]["reading"], "unmeasured")


if __name__ == "__main__":
    unittest.main(verbosity=2)
