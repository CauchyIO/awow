import sys
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

    def test_okr_ids(self):
        ids = cascade_check.parse_okr_ids(OKRS)
        self.assertEqual(ids, {"O1", "O1.KR1", "O1.KR2", "O2", "O2.KR1"})

    def test_serves_headers(self):
        text = "Serves: O1\nServes: O2.KR1\n\n# Quarter focus\nServes: O9 (ignored, not leading)\n"
        self.assertEqual(cascade_check.parse_serves_headers(text), ["O1", "O2.KR1"])

    def test_serves_none(self):
        self.assertEqual(cascade_check.parse_serves_headers("# Just notes\n"), [])


if __name__ == "__main__":
    unittest.main()
