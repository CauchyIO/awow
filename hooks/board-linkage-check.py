#!/usr/bin/env python3
"""PreToolUse(Skill) -> board-linkage reminder.

Reads the PreToolUse payload on stdin. When the tool being invoked is the
`Skill` tool and the skill is one of the inner-loop engine's lifecycle skills,
emit a one-line board-linkage reminder as additionalContext. Non-blocking: it
never denies the call; on any malformed input it logs to stderr and exits 0 so
the tool call is unaffected.

Scoped to repos that have adopted awow (a .agents/AGENTS.md exists under
CLAUDE_PROJECT_DIR); silent everywhere else.
"""

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


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return  # Empty payload is normal for some harness paths; nothing to do.

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Fail visible (logged with context), then fall through without blocking.
        sys.stderr.write(
            f"awow board-linkage-check: could not parse PreToolUse payload "
            f"({exc}); first 200 chars: {raw[:200]!r}\n"
        )
        return

    if data.get("tool_name") != "Skill":
        return

    # Only nudge inside repos that have adopted awow.
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not os.path.isfile(os.path.join(project_dir, ".agents", "AGENTS.md")):
        return

    tool_input = data.get("tool_input") or {}
    skill = str(tool_input.get("skill", ""))
    bare = skill.split(":")[-1].strip()
    reminder = SEAM.get(bare)
    if not reminder:
        return

    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": f"[awow board-linkage] {reminder}",
        }
    }
    print(json.dumps(out))


main()
