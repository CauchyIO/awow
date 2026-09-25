"""Regression test for `/setup-awow --check` and the write-access rule (CAU-1634).

`--check` reports a repo's awow state and changes nothing. With it goes the
"no-op write" probe Step 1a used to verify write access: a no-op write is not
one — it bumps the item's updated time, adds a history entry, and can notify the
team. Write access is now settled from what can be read: verified, unverified,
or denied.

These are static assertions over the prompt sources — the behaviour itself is
graded by the `check-readonly` scenario in tests/setup-awow/ (via /test-awow).
Asserts:

  1. The flag exists and is discoverable: a `--check` section, and the
     argument-hint in the frontmatter the picker reads.
  2. The section forbids every write the wizard otherwise makes, by name, and
     forbids writing to the board to find out.
  3. Nothing prescribes a write probe any more — not the command, not a board
     reference, not an eval fixture's vendored copy of one ({ANCHOR}-first, so
     a stale fixture copy would still teach the probe).
  4. Step 1a and every board reference carry the three-value rule.
  5. The behavioural scenario is wired.

Pure stdlib; no pytest, no network.

Run:  python3 tests/setup-check/test_setup_check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND = REPO_ROOT / ".agents" / "commands" / "setup-awow.md"
BOARDS = REPO_ROOT / "context" / "tooling" / "boards"

FAILURES: list[str] = []

# A sentence that tells the agent to perform a no-op write. Prose explaining
# WHY not to ("a no-op write still bumps…", "A "no-op" write is not one") is
# the rule itself and must not match.
PROBE = re.compile(r"(?i)(verify write access with a \**no-op|a no-op write on a scratch|no-op\** write against a scratch)")


def section(text: str, heading: str) -> str:
    start = text.index(heading)
    nxt = text.find("\n## ", start + 1)
    return text[start: nxt if nxt != -1 else len(text)]


def check_flag() -> None:
    text = COMMAND.read_text()
    if "## `--check`" not in text:
        FAILURES.append("setup-awow has no `--check` section")
        return
    hint = re.search(r'^argument-hint:\s*"([^"]*)"', text, re.M)
    if not hint or "--check" not in hint.group(1):
        FAILURES.append("setup-awow's argument-hint does not advertise --check — the picker cannot show it")
    body = section(text, "## `--check`")
    for needle, why in (
        ("Change nothing", "does not open with the no-change rule"),
        ("setup-progress.md", "does not forbid writing setup-progress.md"),
        ("proposals/", "does not forbid writing proposals/"),
        (".awow/board-session.md", "does not forbid recording the board session"),
        (".awow/anchor.json", "does not forbid writing the anchor mapping"),
        ("ask nothing", "does not forbid questions"),
        ("Never write to the board to find out", "does not forbid a board write as a probe"),
        ("`board-target`", "resolves the installation on its own instead of through board-target"),
        ("Context", "does not report context"),
        ("Anchor", "does not report the anchor"),
        ("Board access", "does not report board access"),
        ("Then stop", "does not stop after the report"),
    ):
        if needle not in body:
            FAILURES.append(f"the --check section {why} (expected {needle!r})")
    if text.index("## `--check`") > text.index("## On every invocation"):
        FAILURES.append("the --check section comes after 'On every invocation' — it must be read first")


def check_no_probe() -> None:
    sources = [COMMAND] + sorted(BOARDS.glob("*/reference/mcp.md"))
    sources += sorted((REPO_ROOT / "tests").rglob("boards/*/reference/mcp.md"))
    for path in sources:
        hit = PROBE.search(path.read_text())
        if hit:
            FAILURES.append(f"{path.relative_to(REPO_ROOT)} still prescribes a write probe: {hit.group(0)!r}")


def check_three_values() -> None:
    step = COMMAND.read_text()
    for value in ("`verified`", "`unverified`", "`denied`"):
        if value not in step:
            FAILURES.append(f"setup-awow Step 1a does not define write access {value}")
    if "Never mutate the board to learn whether you may" not in step:
        FAILURES.append("setup-awow Step 1a does not state the no-mutation rule")
    references = sorted(BOARDS.glob("*/reference/mcp.md"))
    if len(references) < 4:
        FAILURES.append(f"expected an mcp.md reference per supported board, found {len(references)}")
    for path in references:
        text = path.read_text()
        if "without writing" not in text:
            FAILURES.append(f"{path.relative_to(REPO_ROOT)} Verify checklist does not establish write access without writing")
        if "write-unverified" not in text and "write-verified" not in text:
            FAILURES.append(f"{path.relative_to(REPO_ROOT)} names no write-access value to record")


def check_scenario() -> None:
    suite = REPO_ROOT / "tests" / "setup-awow"
    script = suite / "scripts" / "check-readonly.txt"
    for rel in ("scripts/check-readonly.txt", "rubrics/check-readonly.md", "checks/check-readonly.sh",
                "fixtures/check-readonly/setup-progress.md"):
        if not (suite / rel).is_file():
            FAILURES.append(f"tests/setup-awow/{rel} is missing — --check has no behavioural scenario")
    if script.is_file() and "# args: --check" not in script.read_text():
        FAILURES.append("check-readonly's script does not invoke the command with `# args: --check`")
    runner = (REPO_ROOT / ".claude" / "commands" / "test-awow.md").read_text()
    if "# args:" not in runner:
        FAILURES.append("the /test-awow runner does not read a `# args:` line — the scenario would run bare /setup-awow")


def main() -> int:
    check_flag()
    check_no_probe()
    check_three_values()
    check_scenario()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Setup --check OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
