"""Regression test for the core prompts after the core / workflows split (CAU-1640).

A core-only install has five commands. Once 17 commands moved into the optional
awow-workflows plugin, core still named them in 33 places — in the reflex every
session reads, and in advice /setup-awow gives the user ("start with a real
command — /refinement-prep…", which a core-only user does not have).

The rule: **core may name a bundle-only command, but only together with the
plugin it ships in.** Then a reader — agent or user — always knows the command
may be absent, and the reflex says what to do when it is. Asserts:

  1. Every line of a core source that names a bundle-only command also names
     `awow-workflows`. Bundle membership is read from `channel: workflows`, so
     tagging another command extends the test by itself.
  2. The reflex routes to core first, then to the bundle under its plugin's
     name, and says what to do when a bundle route is absent.
  3. What /setup-awow tells the user to try first is a command core ships.
  4. /setup-awow's internal vocabulary — install shape, track, hat, route, mode,
     fill — stays out of the text it says to the user (blockquoted lines), and
     the prompt carries the rule that keeps it out.
  5. The second dry run's fixes hold (CAU-1704): /my-work filters closed
     items in the query, counts what it prints, keeps unassigned blockers
     under Waiting and judges acceptance criteria only on a full read;
     /update-context stops in a repo awow has not set up.

Pure stdlib; no pytest, no network.

Run:  python3 tests/core-prompts/test_core_prompts.py
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

AGENTS = REPO_ROOT / ".agents"
FAILURES: list[str] = []


def sources() -> dict[str, Path]:
    found = {}
    for path in sorted((AGENTS / "commands").glob("*.md")):
        if path.name != "README.md":
            found[path.stem] = path
    for path in sorted((AGENTS / "skills").iterdir()):
        if path.is_dir() and (path / "SKILL.md").is_file():
            found[path.name] = path / "SKILL.md"
        elif path.suffix == ".md" and path.name != "README.md":
            found[path.stem] = path
    return found


def split_sources():
    """(core sources, names of bundle-only commands)."""
    core, bundle_commands = {}, set()
    for name, path in sources().items():
        text = path.read_text()
        if gather.is_workflows_channel(text):
            if path.parent.name == "commands":
                bundle_commands.add(name)
        elif gather.ships_in(text, "both"):
            core[name] = path
    return core, bundle_commands


def check_bundle_commands_named_with_plugin() -> None:
    core, bundle_commands = split_sources()
    if len(bundle_commands) < 10:
        FAILURES.append(f"only {len(bundle_commands)} bundle commands found — the channel read is broken")
        return
    # `/name` as a command: not part of a path (…tooling/design-system.md).
    pattern = re.compile(r"(?<![\w./-])/(" + "|".join(sorted(map(re.escape, bundle_commands))) + r")\b")
    for name, path in core.items():
        for number, line in enumerate(path.read_text().split("\n"), 1):
            hits = sorted(set(pattern.findall(line)))
            if hits and "awow-workflows" not in line:
                FAILURES.append(
                    f"{path.relative_to(REPO_ROOT)}:{number} names {', '.join('/' + h for h in hits)} without "
                    "saying it ships in `awow-workflows` — a core-only install does not have it"
                )


def check_reflex_routes() -> None:
    text = (AGENTS / "skills" / "using-awow" / "SKILL.md").read_text()
    start = text.index("## Route to the moment")
    section = text[start: text.index("\n## ", start + 1)]
    core_at = section.find("`/process-workitem`")
    bundle_at = section.find("`awow-workflows`")
    if core_at == -1 or bundle_at == -1 or core_at > bundle_at:
        FAILURES.append("the reflex does not route to core commands before the awow-workflows ones")
    for route in ("`/process-workitem`", "`/my-work`", "`/update-context`", "`workitem-write`"):
        if route not in section[:bundle_at]:
            FAILURES.append(f"the reflex's core routes omit {route}")
    if "do not hand-roll the flow" not in section or "not installed here" not in section:
        FAILURES.append("the reflex does not say what to do when an awow-workflows route is absent")


def check_setup_first_suggestion() -> None:
    text = (AGENTS / "commands" / "setup-awow.md").read_text()
    marker = "Start with a real command — "
    if marker not in text:
        FAILURES.append("setup-awow no longer tells the user what to try first")
        return
    after = text[text.index(marker) + len(marker):]
    first = re.search(r"`/([a-z-]+)`", after).group(1)
    _, bundle_commands = split_sources()
    if first in bundle_commands:
        FAILURES.append(f"setup-awow's first suggestion is /{first}, which a core-only install does not have")


JARGON = re.compile(r"(?i)\b(install[- ]shape|track|hats?|mode [ab]|deferred fills?)\b")


def check_vocabulary() -> None:
    text = (AGENTS / "commands" / "setup-awow.md").read_text()
    if "Your words, not the user's" not in text:
        FAILURES.append("setup-awow has lost the rule that keeps its internal vocabulary from the user")
    for number, line in enumerate(text.split("\n"), 1):
        stripped = line.lstrip()
        if not stripped.startswith(">"):
            continue
        hit = JARGON.search(stripped)
        if hit:
            FAILURES.append(
                f".agents/commands/setup-awow.md:{number} says {hit.group(0)!r} to the user — "
                "internal vocabulary; say what it means"
            )


def check_second_dry_run() -> None:
    my_work = (AGENTS / "commands" / "my-work.md").read_text()
    for needle, what in (
        ("filter out done and canceled states in the query itself", "filters closed items after fetching"),
        ("count the IDs you print", "estimates its bucket counts"),
        ("put it under **Waiting**, never under Needs you now", "may show an unassigned blocker as needing you"),
        ("only after reading that item's full description", "flags missing acceptance criteria from a partial read"),
        ("your own items In Review that wait on someone else's review", "has no bucket for your items in review"),
        ("`+<n> more: <every ID>`", "lets Next up drop items unnamed"),
        ("An overdue item goes here even when it is also blocked", "leaves open which bucket an overdue, blocked item takes"),
        ("by the pick order `board.md` records", "ignores board.md's pick order on a board without priorities"),
    ):
        if needle not in my_work:
            FAILURES.append(f"/my-work {what}")
    update = (AGENTS / "commands" / "update-context.md").read_text()
    phase0 = update[update.index("## Phase 0"):update.index("## Phase 1")]
    if "`{ANCHOR}/context/team/` does not exist" not in phase0 or "/setup-awow" not in phase0:
        FAILURES.append("/update-context stages candidates in a repo awow has not set up")
    for needle, what in (
        ("`1` or `all` — apply and commit", "hides that applying also commits"),
        ("Dropped (heard, but not a team rule): ", "leaves 'Dropped' unexplained"),
        ("knowledge inbox (`<inbox path>`)", "does not say where the inbox lives"),
    ):
        if needle not in update:
            FAILURES.append(f"/update-context {what}")


def main() -> int:
    check_bundle_commands_named_with_plugin()
    check_reflex_routes()
    check_setup_first_suggestion()
    check_vocabulary()
    check_second_dry_run()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Core prompts OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
