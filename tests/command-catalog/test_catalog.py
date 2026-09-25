"""One command inventory, generated, everywhere it is shown (CAU-1637).

The catalog is written by tools/gather.py from .agents/commands/*.md
frontmatter into three places: context/tooling/command-catalog.md (ships in
every payload), a marked block in README.md, and the phase table in
.agents/commands/README.md. Asserts:

  1. Every shipped command has a `description:` in its frontmatter, single-
     line, and appears in the catalog with that description verbatim; nothing
     appears in the catalog that is not a shipped command.
  2. Each command sits under its plugin (channel: workflows → awow-workflows).
  3. The three files on disk equal what gather.py would write now — the same
     data, so they cannot drift from each other or from the prompts.
  4. The catalog ships in every core payload, and the using-awow reflex names
     it, so /awow-help and the agent read the same list.
  5. A hand edit inside a marked block is reported by `gather.py --check`.

Pure stdlib; no pytest, no network.

Run:  python3 tests/command-catalog/test_catalog.py
"""
from __future__ import annotations

import importlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
gather = importlib.import_module("gather")

COMMANDS = REPO_ROOT / ".agents" / "commands"
FAILURES: list[str] = []


def shipped() -> dict[str, tuple[dict, str]]:
    out = {}
    for path in sorted(COMMANDS.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text()
        if gather.is_vendored_channel(text):
            continue
        out[path.stem] = (gather.parse_frontmatter(text, path)[0], text)
    return out


def catalog_rows(text: str) -> dict[str, tuple[str, str]]:
    """{name: (plugin, description)} from a rendered catalog."""
    rows, plugin = {}, None
    for line in text.split("\n"):
        heading = re.match(r"^### `([\w-]+)`", line)
        if heading:
            plugin = heading.group(1)
        cell = re.match(r"^\| `/([\w-]+)[^`]*` \| (.+) \|$", line)
        if cell and plugin:
            rows[cell.group(1)] = (plugin, cell.group(2))
    return rows


def check_workflows_install(catalog: str) -> list[str]:
    """The catalog carries the exact install command, matching the README (CAU-1704)."""
    failures = []
    if "### Installing `awow-workflows`" not in catalog:
        failures.append("command-catalog.md has no awow-workflows install table")
    readme = (REPO_ROOT / "README.md").read_text()
    for command in ("/plugin install awow-workflows@awow", "copilot plugin install awow-workflows@awow"):
        if command not in catalog or command not in readme:
            failures.append(f"{command!r} is missing from the catalog or the README")
    return failures


def main() -> int:
    commands = shipped()
    catalog = catalog_rows(gather.CATALOG_PATH.read_text())

    for name, (fields, text) in commands.items():
        desc = fields.get("description", "")
        if not desc or desc.startswith((">", "|")):
            FAILURES.append(f"{name}: no single-line `description:` in its frontmatter")
            continue
        if name not in catalog:
            FAILURES.append(f"{name} ships and is missing from the catalog")
            continue
        plugin, shown = catalog[name]
        if shown != desc:
            FAILURES.append(f"{name}: catalog says {shown[:50]!r}, frontmatter says {desc[:50]!r}")
        want = "awow-workflows" if gather.is_workflows_channel(text) else "awow"
        if plugin != want:
            FAILURES.append(f"{name}: catalogued under {plugin}, ships in {want}")
    for name in sorted(set(catalog) - set(commands)):
        FAILURES.append(f"the catalog lists /{name}, which does not ship")

    for plan in gather.catalog_plans():
        if not plan.target.exists() or plan.target.read_text() != plan.content:
            FAILURES.append(f"{plan.target.relative_to(REPO_ROOT)} is stale — run python3 tools/gather.py")
    FAILURES.extend(check_workflows_install(gather.CATALOG_PATH.read_text()))

    if "tooling/command-catalog.md" not in gather.PAYLOAD_CONTEXT_PATHS:
        FAILURES.append("the catalog is not in PAYLOAD_CONTEXT_PATHS, so it does not ship")
    for harness in ("claude", "codex", "copilot", "pi", "opencode"):
        if not (REPO_ROOT / "dist" / harness / "awow" / "context" / "tooling" / "command-catalog.md").is_file():
            FAILURES.append(f"dist/{harness}/awow has no command-catalog.md")
    reflex = (REPO_ROOT / ".agents" / "skills" / "using-awow" / "SKILL.md").read_text()
    if "{AWOW_ROOT}/context/tooling/command-catalog.md" not in reflex:
        FAILURES.append("the using-awow reflex does not name the catalog")

    # A hand edit in a generated block must not survive --check.
    readme = REPO_ROOT / "README.md"
    original = readme.read_text()
    try:
        readme.write_text(original.replace("| `/my-work` |", "| `/my-work` (edited) |", 1))
        result = subprocess.run([sys.executable, "tools/gather.py", "--check"],
                                cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode == 0 or "README.md" not in result.stdout:
            FAILURES.append("gather.py --check does not report a hand edit inside the README catalog block")
    finally:
        readme.write_text(original)

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print(f"Command catalog OK — {len(commands)} commands in three places.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
