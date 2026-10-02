"""Fail if a tracked Markdown file links to a relative path that does not exist.

Checks inline links `[text](target)` outside fenced code blocks. Skips URLs
(`scheme:`), pure anchors (`#section`), and targets carrying a path token
(`{ANCHOR}`, `{PROJECT}`, ...) — those resolve per install, not in this repo.
`dist/` is generated from the sources checked here, test fixtures stand in for
adopter repos, and `proposals/` holds point-in-time drafts whose links are
repointed when they are archived, so all three are out of scope."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^\s*(```|~~~)")
SKIP_PREFIXES = ("dist/", "proposals/", "tests/fixtures/", "tests/process-workitem/fixtures/")


def tracked_markdown() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [REPO_ROOT / p for p in out.splitlines() if not p.startswith(SKIP_PREFIXES)]


def broken_links(path: Path) -> list[tuple[int, str]]:
    bad = []
    in_fence = False
    for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # Inline code spans can hold example link syntax; drop them first.
        line = re.sub(r"`[^`]*`", "", line)
        for m in LINK.finditer(line):
            target = m.group(1).split("#", 1)[0]
            if not target or re.match(r"[a-zA-Z][\w+.-]*:", target) or "{" in target:
                continue
            if not (path.parent / target).exists():
                bad.append((lineno, m.group(1)))
    return bad


def main() -> int:
    bad = [
        f"{path.relative_to(REPO_ROOT)}:{lineno}: {target}"
        for path in tracked_markdown()
        for lineno, target in broken_links(path)
    ]
    if bad:
        print("Broken relative links:", *bad, sep="\n  ")
        return 1
    print("lint-links: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
