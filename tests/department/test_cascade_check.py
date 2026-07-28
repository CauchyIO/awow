import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import cascade_check  # noqa: E402

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


def _git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def make_team(base: Path, name: str, serves: list[str]) -> Path:
    repo = base / name
    (repo / "context" / "quarterly").mkdir(parents=True)
    (repo / "context" / "company").mkdir(parents=True)
    lines = "".join(f"Serves: {s}\n" for s in serves)
    (repo / "context" / "quarterly" / "focus.md").write_text(lines + "\n# Focus\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    _git(repo, "add", "-A"); _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


def make_department(base: Path, teams: list[Path]) -> Path:
    dept = base / "dept"
    (dept / "context" / "department").mkdir(parents=True)
    (dept / "context" / "tooling").mkdir(parents=True)
    (dept / "context" / "tooling" / "department.md").write_text(
        "---\nteams_root: teams\nread_scope: context/team, context/quarterly, context/company\n"
        "decisions_dir: context/department/decisions\nstale_after_days: 28\n---\n")
    rows = "\n".join(f"| {t.name} | teams/{t.name} | Lead |" for t in teams)
    (dept / "context" / "department" / "teams.md").write_text(
        "| Team | Path | Lead |\n|---|---|---|\n" + rows + "\n")
    (dept / "context" / "department" / "okrs-2026-Q3.md").write_text(
        "## O1 — Alpha\n- O1.KR1: x\n## O2 — Beta\n- O2.KR1: y\n")
    subprocess.run(["git", "init", "-q", str(dept)], check=True)
    # The dept's own origin must match what the backlink `parent:` claims, or
    # every team would fail backlink-mismatch even on an otherwise-clean setup.
    # Compute it once and reuse it for both the remote and the backlinks.
    origin_url = f"file://{dept}"
    _git(dept, "remote", "add", "origin", origin_url)
    for t in teams:
        _git(dept, "-c", "protocol.file.allow=always", "submodule", "add", "-q", f"file://{t}", f"teams/{t.name}")
        backlink = dept / "teams" / t.name / "context" / "company" / "department.md"
        backlink.parent.mkdir(parents=True, exist_ok=True)
        backlink.write_text(f"---\ndepartment: Dept\nparent: {origin_url}\n---\n")
    _git(dept, "add", "-A"); _git(dept, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return dept


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


if __name__ == "__main__":
    unittest.main()
