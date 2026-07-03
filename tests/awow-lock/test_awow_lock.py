"""Regression test for tools/awow_lock.py — the 3-way update engine behind
`/update-awow`.

Builds two throwaway git repos (an upstream `src` and a local `tgt`), seeds a
baseline, then diverges them so that every classification verdict is exercised
at once:

    a.md  upstream changed, local didn't      -> update
    b.md  local changed, upstream didn't       -> keep-local
    c.md  both changed differently             -> conflict (write .awow)
    d.md  nobody changed                       -> skip
    e.md  local deleted                        -> removed-local (not re-added)
    f.md  upstream added                        -> new

Then asserts `apply` overwrites only what it should, never clobbers a local
edit, writes the conflict sidecar, bumps the recorded version, and converges
(a second plan is a no-op). Pure stdlib + git; no pytest, no network.

Run:  python3 tests/awow-lock/test_awow_lock.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCK_TOOL = REPO_ROOT / "tools" / "awow_lock.py"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd),
         "-c", "user.email=t@t", "-c", "user.name=t",
         "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, text=True,
    )


def _lock(root: Path, *args: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(LOCK_TOOL), "--root", str(root), *args],
        check=True, capture_output=True, text=True,
    )
    return proc.stdout


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _seed_repo(root: Path, version: str) -> None:
    for name in "abcde":
        _write(root / ".agents" / "commands" / f"{name}.md", f"orig {name}\n")
    _write(root / ".claude-plugin" / "plugin.json",
           json.dumps({"name": "awow", "version": version}) + "\n")
    _write(root / "tools" / "gather.py", "print('gather')\n")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "init")


class AwowLockThreeWay(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.src = base / "src"
        self.tgt = base / "tgt"
        self.src.mkdir()
        self.tgt.mkdir()

        _seed_repo(self.src, "0.1.0")
        _seed_repo(self.tgt, "0.1.0")

        # Baseline captured while local == upstream.
        _lock(self.tgt, "backfill")

        # Upstream moves to 0.2.0: change a, change c, add f.
        _write(self.src / ".claude-plugin" / "plugin.json",
               json.dumps({"name": "awow", "version": "0.2.0"}) + "\n")
        _write(self.src / ".agents" / "commands" / "a.md", "UPSTREAM a\n")
        _write(self.src / ".agents" / "commands" / "c.md", "UPSTREAM c\n")
        _write(self.src / ".agents" / "commands" / "f.md", "brand new f\n")
        _git(self.src, "add", "-A")
        _git(self.src, "commit", "-qm", "v0.2.0")

        # Local edits: change b, change c differently, delete e.
        _write(self.tgt / ".agents" / "commands" / "b.md", "LOCAL b\n")
        _write(self.tgt / ".agents" / "commands" / "c.md", "LOCAL c\n")
        (self.tgt / ".agents" / "commands" / "e.md").unlink()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _verdicts(self) -> dict:
        plan = json.loads(_lock(self.tgt, "status", "--source", str(self.src), "--json"))
        return plan, {e["rel"]: e["verdict"] for e in plan["entries"]}

    def test_plan_classifies_every_verdict(self) -> None:
        plan, v = self._verdicts()
        self.assertEqual(plan["from_version"], "0.1.0")
        self.assertEqual(plan["to_version"], "0.2.0")
        cmd = ".agents/commands"
        self.assertEqual(v[f"{cmd}/a.md"], "update")
        self.assertEqual(v[f"{cmd}/b.md"], "keep-local")
        self.assertEqual(v[f"{cmd}/c.md"], "conflict")
        self.assertEqual(v[f"{cmd}/d.md"], "skip")
        self.assertEqual(v[f"{cmd}/e.md"], "removed-local")
        self.assertEqual(v[f"{cmd}/f.md"], "new")

    def test_apply_reconciles_without_clobbering(self) -> None:
        result = json.loads(_lock(self.tgt, "apply", "--source", str(self.src), "--json"))
        cmd = self.tgt / ".agents" / "commands"

        # upstream taken where local was untouched
        self.assertEqual((cmd / "a.md").read_text(), "UPSTREAM a\n")
        # new file added
        self.assertEqual((cmd / "f.md").read_text(), "brand new f\n")
        # local edits NEVER overwritten
        self.assertEqual((cmd / "b.md").read_text(), "LOCAL b\n")
        self.assertEqual((cmd / "c.md").read_text(), "LOCAL c\n")
        # conflict surfaced as a sidecar carrying the upstream version
        self.assertEqual((cmd / "c.md.awow").read_text(), "UPSTREAM c\n")
        # locally-deleted file stays deleted
        self.assertFalse((cmd / "e.md").exists())
        # version bumped in the reconciled lock
        self.assertEqual(result["to_version"], "0.2.0")
        lock = json.loads((self.tgt / "tools" / "awow.lock.json").read_text())
        self.assertEqual(lock["awow_version"], "0.2.0")

    def test_apply_is_idempotent(self) -> None:
        _lock(self.tgt, "apply", "--source", str(self.src), "--json")
        plan, v = self._verdicts()
        # converged: no more work, version matches
        self.assertEqual(plan["from_version"], plan["to_version"])
        verdicts = set(v.values())
        self.assertNotIn("update", verdicts)
        self.assertNotIn("new", verdicts)
        self.assertNotIn("conflict", verdicts)


if __name__ == "__main__":
    unittest.main(verbosity=2)
