"""Command-surface integrity over the built payloads.

`gather.py --check` proves dist/ matches what the generator would produce; it
cannot tell you the generator planned the wrong *place*. Two invariants that
only the payload on disk can witness:

1. **Everything in a command directory is a command.** Claude Code and Copilot
   auto-discover `commands/` and `.github/prompts/` from the payload root, so a
   file dropped there without frontmatter surfaces as a description-less entry
   in the user's picker — and fails `claude plugin validate --strict`. That is
   how the archetype handler registries came to ship as commands (AWO-161).

2. **Every rooted handler path a prompt names resolves.** The routers reach
   their handler registries by a payload-rooted path, rendered per channel:
   `${CLAUDE_PLUGIN_ROOT}/...` for Claude and Copilot, `../../...` (relative to
   the skill directory) for Codex and Pi. Relocating the registries without
   moving both renderings leaves the routers silently handler-less at runtime,
   which no manifest or drift check would notice.

Pure stdlib; no pytest, no network. The frontmatter probe is deliberately
independent of `gather.parse_frontmatter` — the invariant under test is what a
harness sees in the shipped file, not what the generator believes it wrote.

Run:  python3 tests/payload-commands/test_command_surface.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_ROOTS = ("dist", "dist-telemetry")

# Directories a harness auto-discovers commands/prompts from, relative to a
# payload root. Every .md below one of these must be an invokable command.
COMMAND_DIRS = ("commands", ".github/prompts")

# A path token ending in a handler-registry directory name, e.g.
# "${CLAUDE_PLUGIN_ROOT}/handlers/_workitem-archetypes" or "../../handlers/
# _meeting-archetypes". Stops at whitespace and markdown quoting so the
# surrounding prose never joins the path.
HANDLER_REF = re.compile(r"[^\s`'\"()\[\]]*_(?:workitem|meeting)-archetypes")

PLUGIN_ROOT_TOKEN = "${CLAUDE_PLUGIN_ROOT}/"
SKILL_RELATIVE_TOKEN = "../../"

FAILURES: list[str] = []


def has_frontmatter_description(text: str) -> bool:
    """What a harness looks for: a leading `--- ... ---` block carrying a
    description. Anything else is not an invokable command."""
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    return re.search(r"^description:\s*\S", text[4:end], re.M) is not None


def check_command_dirs() -> None:
    for root_name in PAYLOAD_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for rel in COMMAND_DIRS:
            for path in sorted((root / rel).rglob("*.md")):
                if has_frontmatter_description(path.read_text()):
                    continue
                FAILURES.append(
                    f"{path.relative_to(REPO_ROOT)}: sits in an auto-discovered "
                    f"command directory but carries no frontmatter description, "
                    f"so it ships as a description-less picker entry"
                )


def resolve_handler_ref(path: Path, root: Path, ref: str) -> Path | None:
    """The directory `ref` points at, or None when it is not payload-rooted.

    Unrooted references — the `{ANCHOR}/...` vendored fallback, or a bare
    `_workitem-archetypes/` mentioned in prose — name no payload location and
    are out of scope here.
    """
    if ref.startswith(PLUGIN_ROOT_TOKEN):
        return root / ref[len(PLUGIN_ROOT_TOKEN):]
    if ref.startswith(SKILL_RELATIVE_TOKEN):
        # Agent Skills resolve relative to the skill directory — the file's own
        # parent, which is where the harness cds before reading the body.
        return (path.parent / ref).resolve()
    return None


def check_handler_refs() -> None:
    resolved = 0
    for root_name in PAYLOAD_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            for ref in HANDLER_REF.findall(path.read_text()):
                target = resolve_handler_ref(path, root, ref)
                if target is None:
                    continue
                resolved += 1
                if not target.is_dir():
                    FAILURES.append(
                        f"{path.relative_to(REPO_ROOT)}: handler path {ref!r} "
                        f"resolves to {target}, which does not exist"
                    )
                elif not any(target.glob("*.md")):
                    FAILURES.append(
                        f"{path.relative_to(REPO_ROOT)}: handler path {ref!r} "
                        f"resolves to {target}, which holds no handlers"
                    )
    if resolved == 0:
        FAILURES.append(
            "no payload-rooted handler reference found in any payload — the "
            "routers can no longer be reaching their registries, or this check "
            "has gone vacuous"
        )


def main() -> int:
    check_command_dirs()
    check_handler_refs()
    for failure in FAILURES:
        print(failure)
    if FAILURES:
        print(f"\n{len(FAILURES)} command-surface failure(s).", file=sys.stderr)
        return 1
    print("Payload command surface clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
