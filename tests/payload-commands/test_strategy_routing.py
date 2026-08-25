"""The strategy family ships together, routed, and material-free (AWO-268).

Three promises, each silent at build time if broken:

1. **Presence.** `/strategy-flow` (command), `bet-refinement-coach` (skill),
   and `/okr-cascade` all ship in the payload — the family is findable from
   any repo, not stranded where it was authored.
2. **Routing.** Each of the three names the other two's territory, and the
   session reflex (`using-awow`) carries the strategy route — that reflex is
   the only surface every session is guaranteed to see. The never-built
   `/strategic-review` must not be referenced anywhere in the payload: its
   role lives in `/okr-cascade` Review.
3. **Framework, not materials.** The ported surfaces carry the method, never
   the engagement: no machine-local home paths, no session-folder paths, no
   session-artifact names.

Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-commands/test_strategy_routing.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DIST = REPO_ROOT / "dist"

FAMILY = {
    "strategy-flow": DIST / "commands" / "strategy-flow.md",
    "bet-refinement-coach": DIST / "skills" / "bet-refinement-coach" / "SKILL.md",
    "okr-cascade": DIST / "commands" / "okr-cascade.md",
}

# Every family member must name the other two's territory.
CROSS_REFS = {
    "strategy-flow": ("bet-refinement-coach", "okr-cascade"),
    "bet-refinement-coach": ("strategy-flow", "okr-cascade"),
    "okr-cascade": ("strategy-flow", "bet-refinement-coach"),
}

# Engagement-material markers that must never survive a port into the payload.
# `session-decisions.md` is deliberately NOT a marker: the generic decisions-
# record convention keeps that filename; the engagement shapes are the paths.
MATERIAL_MARKERS = ("~/repos/", "strategy/sessions/", "gate2-bet")

FAILURES: list[str] = []


def main() -> int:
    for name, path in FAMILY.items():
        if not path.is_file():
            FAILURES.append(f"missing payload surface: {path.relative_to(REPO_ROOT)}")

    for name, targets in CROSS_REFS.items():
        path = FAMILY[name]
        if not path.is_file():
            continue
        text = path.read_text()
        for target in targets:
            if target not in text:
                FAILURES.append(
                    f"{path.relative_to(REPO_ROOT)} never names `{target}` — the route is broken"
                )

    reflex = DIST / "skills" / "using-awow" / "SKILL.md"
    if not reflex.is_file() or "strategy-flow" not in reflex.read_text():
        FAILURES.append("using-awow reflex carries no strategy route (strategy-flow unmentioned)")

    for name, path in FAMILY.items():
        if not path.is_file():
            continue
        text = path.read_text()
        for marker in MATERIAL_MARKERS:
            if marker in text:
                FAILURES.append(f"{path.relative_to(REPO_ROOT)} carries material marker {marker!r}")

    for path in sorted(DIST.rglob("*.md")):
        if "strategic-review" in path.read_text():
            FAILURES.append(
                f"{path.relative_to(REPO_ROOT)} references /strategic-review — "
                f"that role lives in /okr-cascade Review"
            )

    if FAILURES:
        print("FAIL test_strategy_routing")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ok test_strategy_routing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
