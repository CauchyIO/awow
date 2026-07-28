"""Regression test for setup/awowify.sh's --layer trimming (Task 5).

Files tagged `layer: team` or `layer: department` in frontmatter ship only
in the matching install profile; untagged files ship in both. The default
(no --layer flag) install is the team profile — existing installs see zero
behavior change, and this suite asserts that explicitly.

The two files this task tags (process-workitem.md, refinement-prep.md) are
the only real `layer: team` files that exist yet; the department command
and department-coach skill (Tasks 6-7) do not exist yet. So this test seeds
a copy of the real .agents/ tree with tiny synthetic `layer: department`
fixtures — one flat command, one flat declarative skill, one directory
skill (whose layer must be read from its SKILL.md, not from its sibling
resource file, which carries no frontmatter at all) — and asserts on those
plus the two real team-tagged files.

Run:  uv run python -m unittest tests/department/test_awowify_layers.py -v
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AWOWIFY = REPO_ROOT / "setup" / "awowify.sh"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class TestAwowifyLayers(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.source = self._make_source()

    def _make_source(self) -> Path:
        """A copy of the real .agents/ tree, plus tiny synthetic fixtures.

        Copying the real tree means the two real team-tagged files and
        every untagged command are exercised exactly as they ship. awowify's
        vendor-stamp step reads $SOURCE/.claude-plugin/plugin.json under
        `set -e -o pipefail`; without it the whole run exits 1 even though
        every file copy already succeeded, so a minimal stub goes in too.
        """
        source = self.tmp / "source"
        shutil.copytree(REPO_ROOT / ".agents", source / ".agents")
        _write(source / ".claude-plugin" / "plugin.json", '{"version": "0.0.0-test"}\n')

        _write(
            source / ".agents" / "commands" / "zz-synthetic-department-cmd.md",
            '---\ndescription: "synthetic fixture"\nlayer: department\n---\n\n# fixture\n',
        )
        _write(
            source / ".agents" / "skills" / "zz-synthetic-department-skill.md",
            "---\nname: zz-synthetic-department-skill\n"
            'description: "synthetic fixture"\nlayer: department\n---\n\nfixture\n',
        )
        _write(
            source / ".agents" / "skills" / "zz-synthetic-department-dirskill" / "SKILL.md",
            "---\nname: zz-synthetic-department-dirskill\n"
            'description: "synthetic fixture"\nlayer: department\n---\n\nfixture\n',
        )
        _write(
            source / ".agents" / "skills" / "zz-synthetic-department-dirskill" / "reference.md",
            "no frontmatter here\n",
        )
        return source

    def _run(self, target: Path, *extra_args: str) -> subprocess.CompletedProcess:
        target.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["bash", str(AWOWIFY), "--source", str(self.source), "--target", str(target), *extra_args],
            capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"awowify.sh failed (exit {result.returncode}):\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        return result

    # -- default install (no --layer) is the team profile -------------------

    def test_default_install_is_team_profile(self):
        target = self.tmp / "team-target"
        self._run(target)

        commands = target / ".agents" / "commands"
        skills = target / ".agents" / "skills"

        # Real team-tagged commands ship by default — zero behavior change:
        # they shipped before this task tagged them, and still ship now.
        self.assertTrue((commands / "process-workitem.md").is_file())
        self.assertTrue((commands / "refinement-prep.md").is_file())
        # Untagged commands ship in every profile.
        self.assertTrue((commands / "daily-digest.md").is_file())
        # Department-tagged files are trimmed from the team profile.
        self.assertFalse((commands / "zz-synthetic-department-cmd.md").exists())
        self.assertFalse((skills / "zz-synthetic-department-skill.md").exists())
        self.assertFalse((skills / "zz-synthetic-department-dirskill").exists())

    def test_no_flag_matches_explicit_layer_team(self):
        """Omitting --layer is identical to passing --layer team."""
        implicit = self.tmp / "implicit"
        explicit = self.tmp / "explicit"
        self._run(implicit)
        self._run(explicit, "--layer", "team")

        implicit_files = sorted(str(p.relative_to(implicit)) for p in implicit.rglob("*") if p.is_file())
        explicit_files = sorted(str(p.relative_to(explicit)) for p in explicit.rglob("*") if p.is_file())
        self.assertEqual(implicit_files, explicit_files)

    # -- --layer department ---------------------------------------------------

    def test_department_layer_includes_department_excludes_team(self):
        target = self.tmp / "dept-target"
        self._run(target, "--layer", "department")

        commands = target / ".agents" / "commands"
        skills = target / ".agents" / "skills"

        # Department-tagged files ship.
        self.assertTrue((commands / "zz-synthetic-department-cmd.md").is_file())
        self.assertTrue((skills / "zz-synthetic-department-skill.md").is_file())
        self.assertTrue((skills / "zz-synthetic-department-dirskill" / "SKILL.md").is_file())
        # The whole directory skill ships with it — its layer comes from
        # SKILL.md, but sibling resource files (no frontmatter) ride along.
        self.assertTrue((skills / "zz-synthetic-department-dirskill" / "reference.md").is_file())
        # Untagged commands still ship.
        self.assertTrue((commands / "daily-digest.md").is_file())
        # Team-tagged commands are excluded from the department profile.
        self.assertFalse((commands / "process-workitem.md").exists())
        self.assertFalse((commands / "refinement-prep.md").exists())

    def test_invalid_layer_value_rejected(self):
        target = self.tmp / "bad-layer"
        target.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["bash", str(AWOWIFY), "--source", str(self.source), "--target", str(target),
             "--layer", "bogus"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be one of team, department", result.stderr)


if __name__ == "__main__":
    unittest.main()
