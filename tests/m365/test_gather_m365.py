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


if __name__ == "__main__":
    unittest.main()
