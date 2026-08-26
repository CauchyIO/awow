#!/usr/bin/env python3
"""PreToolUse(Write|Edit|NotebookEdit) -> wrong-root write guard (CAU-1335).

An awow artefact — proposals/, the awow context tree, .awow/ state — belongs
to exactly one installation: the git repo the session resolved, or its mapped
hub. The reproduced failure (CAU-1335) is a session anchored at a workspace
root writing board, knowledge-base, and .awow files into a sibling repo after
one generic "go". CLAUDE_PROJECT_DIR is the workspace root in that
configuration, so this guard is git-boundary-aware, not project-dir-aware: it
compares the write target's enclosing git root against the session's.

Verdicts:
  - target root == session root                  -> silent allow
  - target root == mapped hub ($AWOW_HUB, else   -> silent allow
    <session root>/.awow/hub.json "path")
  - anything else, artefact path                 -> permissionDecision "ask",
    naming both roots. Interactively that is one explicit question; in a
    headless run it denies — a loud stop instead of a silent wrong-root write.

Non-artefact paths are never touched. AWOW_WRONG_ROOT_GUARD=off disables the
guard (documented escape hatch for automation that owns its scratch repos).
On malformed input the guard logs to stderr and exits 0 — non-blocking, like
lifecycle-seam-check.
"""

import json
import os
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

# Directory names that mark a path as an awow artefact wherever they appear.
ARTEFACT_SEGMENTS = {"proposals", ".awow"}

# context/ is only an awow tree when the segment after it is one of awow's
# own children — a bare `context` match would false-positive on e.g. React
# src/context/ directories.
AWOW_CONTEXT_CHILDREN = {
    "company", "department", "kb-inbox", "knowledge-base", "knowledge-sources",
    "quarterly", "retros", "team", "tooling",
    "mission.md", "board-scope.md", "do-not-propose.md",
}


def git_root(path):
    """The nearest ancestor of `path` containing .git (dir, or worktree-style
    file), or None. Pure filesystem walk — no subprocess, no network."""
    cur = os.path.abspath(path)
    while True:
        if os.path.exists(os.path.join(cur, ".git")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def is_awow_artefact(path):
    parts = os.path.normpath(path).split(os.sep)
    for i, part in enumerate(parts):
        if part in ARTEFACT_SEGMENTS:
            return True
        if part == "context" and i + 1 < len(parts) and parts[i + 1] in AWOW_CONTEXT_CHILDREN:
            return True
    return False


def mapped_hub(session_root):
    """The hub path this machine has mapped: $AWOW_HUB first, else the
    gitignored .awow/hub.json in the session's repo. Origin verification is
    the session-start hook's job; this guard trusts the recorded mapping."""
    env = os.environ.get("AWOW_HUB", "")
    if env:
        return os.path.abspath(env)
    if not session_root:
        return None
    link = os.path.join(session_root, ".awow", "hub.json")
    try:
        with open(link, encoding="utf-8") as f:
            path = str(json.load(f).get("path", ""))
    except (OSError, ValueError):
        return None
    return os.path.abspath(path) if path else None


def main():
    if os.environ.get("AWOW_WRONG_ROOT_GUARD", "").lower() == "off":
        return

    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stderr.write(
            f"awow wrong-root-guard: could not parse PreToolUse payload "
            f"({exc}); first 200 chars: {raw[:200]!r}\n"
        )
        return

    if data.get("tool_name") not in WRITE_TOOLS:
        return

    tool_input = data.get("tool_input") or {}
    target = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if not target:
        return

    anchor = str(data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    target = os.path.abspath(os.path.join(anchor, os.path.expanduser(target)))

    if not is_awow_artefact(target):
        return

    session_root = git_root(anchor)
    target_root = git_root(os.path.dirname(target))

    if target_root is not None and target_root == session_root:
        return

    hub = mapped_hub(session_root)
    if hub and target_root is not None and target_root == git_root(hub):
        return

    reason = (
        f"awow wrong-root guard: this {data.get('tool_name')} targets an awow "
        f"artefact outside the session's repo — target: {target} "
        f"(enclosing repo: {target_root or 'none — not inside any git repo'}; "
        f"session repo: {session_root or f'none — {anchor} is not inside a git repo'}). "
        f"An awow artefact belongs to the resolved installation or its mapped hub; "
        f"crossing a repo boundary needs the user's explicit confirmation naming "
        f"both repos. Contract: context/tooling/context-resolution.md."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }))


main()
