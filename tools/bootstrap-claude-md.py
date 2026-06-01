"""Bootstrap the team's AGENTS.md from the stub plus answers gathered by /setup-awow.

Reads:
  .agents/AGENTS.md                        — the stub (with placeholder sections)
  setup-progress.md                        — which steps completed
  context/team/mission.md                  — team mission
  context/team/members.md                  — team members
  context/team/conventions/REQUIRED/*.md   — required conventions
  context/team/style/*.md                  — style guides
  context/tooling/board.md                 — board choice

Writes:
  .agents/AGENTS.md                        — team-specific AGENTS.md (overwriting the stub)

The output includes:
  - Header pointing to context/ surfaces
  - Board output rules block (lifted from conventions/REQUIRED/output-discipline.md)
  - Team-specific conventions
  - Naming and tagging rules
  - "Do not propose" block (populated from user during /setup-awow Step 4)

Usage:
    python tools/bootstrap-claude-md.py
    python tools/bootstrap-claude-md.py --check   # report what would change, do not write
    python tools/bootstrap-claude-md.py --quickstart   # generate a copy-paste prompt for Steps 0-4

v0.1 status: SKELETON. The full implementation lands once /setup-awow Step 4 is run
against a real team's context. The skeleton documents the intended shape of the output.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_MD = REPO_ROOT / ".agents" / "AGENTS.md"
PROGRESS = REPO_ROOT / "setup-progress.md"
CONTEXT = REPO_ROOT / "context"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--quickstart", action="store_true")
    args = parser.parse_args()

    if not PROGRESS.is_file():
        print("error: setup-progress.md not found. Run /setup-awow first.", file=sys.stderr)
        return 1

    raise NotImplementedError(
        "tools/bootstrap-claude-md.py is a v0.1 skeleton. "
        "Implement when /setup-awow Step 4 is needed in anger."
    )


if __name__ == "__main__":
    sys.exit(main())
