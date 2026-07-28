"""Regression test for orphan detection across BOTH generated payload roots.

find_orphans applies two different rules. Under a fully-generated payload root
every unplanned file is an orphan; everywhere else only files carrying the
GENERATED header are, so user-authored files are never deleted.

Before this test the rule was selected by `if surface == DIST_DIR` — an
identity check against one path. The second payload root, dist-telemetry/, fell
through to the marker branch, and full-copy payload content carries NO marker
(plugin_command_copy, command_skill_stub, and skill_stubs all emit source
bodies verbatim). A stale file there would therefore be undetected, never
removed, still published, and `gather.py --check` would stay green. That is a
silent-corruption failure with no visible symptom, which is why it gets its own
test rather than a line in the split suite.

Four assertions:
  1. Both payload roots are registered as fully generated.
  2. A markerless probe under dist-telemetry/ IS reported as an orphan.
  3. The same probe under .claude/ is NOT — the fully-generated rule stays
     scoped, so a user file outside the payload is still safe.
  4. Real payload content carries no marker, which is the premise that makes
     assertion 2 load-bearing rather than incidental.

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
    "# orphan probe\n\nFull-copy payload shape: deliberately carries no "
    "GENERATED header, exactly like every real payload file.\n"
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

    # 4. Premise: real payload content carries no marker.
    sample = gather.DIST_DIR / "commands" / "setup-awow.md"
    if sample.is_file() and gather.GENERATED_MARKER in sample.read_text():
        FAILURES.append(
            f"{sample} carries the GENERATED marker — the marker branch would "
            "have caught payload orphans after all, so this test's premise is stale."
        )

    # 2. Markerless probe under the telemetry payload root IS an orphan.
    tele_probe = getattr(gather, "DIST_TELEMETRY_DIR", REPO_ROOT / "dist-telemetry")
    tele_probe = tele_probe / "skills" / "_orphan-probe" / "SKILL.md"
    created = make_probe(tele_probe)
    try:
        if gather.GENERATED_MARKER in tele_probe.read_text():
            FAILURES.append("probe body accidentally contains the GENERATED marker")
        found = gather.find_orphans(set(), [tele_probe.parents[2]])
        if tele_probe not in found:
            FAILURES.append(
                f"{tele_probe.relative_to(REPO_ROOT)} was NOT reported as an orphan — "
                "dist-telemetry/ is not being treated as a fully generated root."
            )
    finally:
        remove_probe(tele_probe, created)

    # 3. The same probe under .claude/ is NOT an orphan.
    claude_probe = gather.CLAUDE_DIR / "skills" / "_orphan-probe" / "SKILL.md"
    created = make_probe(claude_probe)
    try:
        found = gather.find_orphans(set(), [gather.CLAUDE_DIR])
        if claude_probe in found:
            FAILURES.append(
                f"{claude_probe.relative_to(REPO_ROOT)} WAS reported as an orphan — "
                "the fully-generated rule leaked outside the payload roots, so a "
                "user-authored file under .claude/ would be deleted."
            )
    finally:
        remove_probe(claude_probe, created)

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Orphan detection covers both payload roots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
