"""Regression test for orphan detection across BOTH generated payload roots.

Every payload root is wholly generated: any unplanned file under it is an
orphan, removed on apply and reported by `--check`. Payload content carries no
marker of its own (plugin_command_copy, command_skill_stub, and skill_stubs all
emit source bodies verbatim), so the sweep has nothing but the plan to go on —
a root left out of GENERATED_ROOTS would have its stale files silently kept,
still published, with `gather.py --check` green. That is a silent-corruption
failure with no visible symptom, which is why it gets its own test rather than
a line in the split suite.

Three assertions:
  1. Both payload roots are registered as fully generated.
  2. An unplanned probe under dist-telemetry/ IS reported as an orphan.
  3. A file inside a nested git checkout under a payload root is NOT — the
     sweep never crosses into another checkout's tracked files (AWO-62).

Pure stdlib; no pytest, no network. Creates and removes one probe file under
each root; leaves no directory it did not find.

Run:  python3 tests/telemetry-split/test_orphan_roots.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

FAILURES = []

PROBE_BODY = (
    "---\nname: orphan-probe\ndescription: \"not a real skill\"\n---\n\n"
    "# orphan probe\n\nFull-copy payload shape, exactly like every real "
    "payload file.\n"
)


def make_probe(path: Path):
    """Create `path` and return the directories that had to be created, deepest
    first, so the caller can remove exactly what it added."""
    created = []
    d = path.parent
    while not d.exists():
        created.append(d)
        d = d.parent
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(PROBE_BODY)
    return created


def remove_probe(path: Path, created) -> None:
    path.unlink(missing_ok=True)
    for d in created:
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()


def main() -> int:
    # 1. Both payload roots registered.
    roots = tuple(getattr(gather, "GENERATED_ROOTS", ()))
    for want in (gather.DIST_DIR, getattr(gather, "DIST_TELEMETRY_DIR", None)):
        if want is None or want not in roots:
            FAILURES.append(
                f"GENERATED_ROOTS is {[str(r) for r in roots]} — missing {want}. "
                "A payload root outside this set has its orphans silently ignored."
            )

    # 2. Unplanned probe under the telemetry payload root IS an orphan.
    tele_probe = getattr(gather, "DIST_TELEMETRY_DIR", REPO_ROOT / "dist-telemetry")
    tele_probe = tele_probe / "skills" / "_orphan-probe" / "SKILL.md"
    created = make_probe(tele_probe)
    try:
        found = gather.find_orphans(set(), [tele_probe.parents[2]])
        if tele_probe not in found:
            FAILURES.append(
                f"{tele_probe.relative_to(REPO_ROOT)} was NOT reported as an orphan — "
                "dist-telemetry/ is not being treated as a fully generated root."
            )
    finally:
        remove_probe(tele_probe, created)

    # 3. A file inside a nested git checkout is NOT an orphan, even under a
    #    fully-generated payload root where every unplanned file otherwise is.
    #    A linked worktree is a copy of this repo; sweeping it destroys tracked
    #    files in another checkout and fails --check on paths this run does not
    #    own (AWO-62).
    nested = gather.DIST_DIR / "_probe-worktree"
    nested_file = nested / "commands" / "probe.md"
    created = make_probe(nested_file)
    (nested / ".git").write_text("gitdir: /elsewhere/.git/worktrees/probe\n")
    try:
        found = gather.find_orphans(set(), [gather.DIST_DIR])
        if nested_file in found:
            FAILURES.append(
                f"{nested_file.relative_to(REPO_ROOT)} WAS reported as an orphan — "
                "the sweep crosses into nested git worktrees and would delete "
                "their tracked files (AWO-62)."
            )
    finally:
        (nested / ".git").unlink(missing_ok=True)
        remove_probe(nested_file, created)
        if nested.is_dir() and not any(nested.iterdir()):
            nested.rmdir()

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Orphan detection covers both payload roots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
