#!/usr/bin/env python3
"""PreToolUse(Skill) -> lifecycle-seam reminders (board + architecture).

Reads the PreToolUse payload on stdin. When the tool being invoked is the
`Skill` tool and the skill is one of the inner-loop engine's lifecycle skills,
emit a one-line board-linkage reminder as additionalContext. Non-blocking: it
never denies the call; on any malformed input it logs to stderr and exits 0 so
the tool call is unaffected.

Scoped to repos that have adopted awow (a .agents/AGENTS.md exists under
CLAUDE_PROJECT_DIR); silent everywhere else.
"""

import glob
import json
import os
import sys

# Engine lifecycle skill -> the board action riveted to that moment.
# Bare skill names; a "plugin:" namespace prefix on the invocation is tolerated.
SEAM = {
    "brainstorming": (
        "Initiative starting — this is your board moment. Find the ticket or "
        "propose one (proposals/ -> approve -> create) before you build."
    ),
    "writing-plans": (
        "Link this plan to the ticket: intent + acceptance criteria in the body, "
        "durable rationale to context/knowledge-base/."
    ),
    "verification-before-completion": (
        "Before you claim done: the ticket only moves to In Review/Done once "
        "verification evidence exists — paste it into a comment."
    ),
    "requesting-code-review": (
        "Move the ticket to In Review and add the 'what to review' comment as you "
        "request the review."
    ),
    "finishing-a-development-branch": (
        "Land the PR, move the ticket to Done, link the PR, and close with a "
        "one-line outcome comment."
    ),
}

# Engine lifecycle skill -> the architecture-plane action riveted to that moment.
# Mirrors SEAM; emitted only when context/tooling/architecture.md exists.
_ARCH_EXEC = (
    "Re-check the plan's architecture-flagged tasks against their governing "
    "ADRs/patterns before building them."
)
ARCH_SEAM = {
    "brainstorming": (
        "Architecture moment — before designing, ask your KB agent whether an "
        "ADR/pattern already covers this; reuse or extend it rather than reinventing."
    ),
    "writing-plans": (
        "Align this plan with the architecture plane: query the governing "
        "ADRs/patterns for its scope, flag the tasks that touch them, "
        "stop-and-surface on conflict, and cite what you checked."
    ),
    "executing-plans": _ARCH_EXEC,
    "subagent-driven-development": _ARCH_EXEC,
    "test-driven-development": _ARCH_EXEC,
}


def architecture_plane_present(project_dir):
    """True if this repo declares an architecture plane (the opt-in pointer).
    The hook stays a dumb nudge: it only checks the pointer exists; the skill
    handles whether a KB agent is actually reachable."""
    return os.path.isfile(
        os.path.join(project_dir, "context", "tooling", "architecture.md")
    )


def superpowers_installed(project_dir):
    """True if the superpowers plugin is present (marketplace cache, user, or
    project scope). Soft-dependency check: keeps the seam explicit even though a
    superpowers skill could not be invoked unless it were installed."""
    home = os.path.expanduser("~")
    patterns = (
        os.path.join(home, ".claude", "plugins", "cache", "*", "superpowers"),
        os.path.join(home, ".claude", "plugins", "*", "superpowers"),
        os.path.join(project_dir, ".claude", "plugins", "*", "superpowers"),
    )
    return any(glob.glob(p) for p in patterns)


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return  # Empty payload is normal for some harness paths; nothing to do.

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Fail visible (logged with context), then fall through without blocking.
        sys.stderr.write(
            f"awow lifecycle-seam-check: could not parse PreToolUse payload "
            f"({exc}); first 200 chars: {raw[:200]!r}\n"
        )
        return

    if data.get("tool_name") != "Skill":
        return

    # Only nudge inside repos that have adopted awow.
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isfile(os.path.join(project_dir, ".agents", "AGENTS.md")):
        return

    # No build engine -> no seam to reinforce. Explicit soft-dependency guard.
    if not superpowers_installed(project_dir):
        return

    tool_input = data.get("tool_input") or {}
    skill = str(tool_input.get("skill", ""))
    bare = skill.split(":")[-1].strip()

    lines = []
    board = SEAM.get(bare)
    if board:
        lines.append(f"[awow board-linkage] {board}")
    if architecture_plane_present(project_dir):
        arch = ARCH_SEAM.get(bare)
        if arch:
            lines.append(f"[awow architecture] {arch}")
    if not lines:
        return

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "\n".join(lines),
        }
    }
    print(json.dumps(out))


main()
