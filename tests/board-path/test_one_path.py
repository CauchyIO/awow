"""Regression test for the one board path (CAU-1638, CAU-1522).

Every board touch goes through two core skills: `board-target` settles which
installation and which board, `workitem-write` makes the change. Before this
the resolution rules lived only in the maintainer repo's .agents/AGENTS.md —
which no plugin ships — and the absent-board fallback was pasted into eight
files. Asserts, in order of how badly each would fail silently:

  1. The rules ship. `board-target` and `workitem-write` exist in every plugin
     folder on every harness, so a plugin install — which has no awow
     AGENTS.md — can still resolve a multi-board or missing `board.md`.
  2. One copy. The resolution ladder and the absent-board rule appear in
     `board-target` and nowhere else in the prompt sources. A second copy is
     how two documents come to disagree about where a write lands.
  3. Delegation. Every command or skill that reads the team's `board.md`
     names `board-target` or `workitem-write` — it does not resolve the board
     on its own.
  4. One approval rule. `workitem-write` exempts the transitions `board.md`
     assigns to the agent, asks only for authorisation it does not hold, and
     resumes an interrupted plan; every `board.md` reference says the same
     thing from its side, so the two read as one rule (CAU-1522).

Pure stdlib; no pytest, no network.

Run:  python3 tests/board-path/test_one_path.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

FAILURES: list[str] = []
AGENTS = REPO_ROOT / ".agents"

# Phrases that belong to the resolution rules and to nothing else.
LADDER_MARKERS = (
    "is a question, not a stop",
    "**Invoker default**",
    "**Session pin**",
    "Probe shallowly downward",
)

# Sources that may read board.md without delegating: the two path skills
# themselves, and the commands that AUTHOR board.md rather than act on it.
DELEGATION_EXEMPT = {
    "board-target", "workitem-write",   # the path itself
    "setup-awow",                       # authors board.md; it does not act on a board
    "update-context",                   # names board.md as a context-write destination, never reads a board
    "using-awow",                       # the reflex; it names the path in its own words
}


def sources() -> dict[str, Path]:
    found = {}
    for path in sorted((AGENTS / "commands").glob("*.md")):
        if path.name != "README.md":
            found[path.stem] = path
    for path in sorted((AGENTS / "skills").iterdir()):
        if path.is_dir() and (path / "SKILL.md").is_file():
            found[path.name] = path / "SKILL.md"
        elif path.suffix == ".md" and path.name != "README.md":
            found[path.stem] = path
    return found


def check_rules_ship() -> None:
    skill_dirs = {
        gather.CLAUDE_DIR: "skills", gather.DIST_WORKFLOWS_DIR: "skills",
        gather.CODEX_DIR: "agent-skills", gather.CODEX_WORKFLOWS_DIR: "agent-skills",
        gather.PI_DIR: "agent-skills", gather.OPENCODE_DIR: "agent-skills",
        gather.COPILOT_DIR: ".github/plugin/skills", gather.COPILOT_WORKFLOWS_DIR: ".github/plugin/skills",
    }
    for root, rel in skill_dirs.items():
        for skill in ("board-target", "workitem-write"):
            if not (root / rel / skill / "SKILL.md").is_file():
                FAILURES.append(
                    f"{root.relative_to(REPO_ROOT)}/ does not ship the `{skill}` skill — a board "
                    "touch there has no rules to follow"
                )


def check_one_copy() -> None:
    texts = {name: path.read_text() for name, path in sources().items()}
    texts["AGENTS.md"] = (AGENTS / "AGENTS.md").read_text()
    for marker in LADDER_MARKERS:
        holders = sorted(name for name, text in texts.items() if marker in text)
        if holders != ["board-target"]:
            FAILURES.append(
                f"the resolution rule {marker!r} appears in {holders}; it belongs in "
                "board-target alone — delegate to the skill instead of restating it"
            )


def check_delegation() -> None:
    for name, path in sources().items():
        if name in DELEGATION_EXEMPT:
            continue
        text = path.read_text()
        if "context/tooling/board.md" in text and "`board-target`" not in text and "`workitem-write`" not in text:
            FAILURES.append(
                f"{path.relative_to(REPO_ROOT)} reads board.md but names neither `board-target` "
                "nor `workitem-write` — it resolves or writes the board on its own"
            )


def check_one_approval_rule() -> None:
    skill = (AGENTS / "skills" / "workitem-write" / "SKILL.md").read_text()
    for needle, why in (
        ("`board-target`", "does not start from the board-target skill"),
        ("Agent-owned transitions", "has no exemption for the transitions board.md assigns to the agent"),
        ("already approved in this conversation", "re-asks for authorisation it already holds"),
        ("Show the concrete change before you ask", "may ask for approval in the abstract"),
        ("Resume, never restart", "has no rule for an interrupted plan"),
    ):
        if needle not in skill:
            FAILURES.append(f"workitem-write {why} (expected {needle!r})")

    rule = "Owner of transition is the approval rule"
    references = sorted((REPO_ROOT / "context" / "tooling" / "boards").glob("*/reference/states.md"))
    if len(references) < 4:
        FAILURES.append(f"expected a states.md reference per supported board, found {len(references)}")
    for path in references + [REPO_ROOT / "context" / "tooling" / "board.md"]:
        text = path.read_text()
        # Keyed on the table's content, not its header — the references word
        # the header differently, and a check that needs the exact header
        # passes on any file that phrases it another way.
        if "Agent (on" not in text:
            FAILURES.append(f"{path.relative_to(REPO_ROOT)} assigns no transition to the agent — expected an ownership table")
        elif rule not in text:
            FAILURES.append(
                f"{path.relative_to(REPO_ROOT)} has an ownership table but does not say that "
                "agent-owned means no approval prompt — it and workitem-write read as two rules"
            )


def main() -> int:
    check_rules_ship()
    check_one_copy()
    check_delegation()
    check_one_approval_rule()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("One board path OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
