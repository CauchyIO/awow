#!/usr/bin/env python3
"""Contract tests for the deliberately small local model campaign."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace


REPO = Path(__file__).resolve().parents[2]


def load_campaign():
    path = REPO / "evals" / "campaign.py"
    spec = importlib.util.spec_from_file_location("eval_campaign", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compact_run(seat, outcome=82.0, process=88.0, valid=10, requested=10):
    return {
        "contract": "awow.eval-scorecard/v1", "subject_sha": "a" * 40,
        "eval_version": "1", "awow_version": "0.7.0",
        "profile": "establishment",
        "scenarios": ["setup-awow-walkthrough"],
        "seat": {"id": seat["id"], "name": seat["name"],
                 "model_id": f"provider/{seat['id']}",
                 "harness": seat["harness"], "effort": seat["effort"]},
        "requested_model": seat["model"],
        "coverage": {"scenarios_executed": 1,
                     "valid_repetitions": valid,
                     "requested_repetitions": requested},
        "capabilities": {"setup-awow": {
            "outcome": outcome, "process": process,
            "balanced": round((outcome + process) / 2, 2),
            "strict_pass": True, "valid_runs": valid,
            "requested_runs": requested, "questions": {},
        }},
        "metrics": {"tokens": 1234, "cost_usd": 0.0123, "wall_s": 45.6},
        "systematic_failure": False,
    }


def fixture_campaign(module):
    seats = module.load_seats(REPO / "evals" / "model-seats.json")
    runs = [compact_run(seat) for seat in seats]
    return {"contract": "awow.eval-campaign/v1", "subject_sha": "a" * 40,
            "eval_version": "1", "profile": "establishment",
            "awow_version": "0.7.0", "run_date": "2026-08-06",
            "model_resolution": {
                run["seat"]["id"]: run["seat"]["model_id"] for run in runs},
            "runs": runs}


class TestRoster(unittest.TestCase):
    def test_roster_is_fixed_twelve_and_every_seat_is_baseline_eligible(self):
        campaign = load_campaign()
        seats = campaign.load_seats(REPO / "evals" / "model-seats.json")
        self.assertEqual(len(seats), 12)
        self.assertEqual({seat["harness"] for seat in seats},
                         {"Codex", "Claude Code", "Pi"})
        self.assertTrue(all(seat["baseline_eligible"] is True for seat in seats))
        self.assertEqual(sum(seat["weekly"] for seat in seats), 6)
        self.assertTrue(all(seat["harness"] == "Pi"
                            for seat in seats if seat["weekly"]))
        self.assertEqual(len({seat["id"] for seat in seats}), 12)
        self.assertEqual({seat["id"] for seat in seats}, {
            "gpt-5-6-sol-xhigh", "gpt-terra-high", "gpt-luna-high",
            "fable-5-high", "opus-5-high", "sonnet-5-high", "kimi-k3",
            "glm-5-2", "deepseek-flash-v4-0731", "gemma-4-26b",
            "qwen-3-6", "poolside-laguna-s2-1",
        })

    def test_serving_endpoints_are_not_seat_or_harness_labels(self):
        campaign = load_campaign()
        seats = campaign.load_seats(REPO / "evals" / "model-seats.json")
        text = json.dumps(seats).lower()
        self.assertNotIn("openrouter", text)
        self.assertNotIn("apim", text)

    def test_weekly_workflow_derives_seats_instead_of_repeating_the_roster(self):
        workflow = (REPO / ".github" / "workflows" / "evals-weekly.yml").read_text()
        seats = load_campaign().load_seats(REPO / "evals" / "model-seats.json")
        self.assertIn("select(.weekly == true)", workflow)
        for seat in seats:
            if seat["weekly"]:
                self.assertNotIn(seat["id"], workflow)

    def test_campaign_profiles_are_the_fixed_horizontal_snapshot(self):
        campaign = load_campaign()
        self.assertEqual(campaign.PROFILES["establishment"], {
            "scenarios": ["setup-awow-walkthrough"], "reps": 10})
        self.assertEqual(campaign.PROFILES["snapshot"], {
            "scenarios": ["setup-awow-walkthrough"], "reps": 5})

    def test_resolution_is_qualified_for_every_selected_seat_up_front(self):
        campaign = load_campaign()
        seats = campaign.load_seats(REPO / "evals" / "model-seats.json")
        with self.assertRaises(ValueError):
            campaign.validate_model_resolution(seats, {"glm-5-2": "z-ai/glm-5.2"})


class TestMerge(unittest.TestCase):
    def test_merge_refuses_mixed_subjects_and_orders_by_roster(self):
        campaign = load_campaign()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            paths = []
            for index, seat_id in enumerate(("glm-5-2", "kimi-k3")):
                path = root / f"{seat_id}.json"
                path.write_text(json.dumps({
                    "contract": "awow.eval-scorecard/v1",
                    "subject_sha": ("a" if index == 0 else "b") * 40,
                    "eval_version": "1", "seat": {"id": seat_id},
                    "coverage": {}, "capabilities": {},
                }))
                paths.append(path)
            with self.assertRaises(ValueError):
                campaign.merge_campaign(paths)


class TestRunSeat(unittest.TestCase):
    def test_resume_refuses_stale_profile_or_seat_identity(self):
        campaign = load_campaign()
        seat = next(seat for seat in campaign.load_seats(
            REPO / "evals" / "model-seats.json") if seat["id"] == "glm-5-2")
        base = compact_run(seat, valid=5, requested=5)
        base.update({
            "profile": "snapshot",
            "scenarios": ["setup-awow-walkthrough"],
            "awow_version": "0.7.0",
            "requested_model": "glm-5-2",
        })
        base["seat"]["model_id"] = "z-ai/glm-5.2"
        mutations = {
            "profile": lambda run: run.update(profile="establishment"),
            "scenarios": lambda run: run.update(scenarios=["daily-digest-review-gate"]),
            "requested model": lambda run: run.update(requested_model="old-glm-route"),
            "resolved model": lambda run: run["seat"].update(model_id="old/glm"),
            "harness": lambda run: run["seat"].update(harness="OpenRouter"),
            "effort": lambda run: run["seat"].update(effort="old-setting"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                stale = json.loads(json.dumps(base))
                mutate(stale)
                result = root / "out" / seat["id"] / "eval-result.json"
                result.parent.mkdir(parents=True)
                result.write_text(json.dumps(stale))
                args = SimpleNamespace(
                    out=root / "out", subject_sha="a" * 40,
                    scenarios=["setup-awow-walkthrough"], reps=5,
                    model_resolution={"glm-5-2": "z-ai/glm-5.2"},
                    eval_version="1", profile="snapshot",
                    awow_version="0.7.0")
                with self.assertRaisesRegex(RuntimeError, "another campaign"):
                    campaign.run_seat(seat, args)

    def test_real_fake_subprocesses_produce_one_compact_result(self):
        campaign = load_campaign()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evaluator = root / "evaluator"
            evaluator.mkdir()
            (evaluator / "make_eval_bundles.py").write_text(textwrap.dedent("""
                import sys
                from pathlib import Path
                Path(sys.argv[sys.argv.index('--out') + 1]).mkdir(parents=True)
            """))
            (evaluator / "eval_run_local.py").write_text(textwrap.dedent("""
                import json, sys
                from pathlib import Path
                out = Path(sys.argv[sys.argv.index('--out') + 1])
                out.mkdir(parents=True)
                answers = [
                    {'question': f'**Q{i}** — question {i}?',
                     'answer': True, 'evidence': 'fixture'}
                    for i in range(1, 7)
                ]
                cell = {
                    'id': 'eval-setup-awow-walkthrough-bulk-r1',
                    'verdict': 'pass',
                    'outcome': {'rubric': answers, 'rubric_yes': 6,
                                'rubric_total': 6},
                    'process': {'scope_violations': [], 'gate_violation': False,
                                'stop_reason': 'persona-done', 'wall_s': 12.3,
                                'tokens': 123, 'cost_usd': 0.0042,
                                'resolved_model_id': 'z-ai/glm-5.2'},
                    'checks': {'post': {'rc': 0, 'log': ''}},
                }
                (out / 'result.json').write_text(json.dumps({
                    'contract': 'eval/v1', 'request_sha': 'a' * 40,
                    'cells': [cell]}))
            """))
            seat = next(seat for seat in campaign.load_seats(
                REPO / "evals" / "model-seats.json") if seat["id"] == "glm-5-2")
            args = SimpleNamespace(
                out=root / "out", evaluator_root=evaluator,
                subject_root=REPO, subject_sha="a" * 40,
                scenarios=["setup-awow-walkthrough"], reps=1,
                model_resolution={"glm-5-2": "z-ai/glm-5.2"},
                eval_version="1", profile="snapshot",
                awow_version="0.7.0")
            path = campaign.run_seat(seat, args)
            result = json.loads(path.read_text())
            self.assertNotIn("transcript", path.read_text().lower())
            self.assertEqual(result["seat"]["harness"], "Pi")
            self.assertEqual(result["seat"]["model_id"], "z-ai/glm-5.2")
            self.assertEqual(result["profile"], "snapshot")
            self.assertEqual(result["scenarios"], ["setup-awow-walkthrough"])
            self.assertEqual(result["awow_version"], "0.7.0")
            self.assertEqual(result["coverage"]["valid_repetitions"], 1)
            self.assertEqual(result["metrics"], {
                "tokens": 123, "cost_usd": 0.0042, "wall_s": 12.3})
            seatmap = json.loads(
                (root / "out" / "glm-5-2" / "seatmap.json").read_text())
            self.assertEqual(seatmap["bulk"], {"seat": "pi", "model": "glm-5-2"})


class TestWeeklySummary(unittest.TestCase):
    def test_weekly_table_is_roster_ordered_and_unmeasured_without_previous(self):
        campaign = load_campaign()
        seats = [seat for seat in campaign.load_seats(
            REPO / "evals" / "model-seats.json") if seat["weekly"]]
        text = campaign.render_weekly_summary([compact_run(seat) for seat in seats])
        self.assertLess(text.index("Kimi K3"), text.index("GLM 5.2"))
        self.assertIn("| Model / effort | Harness | Outcome | Process | Balanced |", text)
        self.assertIn("$0.0123", text)
        self.assertIn("45.6s", text)
        self.assertEqual(text.count("unmeasured"), 6)
        self.assertNotIn("OpenRouter", text)
        self.assertNotIn("APIM", text)

    def test_weekly_reading_uses_only_an_explicit_compatible_previous_run(self):
        campaign = load_campaign()
        seat = next(seat for seat in campaign.load_seats(
            REPO / "evals" / "model-seats.json") if seat["id"] == "kimi-k3")
        previous = compact_run(seat, outcome=82.0)
        current = compact_run(seat, outcome=88.0)
        text = campaign.render_weekly_summary([current], [previous])
        row = next(line for line in text.splitlines() if "Kimi K3" in line)
        self.assertTrue(row.endswith("| raised |"), row)


class TestPublication(unittest.TestCase):
    def test_every_seat_can_qualify_regardless_of_weekly_flag(self):
        campaign = load_campaign()
        for seat in campaign.load_seats(REPO / "evals" / "model-seats.json"):
            result = {**seat, "valid_runs": 10, "requested_runs": 10,
                      "outcome": 82.0, "process": 88.0,
                      "strict_pass": True, "systematic_failure": False}
            self.assertEqual(campaign.qualifies(result), (True, []), seat["id"])

    def test_failed_strict_pass_has_one_readable_reason(self):
        campaign = load_campaign()
        result = {"valid_runs": 10, "requested_runs": 10,
                  "outcome": 82.0, "process": 88.0,
                  "strict_pass": False, "systematic_failure": False}
        self.assertEqual(campaign.qualifies(result),
                         (False, ["strict pass failed"]))

    def test_readme_snapshot_is_clean_and_baseline_first(self):
        campaign = load_campaign()
        block = campaign.render_readme_snapshot(
            fixture_campaign(campaign), "gpt-5-6-sol-xhigh", "glm-5-2")
        self.assertIn("Run date: 2026-08-06", block)
        self.assertIn("awow version: 0.7.0", block)
        self.assertIn("Eval version: 1", block)
        self.assertLess(block.index("**Performance baseline**"),
                        block.index("Automated regression"))
        self.assertNotIn("Delta", block)
        self.assertNotIn("Raised", block)
        self.assertNotIn("Lowered", block)
        self.assertNotIn("OpenRouter", block)
        self.assertNotIn("APIM", block)

    def test_snapshot_uses_the_version_captured_with_the_evaluated_commit(self):
        campaign = load_campaign()
        snapshot = fixture_campaign(campaign)
        snapshot["awow_version"] = "0.6.9"
        for run in snapshot["runs"]:
            run["awow_version"] = "0.6.9"
        block = campaign.render_readme_snapshot(
            snapshot, "gpt-5-6-sol-xhigh", "glm-5-2")
        self.assertIn("awow version: 0.6.9", block)

    def test_publication_rejects_campaign_or_roster_drift(self):
        campaign = load_campaign()

        def add_duplicate(value):
            value["runs"].append(json.loads(json.dumps(value["runs"][0])))

        def add_extra(value):
            extra = json.loads(json.dumps(value["runs"][0]))
            extra["seat"]["id"] = "unconfigured-seat"
            value["runs"].append(extra)

        mutations = {
            "campaign contract": lambda value: value.update(contract="other/v1"),
            "profile": lambda value: value.update(profile="ad-hoc"),
            "duplicate seat": add_duplicate,
            "extra seat": add_extra,
            "seat harness": lambda value: value["runs"][6]["seat"].update(
                harness="OpenRouter"),
            "requested model": lambda value: value["runs"][0].update(
                requested_model="stale-model"),
            "resolved model": lambda value: value["runs"][0]["seat"].update(
                model_id="stale/provider-model"),
            "subject": lambda value: value["runs"][0].update(subject_sha="b" * 40),
            "eval version": lambda value: value["runs"][0].update(eval_version="0"),
            "run profile": lambda value: value["runs"][0].update(profile="snapshot"),
            "scenarios": lambda value: value["runs"][0].update(
                scenarios=["daily-digest-review-gate"]),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                snapshot = fixture_campaign(campaign)
                mutate(snapshot)
                with self.assertRaises(ValueError):
                    campaign.render_readme_snapshot(
                        snapshot, "gpt-5-6-sol-xhigh", "glm-5-2")

    def test_marker_replacement_changes_only_the_snapshot_body(self):
        campaign = load_campaign()
        readme = ("before\n<!-- eval-snapshot:start -->\nold\n"
                  "<!-- eval-snapshot:end -->\nafter\n")
        got = campaign.replace_snapshot(readme, "new")
        self.assertEqual(got, ("before\n<!-- eval-snapshot:start -->\nnew\n"
                               "<!-- eval-snapshot:end -->\nafter\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
