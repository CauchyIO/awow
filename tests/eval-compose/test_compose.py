#!/usr/bin/env python3
"""Behavior tests for scenario fixture composition (world + overlay) and
the duplication guards that keep shared world content from forking back
into per-scenario copies."""
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


validate = load_module("eval_validate_compose", REPO / "evals" / "validate.py")


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


class ComposeFixtureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp))
        self.worlds = self.tmp / "worlds"
        self.scenario = self.tmp / "scenarios" / "s1"
        self.scenario.mkdir(parents=True)

    def compose(self) -> Path:
        dest = self.tmp / "composed"
        validate.compose_fixture(self.scenario, self.worlds, dest)
        return dest

    def test_world_and_overlay_merge(self):
        write_tree(self.worlds / "w", {"context/board.md": "board"})
        (self.scenario / "world.txt").write_text("w\n")
        write_tree(self.scenario / "overlay", {"board/T-1.md": "issue"})
        dest = self.compose()
        self.assertEqual((dest / "context/board.md").read_text(), "board")
        self.assertEqual((dest / "board/T-1.md").read_text(), "issue")

    def test_overlay_wins_on_collision(self):
        write_tree(self.worlds / "w", {"context/board.md": "world version"})
        (self.scenario / "world.txt").write_text("w\n")
        write_tree(self.scenario / "overlay",
                   {"context/board.md": "overlay version"})
        dest = self.compose()
        self.assertEqual((dest / "context/board.md").read_text(),
                         "overlay version")

    def test_no_world_means_overlay_is_whole_tree(self):
        write_tree(self.scenario / "overlay", {"README.md": "greenfield"})
        dest = self.compose()
        self.assertEqual(sorted(p.name for p in dest.iterdir()),
                         ["README.md"])

    def test_missing_world_raises(self):
        (self.scenario / "world.txt").write_text("ghost\n")
        write_tree(self.scenario / "overlay", {"a.md": "x"})
        with self.assertRaises(FileNotFoundError):
            self.compose()


class ValidateWorldTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp))
        self.worlds = self.tmp / "worlds"
        self.scenario = self.tmp / "scenarios" / "s1"
        self.scenario.mkdir(parents=True)

    def test_neither_world_nor_overlay_is_an_error(self):
        errors = validate._validate_world(self.scenario, self.worlds)
        self.assertEqual(len(errors), 1)
        self.assertIn("missing overlay/", errors[0])

    def test_overlay_alone_is_fine(self):
        write_tree(self.scenario / "overlay", {"a.md": "x"})
        self.assertEqual(validate._validate_world(self.scenario, self.worlds),
                         [])

    def test_unresolvable_world_is_an_error(self):
        (self.scenario / "world.txt").write_text("ghost\n")
        errors = validate._validate_world(self.scenario, self.worlds)
        self.assertEqual(len(errors), 1)
        self.assertIn("does not exist", errors[0])

    def test_world_name_with_path_separator_is_an_error(self):
        (self.scenario / "world.txt").write_text("../escape\n")
        errors = validate._validate_world(self.scenario, self.worlds)
        self.assertEqual(len(errors), 1)
        self.assertIn("one world name", errors[0])

    def test_resolvable_world_passes(self):
        write_tree(self.worlds / "w", {"context/board.md": "board"})
        (self.scenario / "world.txt").write_text("w\n")
        self.assertEqual(validate._validate_world(self.scenario, self.worlds),
                         [])


class OverlayDuplicationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.tmp))
        self.worlds = self.tmp / "worlds"
        self.scenarios = self.tmp / "scenarios"

    def scenario(self, name: str, overlay: dict[str, str],
                 world: str | None = None) -> Path:
        s = self.scenarios / name
        s.mkdir(parents=True)
        write_tree(s / "overlay", overlay)
        if world is not None:
            (s / "world.txt").write_text(f"{world}\n")
        return s

    def test_identical_file_across_overlays_is_an_error(self):
        a = self.scenario("a", {"context/labels.md": "same"})
        b = self.scenario("b", {"context/labels.md": "same"})
        errors = validate._validate_overlay_duplication([a, b], self.worlds)
        self.assertEqual(len(errors), 1)
        self.assertIn("move it into a world", errors[0])

    def test_same_path_different_content_is_fine(self):
        a = self.scenario("a", {"context/board.md": "github board"})
        b = self.scenario("b", {"context/board.md": "file board"})
        self.assertEqual(
            validate._validate_overlay_duplication([a, b], self.worlds), [])

    def test_overlay_file_identical_to_world_copy_is_an_error(self):
        write_tree(self.worlds / "w", {"context/labels.md": "same"})
        s = self.scenario("a", {"context/labels.md": "same"}, world="w")
        errors = validate._validate_overlay_duplication([s], self.worlds)
        self.assertEqual(len(errors), 1)
        self.assertIn("delete the overlay file", errors[0])

    def test_overlay_override_of_world_file_is_fine(self):
        write_tree(self.worlds / "w", {"context/labels.md": "world"})
        s = self.scenario("a", {"context/labels.md": "scenario"}, world="w")
        self.assertEqual(
            validate._validate_overlay_duplication([s], self.worlds), [])


class ShippedSuiteCompositionTest(unittest.TestCase):
    """Every shipped scenario must compose, and the world-backed ones must
    inherit the board contract from their world."""

    def test_shipped_scenarios_compose(self):
        scenarios_dir = REPO / "evals" / "scenarios"
        worlds_dir = REPO / "evals" / "worlds"
        for scenario in sorted(p for p in scenarios_dir.iterdir()
                               if p.is_dir()):
            with tempfile.TemporaryDirectory() as td:
                dest = Path(td) / "composed"
                validate.compose_fixture(scenario, worlds_dir, dest)
                self.assertTrue(any(dest.rglob("*")),
                                f"{scenario.name} composed empty")
                if (scenario / "world.txt").is_file():
                    self.assertTrue(
                        (dest / "context" / "tooling" / "board.md").is_file(),
                        f"{scenario.name} lost its world's board contract")


if __name__ == "__main__":
    unittest.main()
