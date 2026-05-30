"""Distribute AGENTS.md updates across sibling repos (when team has multiple repos).

Used when the team has grown into a mono-repo trajectory or runs multiple repos
that share conventions. Reads .agents/AGENTS.md and writes the team-core portion
into each registered sibling repo's AGENTS.md between
`AWOW:CORE:START` and `AWOW:CORE:END` markers.

Sibling repos are listed in `tools/.distribute-targets` (one path per line, gitignored).

Usage:
    python tools/distribute.py
    python tools/distribute.py --check   # report what would change, do not write
    python tools/distribute.py --target /path/to/repo   # one-off, not from .distribute-targets

v0.1 status: SKELETON. The full implementation lands once a team is using awow
across more than one repo. v1.0 makes this org-wide.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--target", type=Path)
    args = parser.parse_args()

    raise NotImplementedError(
        "tools/distribute.py is a v0.1 skeleton. "
        "Implement when the team has more than one repo to keep in sync."
    )


if __name__ == "__main__":
    sys.exit(main())
