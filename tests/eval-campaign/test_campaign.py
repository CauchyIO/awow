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
                eval_version="1")
            path = campaign.run_seat(seat, args)
            result = json.loads(path.read_text())
            self.assertNotIn("transcript", path.read_text().lower())
            self.assertEqual(result["seat"]["harness"], "Pi")
            self.assertEqual(result["seat"]["model_id"], "z-ai/glm-5.2")
            self.assertEqual(result["coverage"]["valid_repetitions"], 1)
            self.assertEqual(result["metrics"], {
                "tokens": 123, "cost_usd": 0.0042, "wall_s": 12.3})
            seatmap = json.loads(
                (root / "out" / "glm-5-2" / "seatmap.json").read_text())
            self.assertEqual(seatmap["bulk"], {"seat": "pi", "model": "glm-5-2"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
