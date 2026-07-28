"""Regression test for the payload classification in tools/gather.py.

The predicate (design spec section 4.1.2): a file under context/ ships if a
default exists that is useful before /setup-awow runs. Contract files are
identical for every adopter; template files ship a working default that
/setup-awow tunes; team data has no meaningful default, and a generic stub is
worse than absence because commands can branch on absence.

Asserts three things: every path under context/ is classified, the two
manifests never overlap, and a representative sample lands in the right class.

Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-classification/test_classification.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import importlib

gather = importlib.import_module("gather")

FAILURES = []

# Representative sample. Not exhaustive — the unclassified check covers the rest.
EXPECTED = {
    # contract: identical for everyone
    "tooling/boards/linear/reference/states.md": "payload",
    "tooling/boards/github-issues/reference/hierarchy.md": "payload",
    "tooling/activity-collection.md": "payload",
    "tooling/harnesses/codex.md": "payload",
    "knowledge-base/mining.md": "payload",
    "knowledge-base/synthesis.md": "payload",
    "kb-inbox/README.md": "payload",
    "retros/canon.md": "payload",
    "retros/anti-patterns.md": "payload",
    # template: ships a working default, /setup-awow tunes it
    "knowledge-base/mining-policy.md": "payload",
    "tooling/knowledge-base.md": "payload",
    "tooling/design-system.md": "payload",
    # team data: no useful default
    "team/mission.md": "team-data",
    "team/members.md": "team-data",
    "team/vision.md": "team-data",
    "team/conventions/REQUIRED/branches.md": "team-data",
    "team/style/prose.md": "team-data",
    "company/stakeholders.md": "team-data",
    "tooling/board.md": "team-data",
    "tooling/architecture.md": "team-data",
    "knowledge-base/glossary.md": "team-data",
    "kb-inbox/_synthesis-log.md": "team-data",
    "quarterly/INPUT.md": "team-data",
}


def main() -> int:
    for rel, want in sorted(EXPECTED.items()):
        got = gather.classify_context_path(rel)
        if got != want:
            FAILURES.append(f"classify({rel!r}) == {got!r}, expected {want!r}")

    # Every real path under context/ must be classified.
    stray = gather.unclassified_context_paths()
    if stray:
        FAILURES.append(
            "unclassified path(s) under context/ — add each to "
            "PAYLOAD_CONTEXT_PATHS or TEAM_DATA_CONTEXT_PATHS:\n    "
            + "\n    ".join(stray)
        )

    # The two manifests must be disjoint; an overlap makes classification
    # order-dependent and therefore silently wrong.
    overlap = set(gather.PAYLOAD_CONTEXT_PATHS) & set(gather.TEAM_DATA_CONTEXT_PATHS)
    if overlap:
        FAILURES.append(f"path(s) in both manifests: {sorted(overlap)}")

    # Bidirectional: the built payload must equal the payload manifest exactly.
    # An unshipped contract file fails as loudly as a shipped team-data file.
    dist_context = gather.DIST_DIR / "context"
    shipped = set()
    if dist_context.is_dir():
        for p in dist_context.rglob("*"):
            if p.is_file():
                shipped.add(p.relative_to(dist_context).as_posix())
    wanted = {
        p.relative_to(gather.CONTEXT_DIR).as_posix()
        for p in gather.CONTEXT_DIR.rglob("*")
        if p.is_file()
        and p.name != ".gitkeep"
        and gather.classify_context_path(
            p.relative_to(gather.CONTEXT_DIR).as_posix()
        ) == "payload"
    }
    for missing in sorted(wanted - shipped):
        FAILURES.append(f"classified payload but not shipped: context/{missing}")
    for extra in sorted(shipped - wanted):
        FAILURES.append(f"shipped but not classified payload: dist/context/{extra}")

    # The work-item archetypes are handlers, not commands: excluded from the
    # picker by SKIP_DIR_PARTS, but /process-workitem reads them at runtime, so
    # they must ship as data.
    arch_src = gather.AGENTS_DIR / "commands" / "_workitem-archetypes"
    arch_dst = gather.DIST_DIR / "commands" / "_workitem-archetypes"
    want_arch = {p.name for p in arch_src.glob("*.md")}
    got_arch = {p.name for p in arch_dst.glob("*.md")} if arch_dst.is_dir() else set()
    for missing in sorted(want_arch - got_arch):
        FAILURES.append(f"archetype not shipped: {missing}")
    for extra in sorted(got_arch - want_arch):
        FAILURES.append(f"archetype shipped but not in source: {extra}")
    # They must NOT become picker entries.
    if (gather.DIST_DIR / "commands" / "bugfix.md").exists():
        FAILURES.append("archetype leaked into dist/commands/ as a top-level command")

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Payload classification OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
