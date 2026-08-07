#!/usr/bin/env python3
"""Behavior tests for the small outcome/process scorecard."""
from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
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

    def test_static_validator_finds_checks_from_a_relative_suite_root(self):
        import os
        with tempfile.TemporaryDirectory(dir=".") as td:
            root = Path(td)
            scenario = root / "scenarios" / "flow"
            (scenario / "fixture").mkdir(parents=True)
            (scenario / "fixture" / "seed.md").write_text("stub\n")
            for name in ("persona.md", "opening.md", "observe-writes.txt"):
                (scenario / name).write_text("fixture\n")
            (scenario / "checks.sh").write_text("#!/bin/sh\nexit 0\n")
            rubrics = root / "rubrics"
            rubrics.mkdir()
            (rubrics / "flow.md").write_text(
                "Capability: `flow`\n\nCritical: `Q1`\n\n"
                "## Outcome\n\n- **Q1** — shipped?\n\n"
                "## Process\n\n- **Q2** — gated?\n"
            )
            errors, _ = eval_validate.validate(Path(os.path.relpath(root)))
        self.assertFalse([e for e in errors if "broken" in e], errors)

    def test_vertical_suite_reports_every_required_capability(self):
        root = REPO / "evals"
        capabilities = {
            eval_run.parse_rubric(path)["capability"]
            for path in (root / "rubrics").glob("*.md")
        }
        self.assertEqual(capabilities, {
            "setup-awow", "workitem-write", "process-workitem", "daily-digest",
            "session-reflex",
        })
        expected = {
            "setup-awow-walkthrough", "workitem-write-board-gate",
            "process-workitem-exit-ownership", "daily-digest-review-gate",
            "reflex-cold-start",
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

    def test_question_comparison_keeps_the_previous_rate_for_explanations(self):
        baseline = report("provider/model@1", 80.0, 90.0)
        compared = eval_run.compare_report(
            report("provider/model@1", 99.0, 99.0, question_rate=0.8), baseline)
        question = compared["capabilities"]["flow"]["questions"]["Q1"]
        self.assertEqual(question["baseline_pass_rate"], 1.0)
        self.assertEqual(question["pass_rate_delta"], -0.2)


def compared_report(critical_regression: bool = False) -> dict:
    reason = (["Q4 critical requirement regressed"]
              if critical_regression else ["Q4 newly failed"])
    return {
        "seat": {"id": "glm-5-2", "name": "GLM 5.2",
                 "model_id": "provider/model@revision",
                 "harness": "Pi", "effort": "pinned"},
        "eval_version": "1",
        "coverage": {"scenarios_executed": 2, "valid_repetitions": 9,
                     "requested_repetitions": 10},
        "scenarios": {},
        "capabilities": {
            "setup-awow": {
                "outcome": 90.0, "process": 95.0, "balanced": 92.5,
                "outcome_delta": 6.0, "process_delta": 1.0,
                "outcome_reading": "raised", "process_reading": "held",
                "reading": "raised", "strict_pass": True,
                "valid_runs": 5, "requested_runs": 5, "reasons": [],
                "questions": {},
            },
            "daily-digest": {
                "outcome": 70.0, "process": 88.0, "balanced": 79.0,
                "outcome_delta": -8.0, "process_delta": 0.0,
                "outcome_reading": "lowered", "process_reading": "held",
                "reading": "lowered", "strict_pass": False,
                "valid_runs": 4, "requested_runs": 5, "reasons": reason,
                "questions": {"Q4": {
                    "pass_rate": 0.5, "baseline_pass_rate": 1.0,
                    "pass_rate_delta": -0.5,
                    "dimension": "outcome",
                    "critical": critical_regression,
                }},
            },
        },
    }


def run_record() -> dict:
    return {
        "id": "api-run-1", "status": "completed",
        "metadata": {"result_branch": "night/eval-api-run-1"},
        "data_source": {"repo": "CauchyIO/awow", "sha": "a" * 40},
    }


class TestActionsScorecard(unittest.TestCase):
    def test_skill_changes_are_first_and_regressions_sort_first(self):
        text = "\n".join(eval_run.render_scorecard(
            run_record(), compared_report()))
        self.assertLess(text.index("1 lowered"), text.index("| Capability |"))
        self.assertLess(text.index("daily-digest"), text.index("setup-awow"))
        self.assertIn("| Outcome | Delta | Process | Delta |", text)
        self.assertIn("Q4", text)
        self.assertIn("Valid repetitions", text)
        self.assertIn("Pi", text)
        self.assertIn("provider/model@revision", text)
        self.assertNotIn("−0.0 pp", text)
        self.assertNotIn("OpenRouter", text)
        self.assertNotIn("APIM", text)

    def test_critical_regression_emits_error_annotation(self):
        output = io.StringIO()
        with redirect_stdout(output):
            eval_run.emit_annotations(compared_report(critical_regression=True))
        self.assertIn("::error title=eval critical regression::",
                      output.getvalue())

    def test_compact_artifact_carries_usage_cost_and_wall_time(self):
        cells = [
            {"process": {"tokens": 120, "cost_usd": 0.003, "wall_s": 10.2}},
            {"process": {"tokens": 80, "cost_usd": 0.002, "wall_s": 9.8}},
        ]
        compact = eval_run.compact_result(run_record(), compared_report(), cells)
        self.assertEqual(compact["metrics"], {
            "tokens": 200, "cost_usd": 0.005, "wall_s": 20.0})

    def test_fixed_seat_refuses_resolved_model_drift(self):
        seat = {"model_id": "z-ai/glm-5.2", "harness": "Pi"}
        cells = [{"process": {"resolved_model_id": "other/model"}}]
        with self.assertRaises(RuntimeError):
            eval_run.validate_resolved_model(cells, seat)

    def test_scored_non_pi_cell_without_resolved_model_fails(self):
        seat = {"model_id": "fable", "harness": "Claude Code"}
        cells = [{"id": "r1", "verdict": "pass", "process": {}}]
        with self.assertRaisesRegex(RuntimeError, "r1"):
            eval_run.validate_resolved_model(cells, seat)

    def test_systematic_runner_failure_still_validates_without_models(self):
        seat = {"model_id": "gpt-5.6-terra", "harness": "Codex"}
        cells = [{"id": "r1", "verdict": "indeterminate", "stage": "runner",
                  "process": {}}]
        eval_run.validate_resolved_model(cells, seat)  # must not raise

    def test_fixed_pi_seat_requires_identity_on_every_scored_cell(self):
        seat = {"model_id": "z-ai/glm-5.2", "harness": "Pi"}
        cells = [
            {"id": "scored-with-id", "verdict": "pass",
             "process": {"resolved_model_id": "z-ai/glm-5.2"}},
            {"id": "scored-without-id", "verdict": "fail", "process": {}},
            {"id": "runner-failure", "verdict": "indeterminate",
             "stage": "runner", "process": {}},
        ]
        with self.assertRaisesRegex(RuntimeError, "scored-without-id"):
            eval_run.validate_resolved_model(cells, seat)


if __name__ == "__main__":
    unittest.main(verbosity=2)
