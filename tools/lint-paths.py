"""Fail if a non-vendored .agents/ prompt body references context/, tools/,
or proposals/ by bare path instead of the {HUB}/{PROJECT}/{AWOW_TOOLS} tokens
(see .agents/AGENTS.md "Path tokens")."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BARE = re.compile(r"(?<![{/\w.\-])(context|tools|proposals)/")


def channel(text: str) -> str:
    m = re.search(r"^channel:\s*(\S+)", text[:2000], re.M)
    return m.group(1) if m else "both"


def main() -> int:
    bad: list[str] = []
    for root in (REPO_ROOT / ".agents" / "commands", REPO_ROOT / ".agents" / "skills"):
        for path in sorted(root.rglob("*.md")):
            if path.name == "README.md":
                continue
            text = path.read_text()
            # vendored: operates on the vendored install, not shipped in the
            # plugin payload. bootstrap: shipped in the payload but *creates*
            # the vendored tree, so its literal paths are the deliverable.
            if channel(text) in ("vendored", "bootstrap"):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if BARE.search(line):
                    bad.append(f"{path.relative_to(REPO_ROOT)}:{n}: bare path reference: {line.strip()}")
    for b in bad:
        print(b)
    if bad:
        print(
            f"\n{len(bad)} bare path reference(s). Use {{HUB}}/{{PROJECT}}/{{AWOW_TOOLS}} "
            f"(see .agents/AGENTS.md 'Path tokens') or mark the file channel: vendored.",
            file=sys.stderr,
        )
        return 1
    print("Path tokens clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
