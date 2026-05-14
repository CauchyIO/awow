"""Reset the adopter-produced state of this repo for prompt iteration.

Maintainers of awow iterate on the prompts in `.agents/` and then re-run the
`/setup-awow` walkthrough end-to-end to see how the prompts feel. This script
puts the repo back to the "fresh template adopter" state without throwing away
in-progress edits to the template itself.

What gets reset
---------------
- Tracked files that the walkthrough overwrites (mission, members, style,
  required conventions, company files, setup-progress checkboxes) are
  restored to HEAD.
- Untracked artefacts the walkthrough creates (`proposals/setup/`,
  `proposals/awow-add/`, `context/tooling/board.md`) are removed.

What is kept by default
-----------------------
- All edits under `.agents/`, `tools/`, `setup/`, `README.md`, `SETUP.md`,
  `mcps/`, etc. — these are the template iterations you are testing.
- `.venv/`, `.mcp.json`, `.vscode/`, `.claude/settings.local.json` — heavy
  infrastructure and MCP credentials. Pass `--full` to wipe these too for a
  cleanroom run.

Usage
-----
    uv run python tools/reset-adopter-state.py --dry-run
    uv run python tools/reset-adopter-state.py
    uv run python tools/reset-adopter-state.py --full

`tools/gather.py` is invoked at the end (unless `--dry-run`) so any
in-progress `.agents/` edits are mirrored into the harness surfaces.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TRACKED_OVERWRITTEN = [
    "setup-progress.md",
    "context/team/mission.md",
    "context/team/vision.md",
    "context/team/members.md",
    "context/team/style/board-output.md",
    "context/team/style/comments.md",
    "context/team/style/placement.md",
    "context/team/style/prose.md",
    "context/team/conventions/REQUIRED/issue-titles.md",
    "context/team/conventions/REQUIRED/labels.md",
    "context/team/conventions/REQUIRED/branches.md",
    "context/team/conventions/REQUIRED/output-discipline.md",
    "context/company/neighbouring-teams.md",
    "context/company/raci.md",
    "context/company/stakeholders.md",
]

UNTRACKED_CREATED = [
    "proposals/setup",
    "proposals/awow-add",
    "context/tooling/board.md",
]

FULL_ONLY = [
    ".venv",
    ".mcp.json",
    ".vscode",
    ".claude/settings.local.json",
]


def safe_path(rel: str) -> Path:
    """Resolve `rel` under REPO_ROOT, refusing anything that escapes the tree."""
    full = (REPO_ROOT / rel).resolve()
    if REPO_ROOT not in full.parents and full != REPO_ROOT:
        raise RuntimeError(f"refusing to touch path outside repo: {rel}")
    return full


def restore_tracked(rel: str, dry_run: bool) -> None:
    full = safe_path(rel)
    if not full.exists():
        print(f"  - {rel} (missing, skipped)")
        return
    print(f"  ~ {rel}")
    if dry_run:
        return
    subprocess.run(
        ["git", "checkout", "HEAD", "--", rel],
        cwd=REPO_ROOT,
        check=True,
    )


def remove_path(rel: str, dry_run: bool) -> None:
    full = safe_path(rel)
    if not full.exists():
        print(f"  - {rel} (missing, skipped)")
        return
    print(f"  x {rel}")
    if dry_run:
        return
    if full.is_dir():
        shutil.rmtree(full)
    else:
        full.unlink()


def run_gather(dry_run: bool) -> None:
    cmd = [sys.executable, "tools/gather.py"]
    print(f"  $ {' '.join(cmd)}")
    if dry_run:
        return
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reset adopter-produced state for prompt iteration.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan without modifying anything.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Also wipe .venv, MCP config, and .vscode/ (cleanroom run).",
    )
    args = parser.parse_args()

    print("Reset adopter-produced state.")
    if args.dry_run:
        print("(dry-run — no changes will be made.)")
    print()

    print("Restore tracked files overwritten by /setup-awow:")
    for rel in TRACKED_OVERWRITTEN:
        restore_tracked(rel, args.dry_run)
    print()

    print("Remove untracked walkthrough artefacts:")
    for rel in UNTRACKED_CREATED:
        remove_path(rel, args.dry_run)
    print()

    if args.full:
        print("--full: wipe infrastructure and MCP credentials:")
        for rel in FULL_ONLY:
            remove_path(rel, args.dry_run)
        print()
    else:
        print("(Skipping .venv / MCP config / .vscode — pass --full to wipe.)")
        print()

    print("Re-mirror .agents/ to harness surfaces:")
    run_gather(args.dry_run)
    print()

    print("Dry run complete." if args.dry_run else "Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
