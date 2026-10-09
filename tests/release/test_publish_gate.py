"""Publishing jobs run in CauchyIO/awow and nowhere else.

The lab is a file copy of awow: same version, same workflows. Without a
repository gate its every push to main runs the release workflow (which would
tag and publish from the lab if it ever held the secrets) and the
awow-dist-matches check (which the lab fails on purpose, being ahead). Both
turned the lab's main red from the day it was mirrored, hiding real failures.

Asserts that each job that publishes, or that checks what was published, is
gated on `github.repository == 'CauchyIO/awow'`.

Pure stdlib; no pytest, no network, no YAML parser.

Run:  python3 tests/release/test_publish_gate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
GATE = "github.repository == 'CauchyIO/awow'"
GATED = [("release.yml", "release"), ("ci.yml", "dist-published")]


def job_block(text: str, job: str) -> str | None:
    """The lines of one job: from its two-space key to the next one."""
    match = re.search(rf"^  {re.escape(job)}:\n((?:(?!  \S).*\n?)*)", text, flags=re.M)
    return match.group(1) if match else None


def main() -> int:
    failures = []
    for filename, job in GATED:
        block = job_block((WORKFLOWS / filename).read_text(), job)
        if block is None:
            failures.append(f"{filename}: no job named {job!r} — the gate list is stale")
            continue
        condition = re.search(r"^    if: (.+)$", block, flags=re.M)
        if not condition or GATE not in condition.group(1):
            failures.append(f"{filename}: job {job!r} is not gated on {GATE}")
    for f in failures:
        print(f"FAIL {f}")
    if failures:
        return 1
    print("Publish gate OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
