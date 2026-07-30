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

Six assertions:
  1. Both payload roots are registered as fully generated.
  2. A markerless probe under dist-telemetry/ IS reported as an orphan.
  3. The same probe under .claude/ is NOT — the fully-generated rule stays
     scoped, so a user file outside the payload is still safe.
  4. Real payload content carries no marker, which is the premise that makes
     assertion 2 load-bearing rather than incidental.
  5. AWOW-62: a nested git checkout under a surface — e.g. a Claude Code
     worktree at .claude/worktrees/<name>/, whose .git is a FILE, not a
     directory — must never be swept for orphans, even though a worktree is
     a full checkout of this repo and therefore contains files that
     legitimately carry the GENERATED marker. A non---check gather run once
     walked into three live worktrees this way and deleted 283 tracked
     files.
  6. The nested-checkout guard must not blind the sweep entirely: a genuine
     orphan outside the nested checkout is still caught.

Pure stdlib; no pytest, no network. Creates and removes one probe file under
each root; leaves no directory it did not find. Assertions 5/6 use their own
throwaway temp directory rather than a real repo path, since they must
exercise a directory the guard is specifically meant to protect and must not
risk touching this repo's actual .claude/worktrees/ checkouts.

Run:  python3 tests/telemetry-split/test_orphan_roots.py
Also collectible by pytest, via test_nested_checkout_guard() below.
"""
from __future__ import annotations

import importlib
import sys
import tempfile
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


def check_nested_checkout_guard() -> list:
    """Assertions 5 & 6 (AWOW-62). Builds a throwaway temp tree shaped like
    the real incident: `<surface>/worktrees/<name>/.git` as a FILE (exactly
    how a Claude Code / git worktree checkout looks), holding a file that
    carries the GENERATED marker — plausible, since a worktree is a full
    checkout of this repo and its own generated stubs carry that marker too.
    A genuine orphan sits directly under the surface, outside the nested
    checkout. Returns a list of failure strings (empty means the guard is
    correct); shared by main()'s script-mode run and by the pytest wrapper
    below so both invocation paths exercise the same check."""
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        surface = Path(tmp) / "surface"

        nested_file = surface / "worktrees" / "probe-worktree" / "commands" / "some-command.md"
        nested_file.parent.mkdir(parents=True)
        (nested_file.parent.parent / ".git").write_text(
            "gitdir: /elsewhere/.git/worktrees/probe-worktree\n"
        )
        nested_file.write_text(gather.GENERATED_MARKER + " -->\nnested checkout content\n")

        real_orphan = surface / "commands" / "stale.md"
        real_orphan.parent.mkdir(parents=True)
        real_orphan.write_text(gather.GENERATED_MARKER + " -->\nstale content\n")

        found = gather.find_orphans(set(), [surface])

        if nested_file in found:
            failures.append(
                f"{nested_file.relative_to(tmp)} WAS reported as an orphan — the "
                "sweep descended into a nested git checkout (.git as a file) and "
                "would delete tracked worktree content (AWOW-62 regression)."
            )
        if real_orphan not in found:
            failures.append(
                f"{real_orphan.relative_to(tmp)} was NOT reported as an orphan — "
                "the nested-checkout guard is over-broad and disabled the sweep "
                "outside the nested checkout too."
            )
    return failures


def test_nested_checkout_guard() -> None:
    """pytest entry point for assertions 5 & 6. This file's own convention
    (module-level FAILURES list + main(), no pytest) is what CI actually
    invokes (`python3 tests/telemetry-split/test_orphan_roots.py`,
    .github/workflows/ci.yml), and pytest cannot collect anything from a
    plain main()/FAILURES script — there is no test_*() function for it to
    find. This thin wrapper calls the same check function so `pytest -q`
    over this directory also has a real, collectible signal."""
    failures = check_nested_checkout_guard()
    assert not failures, "\n".join(failures)


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

    # 5 & 6. Nested git checkouts under a surface are never swept; a genuine
    # orphan outside one is still caught.
    FAILURES.extend(check_nested_checkout_guard())

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Orphan detection covers both payload roots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
