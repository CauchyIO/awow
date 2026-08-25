"""The de-vendoring surface ships in the payload (AWO-259).

`/migrate-to-plugin` exists so a vendored repo is cleaned by the *payload's*
current migration logic, never by whatever `/update-awow` vintage the repo
vendored. That promise has two filesystem legs, and losing either one is
silent at build time:

1. The command itself ships — `dist/commands/migrate-to-plugin.md` for the
   slash-command surface, `dist/agent-skills/migrate-to-plugin/SKILL.md` for
   the commands-as-skills surface (Codex/Pi).
2. The engine ships with it — `dist/tools/awow_lock.py`, byte-identical to
   `tools/awow_lock.py`. A payload without the engine sends the command back
   to the vendored copy, which is exactly the stale-vintage failure the
   command exists to avoid.

Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-commands/test_migrate_surface.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FAILURES: list[str] = []


def has_frontmatter_description(text: str) -> bool:
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    return re.search(r"^description:\s*\S", text[4:end], re.M) is not None


def main() -> int:
    command = REPO_ROOT / "dist" / "commands" / "migrate-to-plugin.md"
    if not command.is_file():
        FAILURES.append(f"missing payload command: {command.relative_to(REPO_ROOT)}")
    elif not has_frontmatter_description(command.read_text()):
        FAILURES.append(f"{command.relative_to(REPO_ROOT)} has no frontmatter description")

    skill = REPO_ROOT / "dist" / "agent-skills" / "migrate-to-plugin" / "SKILL.md"
    if not skill.is_file():
        FAILURES.append(f"missing commands-as-skills surface: {skill.relative_to(REPO_ROOT)}")

    engine_src = REPO_ROOT / "tools" / "awow_lock.py"
    engine_dist = REPO_ROOT / "dist" / "tools" / "awow_lock.py"
    if not engine_dist.is_file():
        FAILURES.append(f"missing payload engine: {engine_dist.relative_to(REPO_ROOT)}")
    elif engine_dist.read_bytes() != engine_src.read_bytes():
        FAILURES.append("dist/tools/awow_lock.py is not byte-identical to tools/awow_lock.py")

    if FAILURES:
        print("FAIL test_migrate_surface")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ok test_migrate_surface")
    return 0


if __name__ == "__main__":
    sys.exit(main())
