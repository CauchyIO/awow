"""Regression test for the lifecycle and story skill retirement (CAU-1639).

board-aware-development, architecture-aware-development and user-story-template
stop existing as standalone, separately-invocable forms. What each was *for*
survives somewhere that already fires at that moment — this test is what keeps
"retired" from meaning "lost".

Asserts, in order of how badly each would fail silently:

  1. Gone — the three names appear in no prompt source and no built payload,
     and no payload ships a skill folder for them. A name left in one harness's
     payload is a skill that still loads for those users only.
  2. The PreToolUse hook is deregistered and its files are gone. hooks.json
     registers SessionStart and nothing else; the seam hook cannot fire from a
     manifest that does not name it.
  3. The engine nudge is gone from the session-start hook. It argued for an
     optional plugin every session, half on the strength of the seam this
     change deletes.
  4. The story shape survives as a resource of workitem-write, and reaches
     every payload root that ships that skill — the shape is what /refinement-prep
     and the drafter actually apply.
  5. using-awow carries the board beats, and /process-workitem carries the
     architecture-plane check gated on the pointer file. These are the two new
     homes; an empty home is the failure mode this whole item risks.

Pure stdlib; no pytest, no network.

Run:  python3 tests/lifecycle-retired/test_retired.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS = REPO_ROOT / ".agents"
DIST = REPO_ROOT / "dist"
HOOKS = REPO_ROOT / "hooks"

RETIRED = ("board-aware-development", "architecture-aware-development", "user-story-template")

FAILURES: list[str] = []


def check_names_gone() -> None:
    """No source or payload text names a retired skill. proposals/ is exempt:
    the design records that argued for them stay as history."""
    roots = [AGENTS, DIST, HOOKS, REPO_ROOT / "tests", REPO_ROOT / "tools", REPO_ROOT / "context"]
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in (".md", ".py", ".json", ".yml", ".yaml", ".sh"):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel.startswith("tests/lifecycle-retired/"):
                continue  # this file names them on purpose
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            for name in RETIRED:
                if name in text:
                    FAILURES.append(f"{rel} still names `{name}` — CAU-1639 retired it")

    # A skill folder anywhere under dist/ is a skill that still loads.
    for path in sorted(DIST.rglob("SKILL.md")):
        if path.parent.name in RETIRED:
            FAILURES.append(f"{path.relative_to(REPO_ROOT)} — a retired skill still ships")


def check_hook_deregistered() -> None:
    manifest = json.loads((HOOKS / "hooks.json").read_text())
    events = sorted(manifest.get("hooks", {}))
    if events != ["SessionStart"]:
        FAILURES.append(f"hooks/hooks.json registers {events}, expected ['SessionStart'] only")
    for rel in ("hooks/lifecycle-seam-check", "hooks/lifecycle-seam-check.py",
                "tests/hooks/test_lifecycle_seam_check.py"):
        if (REPO_ROOT / rel).exists():
            FAILURES.append(f"{rel} still exists — the PreToolUse hook is retired with the seam")
    # Every built payload that carries hooks must carry the same manifest.
    for built in sorted(DIST.rglob("hooks/hooks.json")):
        if sorted(json.loads(built.read_text()).get("hooks", {})) != ["SessionStart"]:
            FAILURES.append(f"{built.relative_to(REPO_ROOT)} still registers a PreToolUse hook")


def check_engine_nudge_gone() -> None:
    for path in sorted(REPO_ROOT.rglob("session-start.py")):
        if "/proposals/" in path.as_posix():
            continue
        text = path.read_text()
        for marker in ("ENGINE_NUDGE", "no-engine-prompt", "engine_installed"):
            if marker in text:
                FAILURES.append(
                    f"{path.relative_to(REPO_ROOT)} still carries {marker} — the engine nudge is retired"
                )


def check_story_shape_ships() -> None:
    source = AGENTS / "skills" / "workitem-write" / "story-shape.md"
    if not source.is_file():
        FAILURES.append(".agents/skills/workitem-write/story-shape.md is missing — the story shape has no home")
        return
    text = source.read_text()
    for needle in ("What every story has", "Anti-patterns", "Make it yours"):
        if needle not in text:
            FAILURES.append(f"story-shape.md lost '{needle}' — the shape must survive the move intact")

    # It travels with workitem-write: wherever that skill ships, so does this file.
    homes = {p.parent for p in DIST.rglob("workitem-write/SKILL.md")}
    if not homes:
        FAILURES.append("no payload ships workitem-write — cannot verify the story shape travels")
    for home in sorted(homes):
        if not (home / "story-shape.md").is_file():
            FAILURES.append(
                f"{home.relative_to(REPO_ROOT)}/story-shape.md is missing — the shape did not travel "
                "with the skill that applies it"
            )

    # Every body that applies the shape names the file, not a retired skill.
    for rel in (".agents/commands/refinement-prep.md",
                ".agents/commands/process-workitem.md",
                ".agents/skills/workitem-write/SKILL.md"):
        if "story-shape.md" not in (REPO_ROOT / rel).read_text():
            FAILURES.append(f"{rel} applies the story shape but names no source for it")


def check_new_homes() -> None:
    reflex = (AGENTS / "skills" / "using-awow" / "SKILL.md").read_text()
    if "## Through the build" not in reflex:
        FAILURES.append("using-awow has no 'Through the build' section — the board beats have no home")
    for beat in ("In Progress", "In Review", "Done"):
        if beat not in reflex:
            FAILURES.append(f"using-awow's build section never names {beat} — the beat is lost")
    if "evidence" not in reflex.lower():
        FAILURES.append("using-awow does not gate In Review / Done on verification evidence")

    flow = (AGENTS / "commands" / "process-workitem.md").read_text()
    if "{ANCHOR}/context/tooling/architecture.md" not in flow:
        FAILURES.append("/process-workitem does not read the architecture pointer — the plane check is lost")
    for needle in ("checked against", "strictness"):
        if needle not in flow:
            FAILURES.append(f"/process-workitem's plane check lost '{needle}'")
    # The check is config-gated: inert where no plane is declared.
    if "No such file" not in flow:
        FAILURES.append("/process-workitem's plane check is not gated on the pointer's absence")


def main() -> int:
    check_names_gone()
    check_hook_deregistered()
    check_engine_nudge_gone()
    check_story_shape_ships()
    check_new_homes()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Lifecycle and story skill retirement OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
