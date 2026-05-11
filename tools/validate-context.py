"""Lint context/ for staleness, missing required files, and over-long stories.

Checks:
  - REQUIRED conventions are present and non-trivial (issue-titles, labels, branches, output-discipline)
  - Mission file exists and contains more than a placeholder
  - Knowledge-base files have been linked from at least one story in the last 90 days
  - Story templates in proposals/ do not exceed the soft length budget from output-discipline.md
  - Setup-progress.md is in sync with reality (claimed steps actually have their output files)

Reports findings; does not fix. The point is signal, not enforcement.

Usage:
    python tools/validate-context.py
    python tools/validate-context.py --json   # machine-readable output

v0.1 status: SKELETON.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    raise NotImplementedError(
        "tools/validate-context.py is a v0.1 skeleton. "
        "Implement when the team has shipped one Seed cycle and staleness becomes a real signal."
    )


if __name__ == "__main__":
    sys.exit(main())
