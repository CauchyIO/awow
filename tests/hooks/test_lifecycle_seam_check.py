#!/usr/bin/env python3
"""Black-box test for the lifecycle-seam-check PreToolUse hook.

Stdlib only, no pytest. Invokes the hook as a subprocess with a controlled
CLAUDE_PROJECT_DIR and stdin payload, and asserts on stdout. Run:
    python3 tests/hooks/test_lifecycle_seam_check.py
Exits 0 if all pass, 1 otherwise.
"""

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "..", "hooks", "lifecycle-seam-check.py")

failures = []


def _project(adopted=True, engine=True, plane=False):
    """Build a temp project dir with the requested gates satisfied; return its path."""
    d = tempfile.mkdtemp()
    if adopted:
        os.makedirs(os.path.join(d, ".agents"), exist_ok=True)
        open(os.path.join(d, ".agents", "AGENTS.md"), "w").close()
    if engine:
        os.makedirs(os.path.join(d, ".claude", "plugins", "sp", "superpowers"), exist_ok=True)
    if plane:
        os.makedirs(os.path.join(d, "context", "tooling"), exist_ok=True)
        open(os.path.join(d, "context", "tooling", "architecture.md"), "w").close()
    return d


def _run(skill, project_dir, raw=None):
    """Invoke the hook; return stdout string."""
    payload = raw if raw is not None else json.dumps(
        {"tool_name": "Skill", "tool_input": {"skill": skill}}
    )
    env = dict(os.environ, CLAUDE_PROJECT_DIR=project_dir)
    p = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env
    )
    assert p.returncode == 0, f"hook exited {p.returncode}, stderr={p.stderr!r}"
    return p.stdout


def check(name, cond):
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}")
        failures.append(name)


# Architecture line fires for each lifecycle skill WHEN the plane is present.
for skill in ("brainstorming", "writing-plans", "executing-plans",
              "subagent-driven-development", "test-driven-development"):
    d = _project(plane=True)
    out = _run(skill, d)
    check(f"arch line present for {skill} (plane present)", "[awow architecture]" in out)

# Architecture line is ABSENT when no pointer file exists.
d = _project(plane=False)
out = _run("writing-plans", d)
check("arch line absent without plane", "[awow architecture]" not in out)

# writing-plans co-emits BOTH lines when the plane is present.
d = _project(plane=True)
out = _run("writing-plans", d)
check("board line present for writing-plans", "[awow board-linkage]" in out)
check("co-emit both lines for writing-plans", "[awow board-linkage]" in out and "[awow architecture]" in out)

# Malformed and empty stdin: exit 0, no output.
d = _project(plane=True)
check("malformed stdin -> no output", _run("", d, raw="{not json") == "")
check("empty stdin -> no output", _run("", d, raw="") == "")

if failures:
    print(f"\n{len(failures)} failing: {failures}")
    sys.exit(1)
print("\nall passed")
sys.exit(0)
