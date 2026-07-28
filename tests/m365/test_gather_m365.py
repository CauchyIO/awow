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


class TestTrackedFilesFiltering(unittest.TestCase):
    """Fix 1: untracked working-tree files must never leak into the emitted package."""

    def _init_repo(self, root: Path) -> None:
        import subprocess
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)

    def _commit(self, root: Path, *rel_paths: str) -> None:
        import subprocess
        subprocess.run(["git", "add", *rel_paths], cwd=root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "add tracked fixture"], cwd=root, check=True)

    def test_tracked_files_none_outside_git_repo(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(gather_m365._tracked_files(Path(td)))

    def test_tracked_files_returns_set_inside_work_tree(self):
        # The is-inside-work-tree probe means the None fallback can never trigger
        # once we're inside a git repo — even one with no commits yet.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._init_repo(root)
            tracked = gather_m365._tracked_files(root)
            self.assertIsNotNone(tracked)
            self.assertEqual(tracked, set())

    def test_tracked_files_lists_committed_paths(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._init_repo(root)
            (root / "tracked.md").write_text("tracked\n")
            self._commit(root, "tracked.md")
            (root / "untracked.md").write_text("untracked\n")
            tracked = gather_m365._tracked_files(root)
            self.assertEqual(tracked, {"tracked.md"})

    def test_included_commands_skips_untracked_command(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._init_repo(root)
            cmds = root / ".agents" / "commands"
            cmds.mkdir(parents=True)
            (cmds / "in.md").write_text(FM)
            self._commit(root, ".agents/commands/in.md")
            # Untracked second command file — should never be discovered.
            (cmds / "out.md").write_text(FM.replace("Draft a feature", "B feature"))
            entries = gather_m365.included_commands(root)
            self.assertEqual([e.name for e in entries], ["in"])

    def test_build_file_index_skips_untracked_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._init_repo(root)
            team = root / "context" / "team"
            team.mkdir(parents=True)
            (team / "tracked.md").write_text("# Tracked\n\nbody\n")
            self._commit(root, "context/team/tracked.md")
            (team / "untracked.md").write_text("# Untracked\n\nbody\n")
            index = gather_m365.build_file_index(root, ("context/team",))
            paths = [p for p, _ in index]
            self.assertEqual(paths, ["context/team/tracked.md"])

    def test_non_git_directory_still_includes_all_fixtures(self):
        # Confirms the existing (non-git temp-dir) fixtures in TestIncludedCommands and
        # TestIndexAndInstructions are unaffected: no tracked set means no filtering.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cmds = root / ".agents" / "commands"
            cmds.mkdir(parents=True)
            (cmds / "in.md").write_text(FM)
            entries = gather_m365.included_commands(root)
            self.assertEqual([e.name for e in entries], ["in"])


class TestIndexAndInstructions(unittest.TestCase):
    def _cfg(self, **over):
        base = dict(
            agent_name="awow Coach", agent_description="d", github_repo="o/r",
            ref="main", explore_starter="Explore awow",
            index_roots=("context/team",), identity="You are the awow Coach.",
        )
        base.update(over)
        return gather_m365.M365Config(**base)

    def test_index_walks_roots(self):
        index = gather_m365.build_file_index(REPO_ROOT, ("context/team",))
        paths = [p for p, _ in index]
        self.assertIn("context/team/mission.md", paths)
        self.assertEqual(paths, sorted(paths))
        for _, desc in index:
            self.assertNotIn("\n", desc)

    def test_assembles_within_budget(self):
        cmd = gather_m365.CommandEntry("refinement-prep", ".agents/commands/refinement-prep.md", "Draft a feature", "draft a feature")
        text = gather_m365.assemble_instructions(self._cfg(), [cmd], [("context/team/mission.md", "the mission")])
        self.assertIn("You are the awow Coach.", text)
        self.assertIn('"Draft a feature" -> fetch .agents/commands/refinement-prep.md', text)
        self.assertIn("context/team/mission.md — the mission", text)
        self.assertLessEqual(len(text), gather_m365.INSTRUCTION_BUDGET)

    def test_over_budget_fails_loud(self):
        huge = [(f"context/x/file{i}.md", "y" * 200) for i in range(200)]
        with self.assertRaises(gather_m365.M365BudgetError):
            gather_m365.assemble_instructions(self._cfg(), [], huge)


class TestJsonBuilders(unittest.TestCase):
    def _cfg(self):
        return gather_m365.M365Config(
            agent_name="awow Coach", agent_description="d", github_repo="CauchyIO/awow",
            ref="main", explore_starter="Explore awow",
            index_roots=("context/team",), identity="id",
        )

    def test_declarative_agent_shape(self):
        cmd = gather_m365.CommandEntry("refinement-prep", ".agents/commands/refinement-prep.md", "Draft a feature", "d")
        da = gather_m365.build_declarative_agent(self._cfg(), "INSTR", [cmd])
        self.assertEqual(da["$schema"], "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.7/schema.json")
        self.assertEqual(da["version"], "v1.7")
        self.assertEqual(da["instructions"], "INSTR")
        titles = [s["title"] for s in da["conversation_starters"]]
        self.assertEqual(titles, ["Explore awow", "Draft a feature"])
        self.assertEqual(da["actions"], [{"id": "awowFetch", "file": "fetchAwowContext.plugin.json"}])

    def test_teams_manifest_structure(self):
        manifest = gather_m365.build_teams_manifest(self._cfg())
        self.assertEqual(manifest["$schema"], "https://developer.microsoft.com/json-schemas/teams/v1.19/MicrosoftTeams.schema.json")
        self.assertEqual(manifest["manifestVersion"], "1.19")
        self.assertEqual(manifest["icons"], {"color": "color.png", "outline": "outline.png"})
        self.assertEqual(manifest["copilotAgents"]["declarativeAgents"][0]["file"], "declarativeAgent.json")
        # Verify ID is stable
        a = gather_m365.build_teams_manifest(self._cfg())["id"]
        b = gather_m365.build_teams_manifest(self._cfg())["id"]
        self.assertEqual(a, b)

    def test_build_plugin_manifest(self):
        cfg = self._cfg()
        pm = gather_m365.build_plugin_manifest(cfg)
        self.assertEqual(pm["$schema"], "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.3/schema.json")
        self.assertEqual(pm["schema_version"], "v2.3")
        self.assertEqual(pm["namespace"], "awowfetch")
        self.assertEqual(pm["functions"][0]["name"], "fetchAwowContext")
        self.assertEqual(pm["runtimes"][0]["spec"]["url"], "fetchAwowContext.openapi.json")
        self.assertEqual(pm["runtimes"][0]["auth"], {"type": "None"})

    def test_openapi_targets_raw_githubusercontent(self):
        cfg = self._cfg()
        spec = gather_m365.build_openapi_spec(cfg)
        self.assertEqual(spec["openapi"], "3.0.1")
        self.assertEqual(spec["servers"], [{"url": "https://raw.githubusercontent.com"}])
        path = "/CauchyIO/awow/main/{filePath}"
        self.assertIn(path, spec["paths"])
        op = spec["paths"][path]["get"]
        self.assertEqual(op["operationId"], "fetchAwowContext")
        # Only one parameter: filePath. No ref query param, no Accept header param.
        self.assertEqual(len(op["parameters"]), 1)
        self.assertEqual(op["parameters"][0]["name"], "filePath")
        self.assertIn("%2F", op["parameters"][0]["description"])

    def test_dump_json_deterministic(self):
        obj = {"b": 1, "a": [1, 2]}
        self.assertEqual(gather_m365.dump_json(obj), gather_m365.dump_json(obj))
        self.assertTrue(gather_m365.dump_json(obj).endswith("\n"))


class TestIcons(unittest.TestCase):
    def _size(self, data: bytes) -> tuple[int, int]:
        import struct
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        w, h = struct.unpack(">II", data[16:24])
        return w, h

    def test_icons_exist_with_required_sizes(self):
        assets = REPO_ROOT / "context" / "tooling" / "m365" / "assets"
        self.assertEqual(self._size((assets / "color.png").read_bytes()), (192, 192))
        self.assertEqual(self._size((assets / "outline.png").read_bytes()), (32, 32))


if __name__ == "__main__":
    unittest.main()
