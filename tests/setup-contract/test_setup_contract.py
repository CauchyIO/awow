"""Regression test for the small /setup-awow (CAU-1633).

Setup inspects what exists, asks only for what is missing, and presents one
configuration diff for approval. The flag set is the one CAU-1624 decided:
a board URL argument, `--anchor <git-url>`, `--check`. The wizard is gone with
its progress file, its routes, its hats, and its interviews; the workshop
lives in the awow-workflows bundle as /team-workshop. These are static
assertions over the prompt sources — the behaviour is graded by the
tests/setup-awow/ scenarios (via /test-awow). Asserts:

  1. The flag contract: the argument-hint is exactly the decided set, and no
     retired flag or route survives anywhere in the command.
  2. The five situations are each headed, so an agent finds the one it is in.
  3. The command never instructs writing wizard state — setup-progress.md or
     proposals/setup/ — and forbids every board write.
  4. The never-ask rule is present and names the interviews that left.
  5. The workshop moved: its prepare and process sections live in
     team-workshop.md (channel: workflows) and not in setup-awow.md; the
     setup-workshop lens routes there.
  6. The behavioural scenarios are wired, one per situation.
  7. The second dry run's fixes hold (CAU-1704): Init never drafts board.md
     without reading the board; the gate names its replies and lands only
     what the approved lines say; the closing quote names no awow-workflows
     command; --check spells each symbol out; no board template states the
     status:* prefix as observed.
  8. The VM dry run's fixes hold (CAU-1711): the diff shows board.md's state
     table in full; --check uses plain labels and, with nothing to repair,
     says the repo is set up and names the next command.

Pure stdlib; no pytest, no network.

Run:  python3 tests/setup-contract/test_setup_contract.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS = REPO_ROOT / ".agents" / "commands"
COMMAND = COMMANDS / "setup-awow.md"
WORKSHOP = COMMANDS / "team-workshop.md"
LENS = COMMANDS / "_meeting-archetypes" / "setup-workshop.md"
SUITE = REPO_ROOT / "tests" / "setup-awow"

FAILURES: list[str] = []

ARGUMENT_HINT = "[<board-url>] [--anchor <git-url>] [--check]"
RETIRED = ("--yes", "--quickstart", "--root", "--workshop", "--anchored")
WIZARD_STATE = re.compile(r"(?i)(record|write|update|mark)[^.\n]{0,60}`setup-progress\.md`")
SITUATIONS = ("### Init a repo", "### Share an anchor", "### Connect a repo", "### Join the team", "### Use or repair")
SCENARIOS = ("init-plugin-repo", "init-ambient-candidates", "connect-repo", "join-anchored", "use-configured",
             "repair-board-blocked", "check-readonly")


def check_flags() -> None:
    text = COMMAND.read_text()
    hint = re.search(r'^argument-hint:\s*"([^"]*)"', text, re.M)
    if not hint or hint.group(1) != ARGUMENT_HINT:
        FAILURES.append(f"argument-hint is not the decided flag set {ARGUMENT_HINT!r}: {hint and hint.group(1)!r}")
    body = text.split("\n---", 2)[-1]
    for flag in RETIRED:
        for number, line in enumerate(body.split("\n"), 1):
            if flag in line and "Never accept" not in line and "No other flag" not in line:
                FAILURES.append(f"setup-awow line {number} still carries retired flag {flag}: {line.strip()[:80]!r}")
    for word in ("track:", "hat:", "route:", "install-shape:", "Mode A", "Mode B", "step map", "Step 0", "Step 1b"):
        if word in body:
            FAILURES.append(f"setup-awow still speaks the wizard's vocabulary: {word!r}")


def check_situations() -> None:
    text = COMMAND.read_text()
    for heading in SITUATIONS:
        if heading not in text:
            FAILURES.append(f"setup-awow has no {heading!r} section")
    if "## Never ask" not in text:
        FAILURES.append("setup-awow has no 'Never ask' rule")
    else:
        section = text[text.index("## Never ask"):]
        section = section[: section.find("\n## ", 1)]
        for interview in ("team or one person", "role", "mission", "member roster", "vision", "harnesses", "extras", "skills"):
            if interview not in section:
                FAILURES.append(f"the never-ask rule does not name {interview!r}")
    if "## The diff and the gate" not in text:
        FAILURES.append("setup-awow has no single diff-and-gate section")


def check_no_wizard_state() -> None:
    text = COMMAND.read_text()
    hit = WIZARD_STATE.search(text)
    if hit:
        FAILURES.append(f"setup-awow still writes wizard state: {hit.group(0)!r}")
    if "proposals/setup/" in text and "never write" not in text.lower():
        FAILURES.append("setup-awow names proposals/setup/ without forbidding it")
    for needle in ("Write no board item", "Never mutate the board to learn whether you may"):
        if needle not in text:
            FAILURES.append(f"setup-awow lost the board-write prohibition {needle!r}")


def check_workshop_moved() -> None:
    if not WORKSHOP.is_file():
        FAILURES.append("team-workshop.md is missing — the workshop has no home")
        return
    workshop = WORKSHOP.read_text()
    front = workshop[4: workshop.find("\n---", 3)] if workshop.startswith("---\n") else ""
    if not re.search(r"^channel:\s*workflows", front, re.M):
        FAILURES.append("team-workshop.md is not `channel: workflows` — it would ship in core")
    if not re.search(r"^consumes:\s*transcript", front, re.M):
        FAILURES.append("team-workshop.md does not declare `consumes: transcript` — /process-transcript cannot dispatch to it")
    for section in ("## Prepare the workshop", "## Process the workshop"):
        if section not in workshop:
            FAILURES.append(f"team-workshop.md has no {section!r} section")
        if section in COMMAND.read_text():
            FAILURES.append(f"setup-awow still carries {section!r}")
    setup = COMMAND.read_text()
    for word in ("meeting-brief", "coverage map", "workshop route"):
        if word in setup:
            FAILURES.append(f"setup-awow still carries workshop text: {word!r}")
    if "/team-workshop" not in LENS.read_text():
        FAILURES.append("the setup-workshop lens does not route to /team-workshop")


def check_scenarios() -> None:
    for name in SCENARIOS:
        for rel in (f"scripts/{name}.txt", f"rubrics/{name}.md", f"checks/{name}.sh"):
            if not (SUITE / rel).is_file():
                FAILURES.append(f"tests/setup-awow/{rel} is missing")
        if not (SUITE / "fixtures" / name).is_dir():
            FAILURES.append(f"tests/setup-awow/fixtures/{name}/ is missing")
    for stale in SUITE.glob("fixtures/*/setup-progress.md"):
        if stale.parent.name != "check-readonly":
            FAILURES.append(f"{stale.relative_to(REPO_ROOT)}: a fixture still models wizard state")


def check_second_dry_run() -> None:
    text = COMMAND.read_text()
    if "surface: pending" in text or "Show no diff" not in text:
        FAILURES.append("setup-awow may draft board.md without reading the board")
    gate = text[text.index("## The diff and the gate"):text.index("## Closing line")]
    for reply in ("`go`", "`strike", "`show", "`cancel`"):
        if reply not in gate:
            FAILURES.append(f"the setup gate does not name the reply {reply}")
    if "Land exactly what each approved line says" not in gate:
        FAILURES.append("the setup gate lets a landing write more than the approved lines say")
    closing = text[text.index("## Closing line"):]
    quote = "\n".join(l for l in closing.split("\n") if l.startswith(">"))
    if "/process-transcript" in quote or "/team-workshop" in quote:
        FAILURES.append("the setup closing quote names awow-workflows commands whether or not they are installed")
    for word in ("`✓ ok`", "`⧗ incomplete`", "`✗ broken`"):
        if word not in text:
            FAILURES.append(f"--check does not spell out {word}")
    for labels in sorted((REPO_ROOT / "context" / "tooling" / "boards").glob("*/reference/labels.md")):
        if "Prefix scheme: type:* / area:* / status:*" in labels.read_text():
            FAILURES.append(f"{labels.relative_to(REPO_ROOT)} states status:* as observed")


def check_vm_dry_run() -> None:
    text = COMMAND.read_text()
    for needle, what in (
        ("show its State machine table in full", "the diff summarises board.md's approval table"),
        ("**Setup files**, **Shared team repo**, **Board access**", "--check labels its report with internal words"),
        ("`This repo is set up. Next: /my-work`", "--check does not say the repo is set up or name the next command"),
        ("An absent team profile on its own leaves this `✓ ok`", "--check reports a missing profile as incomplete"),
        ("(created on first use)", "the AGENTS.md pointer names proposals/ without saying it appears on first use"),
        ("Which of these connections should I use", "Init lists several connections but never asks which to use"),
    ):
        if needle not in text:
            FAILURES.append(what)


def main() -> int:
    check_flags()
    check_situations()
    check_no_wizard_state()
    check_workshop_moved()
    check_scenarios()
    check_second_dry_run()
    check_vm_dry_run()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Setup contract OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
