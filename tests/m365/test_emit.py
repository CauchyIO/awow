import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "dist" / "m365" / "appPackage"


def run_gather(*args):
    return subprocess.run(
        [sys.executable, "tools/gather.py", *args],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


class TestEmit(unittest.TestCase):
    def test_emit_then_check_is_clean(self):
        write = run_gather("--surface", "m365")
        self.assertEqual(write.returncode, 0, write.stderr)
        for name in ["manifest.json", "declarativeAgent.json",
                     "fetchAwowContext.plugin.json", "fetchAwowContext.openapi.json",
                     "color.png", "outline.png"]:
            self.assertTrue((PKG / name).is_file(), name)
        da = json.loads((PKG / "declarativeAgent.json").read_text())
        self.assertLessEqual(len(da["instructions"]), 8000)
        check = run_gather("--surface", "m365", "--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        # Regeneration must reproduce exactly the committed bytes — catches a stale
        # committed package (e.g. one regenerated before a routing/config change landed).
        diff = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", "dist/m365"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        self.assertEqual(diff.returncode, 0, diff.stdout + diff.stderr)

    def test_default_surface_untouched_by_m365(self):
        check = run_gather("--check")
        self.assertNotIn("dist/m365", check.stdout)


class TestRefinementPrepIncluded(unittest.TestCase):
    def test_starter_and_routing_present(self):
        da = json.loads((PKG / "declarativeAgent.json").read_text())
        titles = [s["title"] for s in da["conversation_starters"]]
        self.assertIn("Draft a feature for the next refinement", titles)
        self.assertIn(".agents/commands/refinement-prep.md", da["instructions"])


if __name__ == "__main__":
    unittest.main()
