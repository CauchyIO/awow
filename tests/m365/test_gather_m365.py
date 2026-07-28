import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import gather_m365  # noqa: E402


class TestLoadConfig(unittest.TestCase):
    def test_loads_repo_config(self):
        cfg = gather_m365.load_config(REPO_ROOT)
        self.assertEqual(cfg.github_repo, "CauchyIO/awow")
        self.assertEqual(cfg.ref, "main")
        self.assertTrue(cfg.agent_name)
        self.assertTrue(cfg.agent_description)
        self.assertTrue(cfg.explore_starter)
        self.assertIn("context/team", cfg.index_roots)
        self.assertIn("board systems are not connected", cfg.identity.lower())

    def test_missing_config_fails_loud(self):
        with self.assertRaises(gather_m365.M365ConfigError):
            gather_m365.load_config(Path("/nonexistent"))


FM = """---
phase: seed
m365:
  include: true
  conversation_starter: "Draft a feature"
removes_pain: "x"
---

# /demo — a demo command
"""


class TestM365Block(unittest.TestCase):
    def test_parses_block(self):
        block = gather_m365.parse_m365_block(FM)
        self.assertEqual(block, {"include": True, "conversation_starter": "Draft a feature"})

    def test_absent_block_is_none(self):
        self.assertIsNone(gather_m365.parse_m365_block("---\nphase: seed\n---\n\nbody\n"))

    def test_include_false(self):
        text = FM.replace("include: true", "include: false")
        self.assertFalse(gather_m365.parse_m365_block(text)["include"])


class TestIncludedCommands(unittest.TestCase):
    def test_discovers_only_included(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cmds = root / ".agents" / "commands"
            cmds.mkdir(parents=True)
            (cmds / "in.md").write_text(FM)
            (cmds / "out.md").write_text("---\nphase: seed\n---\n\n# /out — excluded\n")
            (cmds / "README.md").write_text("# readme\n")
            entries = gather_m365.included_commands(root)
            self.assertEqual([e.name for e in entries], ["in"])
            self.assertEqual(entries[0].rel_path, ".agents/commands/in.md")
            self.assertEqual(entries[0].starter, "Draft a feature")
            self.assertEqual(entries[0].description, "a demo command")

    def test_sorted_by_name_not_path(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cmds = root / ".agents" / "commands"
            (cmds / "zzzdir").mkdir(parents=True)
            # Create nested aaa.md (would sort last if sorted by path)
            (cmds / "zzzdir" / "aaa.md").write_text(FM)
            # Create top-level bbb.md and ccc.md (would sort first/second if sorted by path)
            (cmds / "bbb.md").write_text(FM.replace("Draft a feature", "B feature"))
            (cmds / "ccc.md").write_text(FM.replace("Draft a feature", "C feature"))
            entries = gather_m365.included_commands(root)
            # Should be sorted by name: aaa, bbb, ccc (not by path: bbb, ccc, aaa)
            self.assertEqual([e.name for e in entries], ["aaa", "bbb", "ccc"])

    def test_include_true_without_starter_fails_loud(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cmds = root / ".agents" / "commands"
            cmds.mkdir(parents=True)
            # include: true but no conversation_starter
            no_starter = """---
phase: seed
m365:
  include: true
---

# /bad — no starter
"""
            (cmds / "bad.md").write_text(no_starter)
            with self.assertRaises(gather_m365.M365ConfigError) as ctx:
                gather_m365.included_commands(root)
            self.assertIn("conversation_starter is missing", str(ctx.exception))

    def test_non_canonical_include_value_fails_loud(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cmds = root / ".agents" / "commands"
            cmds.mkdir(parents=True)
            # include: True (capitalized, not converted to bool)
            bad_bool = """---
phase: seed
m365:
  include: True
  conversation_starter: "Feature"
---

# /bad — bad bool
"""
            (cmds / "bad.md").write_text(bad_bool)
            with self.assertRaises(gather_m365.M365ConfigError) as ctx:
                gather_m365.included_commands(root)
            self.assertIn("m365.include must be true or false", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
