import contextlib
import datetime as dt
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import cascade_check  # noqa: E402
from fixture import _git, make_department, make_team  # noqa: E402

CASCADE_CHECK_PATH = REPO_ROOT / "tools" / "cascade_check.py"

REGISTRY = """# Teams
| Team | Path | Lead |
|---|---|---|
| Team Blue | teams/team-blue | B. Lead |
| Team Green | teams/team-green | G. Lead |
"""

OKRS = """# Department OKRs 2026-Q3
## O1 — Ship the platform
- O1.KR1: from 0 to 3 modules by 2026-09-30
- O1.KR2: uptime 99.5%
## O2 — Grow adoption
- O2.KR1: 4 -> 8 teams
"""


class TestParsers(unittest.TestCase):
    def test_registry(self):
        rows = cascade_check.parse_registry(REGISTRY)
        self.assertEqual([r["team"] for r in rows], ["Team Blue", "Team Green"])
        self.assertEqual(rows[0]["path"], "teams/team-blue")

    def test_registry_malformed_fails_loud(self):
        with self.assertRaises(cascade_check.CascadeConfigError):
            cascade_check.parse_registry("no table here")

    def test_registry_mixed_good_and_malformed_row(self):
        """Good row + malformed row (missing cell) should raise CascadeConfigError."""
        text = """# Teams
| Team | Path | Lead |
|---|---|---|
| Team Blue | teams/team-blue | B. Lead |
| Team Green | teams/team-green |
"""
        with self.assertRaises(cascade_check.CascadeConfigError) as cm:
            cascade_check.parse_registry(text)
        self.assertIn("malformed row", str(cm.exception))

    def test_okr_ids(self):
        ids = cascade_check.parse_okr_ids(OKRS)
        self.assertEqual(ids, {"O1", "O1.KR1", "O1.KR2", "O2", "O2.KR1"})

    def test_serves_headers(self):
        text = "Serves: O1\nServes: O2.KR1\n\n# Quarter focus\nServes: O9 (ignored, not leading)\n"
        self.assertEqual(cascade_check.parse_serves_headers(text), ["O1", "O2.KR1"])

    def test_serves_none(self):
        self.assertEqual(cascade_check.parse_serves_headers("# Just notes\n"), [])

    def test_serves_headers_with_blank_line(self):
        """Blank lines don't stop the scan; only non-empty non-Serves lines do."""
        text = "Serves: O1\n\nServes: O2\n# content\nServes: O3\n"
        self.assertEqual(cascade_check.parse_serves_headers(text), ["O1", "O2"])


class TestLoadIndirection(unittest.TestCase):
    def test_load_indirection_happy_path(self):
        """Happy path: valid frontmatter returns parsed dict with correct types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "context" / "tooling").mkdir(parents=True)
            dept_file = repo_root / "context" / "tooling" / "department.md"
            dept_file.write_text("""---
teams_root: teams/
read_scope: decisions, proposals
decisions_dir: context/decisions/
stale_after_days: 90
---
# Department tooling config
""")
            result = cascade_check.load_indirection(repo_root)
            self.assertEqual(result["teams_root"], "teams/")
            self.assertEqual(result["read_scope"], ["decisions", "proposals"])
            self.assertEqual(result["decisions_dir"], "context/decisions/")
            self.assertEqual(result["stale_after_days"], 90)
            self.assertIsInstance(result["stale_after_days"], int)
            self.assertIsInstance(result["read_scope"], list)

    def test_load_indirection_missing_file(self):
        """Missing context/tooling/department.md raises CascadeConfigError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            with self.assertRaises(cascade_check.CascadeConfigError) as cm:
                cascade_check.load_indirection(repo_root)
            self.assertIn("missing", str(cm.exception))

    def test_load_indirection_missing_field(self):
        """Missing required field raises CascadeConfigError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "context" / "tooling").mkdir(parents=True)
            dept_file = repo_root / "context" / "tooling" / "department.md"
            dept_file.write_text("""---
teams_root: teams/
read_scope: decisions
decisions_dir: context/decisions/
---
# Missing stale_after_days
""")
            with self.assertRaises(cascade_check.CascadeConfigError) as cm:
                cascade_check.load_indirection(repo_root)
            self.assertIn("missing field", str(cm.exception))

    def test_load_indirection_non_integer_stale_days(self):
        """Non-integer stale_after_days raises CascadeConfigError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "context" / "tooling").mkdir(parents=True)
            dept_file = repo_root / "context" / "tooling" / "department.md"
            dept_file.write_text("""---
teams_root: teams/
read_scope: decisions
decisions_dir: context/decisions/
stale_after_days: not-a-number
---
# Invalid stale_after_days
""")
            with self.assertRaises(cascade_check.CascadeConfigError) as cm:
                cascade_check.load_indirection(repo_root)
            self.assertIn("stale_after_days", str(cm.exception))
            self.assertIn("integer", str(cm.exception))

    def test_load_indirection_real_repo(self):
        """Real repo: load_indirection(REPO_ROOT) succeeds and returns teams_root == 'teams'."""
        result = cascade_check.load_indirection(REPO_ROOT)
        self.assertEqual(result["teams_root"], "teams")


class TestFindQuarterDoc(unittest.TestCase):
    def test_find_quarter_doc_newest_by_name(self):
        """Newest OKR doc by name sort (lexicographic)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            dept_dir = repo_root / "context" / "department"
            dept_dir.mkdir(parents=True)
            (dept_dir / "okrs-2026-Q2.md").write_text("# Q2")
            (dept_dir / "okrs-2026-Q3.md").write_text("# Q3")
            result = cascade_check.find_quarter_doc(repo_root)
            self.assertEqual(result.name, "okrs-2026-Q3.md")

    def test_find_quarter_doc_empty_dir(self):
        """No OKR docs raises CascadeConfigError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "context" / "department").mkdir(parents=True)
            with self.assertRaises(cascade_check.CascadeConfigError) as cm:
                cascade_check.find_quarter_doc(repo_root)
            self.assertIn("okrs-", str(cm.exception))


class TestRunCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_clean_department(self):
        a = make_team(self.tmp, "team-a", ["O1"]); b = make_team(self.tmp, "team-b", ["O2.KR1"])
        dept = make_department(self.tmp, [a, b])
        result = cascade_check.run_check(dept)
        self.assertEqual(result["findings"], [])

    def test_serves_unknown_and_orphan(self):
        a = make_team(self.tmp, "team-a", ["O9"]); b = make_team(self.tmp, "team-b", ["O1"])
        dept = make_department(self.tmp, [a, b])
        classes = sorted(f["class"] for f in cascade_check.run_check(dept)["findings"])
        self.assertIn("serves-unknown", classes)
        self.assertIn("orphaned-objective", classes)  # O2 unserved

    def test_serves_nothing(self):
        a = make_team(self.tmp, "team-a", [])
        dept = make_department(self.tmp, [a])
        classes = [f["class"] for f in cascade_check.run_check(dept)["findings"]]
        self.assertIn("serves-nothing", classes)

    def test_missing_okrs_is_config_error(self):
        a = make_team(self.tmp, "team-a", ["O1"])
        dept = make_department(self.tmp, [a])
        (dept / "context" / "department" / "okrs-2026-Q3.md").unlink()
        with self.assertRaises(cascade_check.CascadeConfigError):
            cascade_check.run_check(dept)

    def test_git_failure_short_circuits_to_single_registered_missing(self):
        """A git failure resolving a team's pin/remote state (here: no `origin` to
        ls-remote) yields exactly one registered-missing finding for that team,
        with no content (backlink/Serves) findings alongside it. The other team's
        checks are unaffected."""
        a = make_team(self.tmp, "team-a", ["O1"]); b = make_team(self.tmp, "team-b", ["O2.KR1"])
        dept = make_department(self.tmp, [a, b])
        _git(dept / "teams" / "team-a", "remote", "remove", "origin")
        result = cascade_check.run_check(dept)
        team_a_findings = [f for f in result["findings"] if f["team"] == "team-a"]
        self.assertEqual(len(team_a_findings), 1)
        self.assertEqual(team_a_findings[0]["class"], "registered-missing")
        team_b_findings = [f for f in result["findings"] if f["team"] == "team-b"]
        self.assertEqual(team_b_findings, [])


class TestFindingClasses(unittest.TestCase):
    """One seeded deviation per remaining finding class, plus CLI exit codes.

    Clean department, serves-unknown/orphaned-objective, serves-nothing,
    missing-OKR-doc config error, and the git-failure short-circuit are
    already covered by TestRunCheck above and are not duplicated here.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(CASCADE_CHECK_PATH), *args],
            capture_output=True, text=True,
        )

    def test_backlink_missing(self):
        a = make_team(self.tmp, "team-a", ["O1"])
        dept = make_department(self.tmp, [a])
        backlink = dept / "teams" / "team-a" / "context" / "company" / "department.md"
        backlink.unlink()
        classes = [(f["class"], f["team"]) for f in cascade_check.run_check(dept)["findings"]]
        self.assertIn(("backlink-missing", "team-a"), classes)

    def test_backlink_mismatch(self):
        a = make_team(self.tmp, "team-a", ["O1"])
        dept = make_department(self.tmp, [a])
        backlink = dept / "teams" / "team-a" / "context" / "company" / "department.md"
        backlink.write_text("---\ndepartment: Dept\nparent: file:///not/the/right/origin\n---\n")
        classes = [(f["class"], f["team"]) for f in cascade_check.run_check(dept)["findings"]]
        self.assertIn(("backlink-mismatch", "team-a"), classes)

    def test_registered_missing_for_registry_row_with_no_submodule(self):
        a = make_team(self.tmp, "team-a", ["O1"])
        dept = make_department(self.tmp, [a])
        teams_md = dept / "context" / "department" / "teams.md"
        teams_md.write_text(teams_md.read_text() + "| Team X | teams/team-x | Lead |\n")
        findings = [f for f in cascade_check.run_check(dept)["findings"] if f["team"] == "Team X"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["class"], "registered-missing")

    def test_unregistered_present(self):
        a = make_team(self.tmp, "team-a", ["O1"])
        dept = make_department(self.tmp, [a])
        rogue = dept / "teams" / "rogue"
        rogue.mkdir()
        (rogue / "notes.md").write_text("# rogue\n")
        classes = [(f["class"], f["team"]) for f in cascade_check.run_check(dept)["findings"]]
        self.assertIn(("unregistered-present", "rogue"), classes)

    def test_pin_stale(self):
        a = make_team(self.tmp, "team-a", ["O1"])
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        env = {**os.environ, "GIT_AUTHOR_DATE": old, "GIT_COMMITTER_DATE": old}
        _git(a, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "--amend", "--no-edit", env=env)
        dept = make_department(self.tmp, [a], stale_after_days=28)
        result = cascade_check.run_check(dept)
        classes = [f["class"] for f in result["findings"]]
        self.assertIn("pin-stale", classes)
        self.assertGreaterEqual(result["pin_age_days"]["team-a"], 59)

    def test_drift_is_informational_only(self):
        """Drift alone (remote moved past the pin) is not a finding and
        keeps the CLI exit code at 0."""
        a = make_team(self.tmp, "team-a", ["O1"]); b = make_team(self.tmp, "team-b", ["O2.KR1"])
        dept = make_department(self.tmp, [a, b])
        # Advance team-a's origin past what the parent already pinned.
        (a / "context" / "quarterly" / "focus.md").write_text("Serves: O1\n\n# Focus v2\n")
        _git(a, "add", "-A")
        _git(a, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "update")

        result = cascade_check.run_check(dept)
        self.assertEqual(result["findings"], [])
        drift_by_team = {d["team"]: d for d in result["drift"]}
        self.assertIn("team-a", drift_by_team)
        self.assertNotEqual(drift_by_team["team-a"]["pinned"], drift_by_team["team-a"]["remote"])

        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = cascade_check.main(["--json", "--root", str(dept)])
        self.assertEqual(exit_code, 0)

    def test_cli_exit_clean_is_zero(self):
        a = make_team(self.tmp, "team-a", ["O1"]); b = make_team(self.tmp, "team-b", ["O2.KR1"])
        dept = make_department(self.tmp, [a, b])
        result = self._run_cli("--root", str(dept))
        self.assertEqual(result.returncode, 0)

    def test_cli_exit_one_finding_is_one(self):
        a = make_team(self.tmp, "team-a", [])
        dept = make_department(self.tmp, [a])
        result = self._run_cli("--root", str(dept))
        self.assertEqual(result.returncode, 1)

    def test_human_table_prints_dash_not_none_for_department_side_findings(self):
        """`orphaned-objective` findings carry team=None. The human (non-JSON)
        table must print `-` there, never Python's `None`."""
        a = make_team(self.tmp, "team-a", ["O1"])  # O2 goes unserved
        dept = make_department(self.tmp, [a])
        result = self._run_cli("--root", str(dept))
        self.assertEqual(result.returncode, 1)
        self.assertIn("\t-\t", result.stdout)
        self.assertNotIn("None", result.stdout)

    def test_cli_exit_missing_indirection_is_two_with_stderr_error(self):
        empty = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, empty, ignore_errors=True)
        result = self._run_cli("--root", str(empty))
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)


if __name__ == "__main__":
    unittest.main()
