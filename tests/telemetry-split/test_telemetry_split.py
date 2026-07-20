"""Regression test for the telemetry channel split in tools/gather.py.

Design spec section 4.3: five skills (mlflow-export, prompt-skill-analysis,
project-timeline, awow-usage-coach, session-export) move out of the base plugin
into a second Claude-Code-only plugin built at dist-telemetry/. Four stay
(using-awow, board-aware-development, architecture-aware-development,
user-story-template).

Asserts, in order of how badly each would fail silently:

  1. Channel routing — every skill source declares the channel it should, and
     gather.py's parser agrees with tools/lint-paths.py's independent one on
     every file both scan. Two parsers, one answer.
  2. Placement, both directions — a telemetry skill is under dist-telemetry/
     and under NEITHER dist/skills/ nor dist/agent-skills/; a staying skill is
     the mirror image. A one-directional check passes a skill that shipped
     twice.
  3. Tool split — each plugin carries its own runtime tooling and only its own.
  4. Claude-Code-only — dist-telemetry/ has no Codex manifest, no Pi package,
     no agent-skills surface, and no hooks.
  5. Executable dependencies resolve — every {AWOW_TOOLS} path a telemetry
     skill body names is a file that ships in dist-telemetry/tools/.

Pure stdlib; no pytest, no network.

Run:  python3 tests/telemetry-split/test_telemetry_split.py
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

# tools/lint-paths.py cannot be imported by name — the hyphen is not a valid
# identifier — so load it from its path. Importing it at all is the point: the
# two channel parsers are independent implementations and must not drift.
_spec = importlib.util.spec_from_file_location(
    "lint_paths", REPO_ROOT / "tools" / "lint-paths.py"
)
lint_paths = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint_paths)

FAILURES = []

TELEMETRY_SKILLS = [
    "awow-usage-coach",
    "mlflow-export",
    "project-timeline",
    "prompt-skill-analysis",
    "session-export",
]
STAYING_SKILLS = [
    "architecture-aware-development",
    "board-aware-development",
    "using-awow",
]
# Declarative skills (a bare <name>.md, not a <name>/SKILL.md directory).
STAYING_DECLARATIVE = ["user-story-template"]
VENDORED_SKILLS = ["session-correlation"]
VENDORED_DECLARATIVE = ["agent-directive-voice"]

# The three runtime tools the telemetry skills execute. Kept literal so a new
# {AWOW_TOOLS} reference in a moving skill fails here and forces a decision
# about which plugin ships it, rather than dangling in a built payload.
TELEMETRY_TOOL_FILES = {
    "mlflow_reader.py",
    "session_timeline.py",
    "session_timeline_template.html",
}
BASE_TOOL_FILES = {"hooks/leak-patterns.txt", "hooks/pre-push"}


def skill_text(name: str) -> str:
    path = REPO_ROOT / ".agents" / "skills" / name / "SKILL.md"
    if not path.is_file():
        path = REPO_ROOT / ".agents" / "skills" / (name + ".md")
    return path.read_text()


def files_under(root: Path) -> set:
    if not root.is_dir():
        return set()
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def check_channels() -> None:
    expected = {}
    for n in TELEMETRY_SKILLS:
        expected[n] = "telemetry"
    for n in STAYING_SKILLS + STAYING_DECLARATIVE:
        expected[n] = "both"
    for n in VENDORED_SKILLS + VENDORED_DECLARATIVE:
        expected[n] = "vendored"
    for name, want in sorted(expected.items()):
        got = gather.declared_channel(skill_text(name))
        if got != want:
            FAILURES.append(f"declared_channel({name}) == {got!r}, expected {want!r}")

    # The two predicates must agree with the accessor, not re-derive it.
    for name in TELEMETRY_SKILLS:
        text = skill_text(name)
        if not gather.is_telemetry_channel(text):
            FAILURES.append(f"is_telemetry_channel({name}) is False")
        if gather.is_vendored_channel(text):
            FAILURES.append(f"is_vendored_channel({name}) is True — telemetry is not vendored")

    # gather.py and lint-paths.py parse `channel:` independently. Drift between
    # them silently changes which files get linted.
    for root in (REPO_ROOT / ".agents" / "commands", REPO_ROOT / ".agents" / "skills"):
        for path in sorted(root.rglob("*.md")):
            if path.name == "README.md":
                continue
            text = path.read_text()
            a, b = gather.declared_channel(text), lint_paths.channel(text)
            if a != b:
                rel = path.relative_to(REPO_ROOT)
                FAILURES.append(f"channel parsers disagree on {rel}: gather={a!r} lint={b!r}")


def check_placement() -> None:
    dist_skills = files_under(gather.DIST_DIR / "skills")
    dist_agent = files_under(gather.DIST_DIR / "agent-skills")
    tele_skills = files_under(gather.DIST_TELEMETRY_DIR / "skills")

    def owns(files, name):
        return any(f.split("/")[0] == name for f in files)

    for name in TELEMETRY_SKILLS:
        if not owns(tele_skills, name):
            FAILURES.append(f"{name} is telemetry but absent from dist-telemetry/skills/")
        if owns(dist_skills, name):
            FAILURES.append(f"{name} is telemetry but still in dist/skills/ — it shipped twice")
        if owns(dist_agent, name):
            FAILURES.append(
                f"{name} is telemetry but still in dist/agent-skills/ — it reached "
                "Codex and Pi, which awow-telemetry does not target"
            )
    for name in STAYING_SKILLS + STAYING_DECLARATIVE:
        if not owns(dist_skills, name):
            FAILURES.append(f"{name} stays in the base plugin but is absent from dist/skills/")
        if owns(tele_skills, name):
            FAILURES.append(f"{name} stays in the base plugin but leaked into dist-telemetry/skills/")
    for name in VENDORED_SKILLS + VENDORED_DECLARATIVE:
        if owns(dist_skills, name) or owns(tele_skills, name):
            FAILURES.append(f"{name} is vendored and must ship in no payload")


def check_tools_and_isolation() -> None:
    base_tools = files_under(gather.DIST_DIR / "tools")
    tele_tools = files_under(gather.DIST_TELEMETRY_DIR / "tools")
    if base_tools != BASE_TOOL_FILES:
        FAILURES.append(f"dist/tools/ == {sorted(base_tools)}, expected {sorted(BASE_TOOL_FILES)}")
    if tele_tools != TELEMETRY_TOOL_FILES:
        FAILURES.append(
            f"dist-telemetry/tools/ == {sorted(tele_tools)}, expected {sorted(TELEMETRY_TOOL_FILES)}"
        )

    # Claude-Code-only (design spec 4.3): no Codex manifest, no Pi package, no
    # agent-skills surface, no hooks. The SessionStart hook reads using-awow,
    # which lives in the base plugin — a copy here would inject an error string
    # into every session and double-inject for anyone with both installed.
    for rel in (
        ".codex-plugin/plugin.json",
        "package.json",
        ".agents/plugins/marketplace.json",
        "agent-skills",
        "commands",
        "hooks",
        "context",
    ):
        if (gather.DIST_TELEMETRY_DIR / rel).exists():
            FAILURES.append(f"dist-telemetry/{rel} exists — awow-telemetry is Claude-Code-only")

    # Every {AWOW_TOOLS} path a telemetry skill names must ship beside it.
    import re
    pat = re.compile(r"\{AWOW_TOOLS\}/([A-Za-z0-9_.-]+)")
    for name in TELEMETRY_SKILLS:
        for ref in sorted(set(pat.findall(skill_text(name)))):
            if ref not in TELEMETRY_TOOL_FILES:
                FAILURES.append(
                    f"{name} references {{AWOW_TOOLS}}/{ref}, which dist-telemetry/tools/ "
                    "does not ship — add it to TELEMETRY_TOOL_PATHS or drop the reference"
                )


def check_marketplace() -> None:
    mk = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entries = {p["name"]: p for p in mk.get("plugins", [])}
    if set(entries) != {"awow", "awow-telemetry"}:
        FAILURES.append(
            f"marketplace declares {sorted(entries)}, expected ['awow', 'awow-telemetry']"
        )
        return
    for name, want_source in (("awow", "./dist"), ("awow-telemetry", "./dist-telemetry")):
        got = entries[name].get("source")
        if got != want_source:
            FAILURES.append(f"marketplace entry {name} source == {got!r}, expected {want_source!r}")
        # A source that resolves to nothing is an install failure with no build error.
        target = REPO_ROOT / want_source
        if not (target / ".claude-plugin" / "plugin.json").is_file():
            FAILURES.append(f"{want_source}/.claude-plugin/plugin.json is missing — {name} cannot install")

    # Lockstep (design spec 8): awow-telemetry versions with awow this release.
    canonical = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
    for rel in (
        "dist/.claude-plugin/plugin.json",
        "dist-telemetry/.claude-plugin/plugin.json",
        "dist/.codex-plugin/plugin.json",
        "dist/package.json",
    ):
        built = json.loads((REPO_ROOT / rel).read_text())["version"]
        if built != canonical:
            FAILURES.append(f"{rel} version {built!r} != canonical {canonical!r}")
    if tuple(int(x) for x in canonical.split(".")) < (0, 6, 0):
        FAILURES.append(
            f"version is {canonical} — a second plugin ships this release, so "
            "design spec section 8 requires 0.6.0 minimum"
        )


def main() -> int:
    check_channels()
    check_placement()
    check_tools_and_isolation()
    check_marketplace()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Telemetry split OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
