#!/usr/bin/env python3
"""Transient-fault tests for .github/actions/eval-run/run.py.

No mocks: every test drives the real request/api/main code against a real
http.server bound to loopback, over real sockets and real urllib. The server
serves a scripted response sequence per path, so a flaky gateway is reproduced
rather than asserted about. Timings are shortened via module constants (config,
not substitution) so the suite runs in about a second."""
from __future__ import annotations

import http.server
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

spec = importlib.util.spec_from_file_location(
    "eval_run", REPO / ".github" / "actions" / "eval-run" / "run.py")
eval_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_run)

# Real waits, just short ones — the retry path still sleeps for real.
eval_run.RETRY_BACKOFF = (0.01, 0.01, 0.01)
eval_run.POLL_SECONDS = 0.01


def ok(payload: dict) -> tuple[int, dict]:
    return 200, payload


def boom(code: int = 500) -> tuple[int, dict]:
    return code, {"statusCode": code, "message": "Internal Server Error"}


class ScriptedHandler(http.server.BaseHTTPRequestHandler):
    """Serves the next scripted response for the request's path."""

    def _serve(self) -> None:
        path = self.path
        self.server.seen.append((self.command, path))
        queue = self.server.script.get(path)
        if not queue:
            self.send_error(404, "no scripted response")
            return
        code, payload = queue.pop(0) if len(queue) > 1 else queue[0]
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = do_POST = _serve

    def log_message(self, *args) -> None:  # keep test output clean
        pass


class ServerFixture(unittest.TestCase):
    """A real HTTP server on an ephemeral loopback port for each test."""

    def serve(self, script: dict[str, list]) -> None:
        self.server = http.server.HTTPServer(("127.0.0.1", 0), ScriptedHandler)
        self.server.script = script
        self.server.seen = []
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        host, port = self.server.server_address
        os.environ["EVAL_BASE_URL"] = f"http://{host}:{port}"
        os.environ["EVAL_API_KEY"] = "test-key"

    def calls(self, path: str) -> int:
        return sum(1 for _, p in self.server.seen if p == path)


class TestRetryPolicy(ServerFixture):
    def test_transient_is_retried_then_succeeds(self):
        self.serve({"/runs/r1": [boom(), boom(), ok({"status": "completed"})]})
        got = eval_run.api("GET", "/runs/r1", attempts=4)
        self.assertEqual(got["status"], "completed")
        self.assertEqual(self.calls("/runs/r1"), 3)

    def test_every_transient_status_is_retryable(self):
        for code in sorted(eval_run.TRANSIENT_STATUS):
            with self.subTest(code=code):
                self.serve({"/x": [boom(code), ok({"ok": True})]})
                self.assertEqual(eval_run.api("GET", "/x", attempts=2),
                                 {"ok": True})
                self.assertEqual(self.calls("/x"), 2)

    def test_single_shot_does_not_retry(self):
        """POST /runs must never be retried — a duplicate run is billable."""
        self.serve({"/runs": [boom()]})
        with self.assertRaises(eval_run.Transient):
            eval_run.api("POST", "/runs", {"a": 1})
        self.assertEqual(self.calls("/runs"), 1)

    def test_retry_exhaustion_raises_the_real_error(self):
        self.serve({"/runs/r1": [boom(503)]})
        with self.assertRaises(eval_run.Transient) as caught:
            eval_run.api("GET", "/runs/r1", attempts=3)
        self.assertIn("503", str(caught.exception))
        self.assertEqual(self.calls("/runs/r1"), 3)

    def test_non_transient_error_is_not_retried(self):
        """A 404 is the service talking. It must surface, not be papered over."""
        self.serve({"/runs/r1": [(404, {"message": "Resource not found"})]})
        with self.assertRaises(Exception) as caught:
            eval_run.api("GET", "/runs/r1", attempts=4)
        self.assertNotIsInstance(caught.exception, eval_run.Transient)
        self.assertEqual(self.calls("/runs/r1"), 1)

    def test_unreachable_host_is_transient(self):
        os.environ["EVAL_BASE_URL"] = "http://127.0.0.1:1"  # nothing listening
        os.environ["EVAL_API_KEY"] = "test-key"
        with self.assertRaises(eval_run.Transient):
            eval_run.api("GET", "/runs/r1", attempts=2)


RECORD = {"id": "r1", "status": "completed",
          "metadata": {"result_branch": "night/eval-x",
                       "seat_id": "glm-5-2",
                       "resolved_model_id": "z-ai/glm-5.2",
                       "harness": "Pi", "effort": "pinned"},
          "data_source": {"repo": "CauchyIO/awow", "sha": "a" * 40}}

ITEMS = {"judge": {"calibration": {"setup-awow-walkthrough": "abc"}},
         "data": [{"cell": {
             "id": "eval-setup-awow-walkthrough-worker-r1",
             "outcome": {"rubric_yes": 5, "rubric_total": 6,
                         "rubric": [
                             {"question": f"**Q{i}** — question {i}?",
                              "answer": i != 6, "evidence": "because"}
                             for i in range(1, 7)]},
             "process": {"stop_reason": "persona-done",
                         "scope_violations": [], "gate_violation": False},
             "checks": {"post": {"rc": 0, "log": ""}}}}]}


class TestPollLoop(ServerFixture):
    """End-to-end through main(): real server, real sockets, real retries."""

    def drive(self, script: dict[str, list]) -> int:
        self.serve(script)
        env = {"EVAL_MODEL": "worker", "EVAL_REPS": "1",
               "EVAL_BUDGET_PER_SCENARIO": "400000",
               "EVAL_SEAT_ID": "glm-5-2", "EVAL_VERSION": "1",
               "EVAL_SCENARIOS": "setup-awow-walkthrough",
               "EVAL_ENFORCE": "false"}
        for k, v in env.items():
            os.environ[k] = v
        temp = Path(tempfile.mkdtemp())
        out = temp / "summary.md"
        out.touch()
        os.environ["GITHUB_STEP_SUMMARY"] = str(out)
        os.environ["GITHUB_OUTPUT"] = str(temp / "github-output")
        os.environ["EVAL_RESULT_PATH"] = str(temp / "eval-result.json")
        self.summary_path = out
        self.result_path = temp / "eval-result.json"
        os.chdir(REPO)  # main() reads evals/scenarios and git HEAD
        return eval_run.main()

    def test_poll_survives_transients_below_the_cap(self):
        rc = self.drive({
            "/runs": [ok({"id": "r1"})],
            "/runs/r1": [boom(), boom(), boom(), ok(RECORD)],
            "/runs/r1/output-items": [ok(ITEMS)],
        })
        self.assertEqual(rc, 0)
        self.assertEqual(self.calls("/runs/r1"), 4)
        self.assertIn("5/6", self.summary_path.read_text())
        result = json.loads(self.result_path.read_text())
        self.assertEqual(result["contract"], "awow.eval-scorecard/v1")
        self.assertNotIn("transcript", self.result_path.read_text().lower())

    def test_poll_gives_up_after_consecutive_cap(self):
        self.assertEqual(eval_run.MAX_CONSECUTIVE_POLL_FAILURES, 5)
        with self.assertRaises(eval_run.Transient):
            self.drive({"/runs": [ok({"id": "r1"})], "/runs/r1": [boom()]})
        self.assertEqual(self.calls("/runs/r1"),
                         eval_run.MAX_CONSECUTIVE_POLL_FAILURES)

    def test_consecutive_counter_resets_on_success(self):
        """Blips spread out must not accumulate into a spurious give-up."""
        script = [boom(), boom(), boom(), boom(), ok({"status": "queued"}),
                  boom(), boom(), boom(), boom(), ok(RECORD)]
        rc = self.drive({"/runs": [ok({"id": "r1"})], "/runs/r1": script,
                         "/runs/r1/output-items": [ok(ITEMS)]})
        self.assertEqual(rc, 0)
        self.assertEqual(self.calls("/runs/r1"), 10)

    def test_submission_transient_aborts_without_retry(self):
        with self.assertRaises(eval_run.Transient):
            self.drive({"/runs": [boom()]})
        self.assertEqual(self.calls("/runs"), 1)

    def test_output_items_blip_does_not_lose_the_scores(self):
        rc = self.drive({
            "/runs": [ok({"id": "r1"})],
            "/runs/r1": [ok(RECORD)],
            "/runs/r1/output-items": [boom(), boom(), ok(ITEMS)],
        })
        self.assertEqual(rc, 0)
        self.assertIn("5/6", self.summary_path.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
