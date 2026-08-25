#!/usr/bin/env python3
"""Black-box test for the wrong-root-guard PreToolUse hook (CAU-1335).

Stdlib only, no pytest — same harness as test_lifecycle_seam_check.py.
Invokes the hook as a subprocess with a controlled payload and asserts on
stdout. Run:
    python3 tests/hooks/test_wrong_root_guard.py
Exits 0 if all pass, 1 otherwise.
"""

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(__file__), "..", "..", "hooks", "wrong-root-guard.py")

failures = []


def _workspace():
    """A temp workspace root (NOT a git repo) to build repos under."""
    d = tempfile.mkdtemp()
    atexit.register(lambda p=d: shutil.rmtree(p, ignore_errors=True))
    return d


def _repo(parent, name, git=True, gitfile=False):
    """A child directory; a git repo when git=True (a worktree-style .git FILE
    when gitfile=True)."""
    d = os.path.join(parent, name)
    os.makedirs(d, exist_ok=True)
    if git:
        if gitfile:
            with open(os.path.join(d, ".git"), "w") as f:
                f.write("gitdir: /somewhere/else\n")
        else:
            os.makedirs(os.path.join(d, ".git"), exist_ok=True)
    return d


def _run(file_path, cwd, tool="Write", extra_env=None, raw=None,
         project_dir=None):
    """Invoke the hook; return (stdout, stderr)."""
    payload = raw if raw is not None else json.dumps(
        {"tool_name": tool, "tool_input": {"file_path": file_path}, "cwd": cwd}
    )
    env = dict(os.environ)
    env.pop("AWOW_HUB", None)
    env.pop("AWOW_WRONG_ROOT_GUARD", None)
    env["CLAUDE_PROJECT_DIR"] = project_dir if project_dir is not None else cwd
    if extra_env:
        env.update(extra_env)
    p = subprocess.run(
        [sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env
    )
    if p.returncode != 0:
        failures.append(f"hook exited {p.returncode}, stderr={p.stderr!r}")
    return p.stdout, p.stderr


def _decision(stdout):
    """The permissionDecision in the hook's output, or None for silent allow."""
    if not stdout.strip():
        return None
    out = json.loads(stdout)
    return out["hookSpecificOutput"].get("permissionDecision")


def check(name, cond, detail=""):
    if not cond:
        failures.append(f"{name}: {detail}")
        print(f"FAIL {name} {detail}")
    else:
        print(f"ok   {name}")


# --- same-repo writes are silent allows ------------------------------------

ws = _workspace()
repo_a = _repo(ws, "repo-a")
repo_b = _repo(ws, "repo-b")

out, _ = _run(os.path.join(repo_a, "proposals", "x.md"), cwd=repo_a)
check("same-repo proposals write allowed", _decision(out) is None, out)

out, _ = _run(os.path.join(repo_a, "context", "knowledge-base", "d.md"), cwd=repo_a)
check("same-repo kb write allowed", _decision(out) is None, out)

out, _ = _run(os.path.join(repo_a, ".awow", "board-session.md"), cwd=repo_a)
check("same-repo .awow write allowed", _decision(out) is None, out)

# --- cross-repo artefact writes ask ----------------------------------------

out, _ = _run(os.path.join(repo_b, "proposals", "x.md"), cwd=repo_a)
check("cross-repo proposals write asks", _decision(out) == "ask", out)

out, _ = _run(os.path.join(repo_b, "context", "tooling", "board.md"), cwd=repo_a, tool="Edit")
check("cross-repo board edit asks", _decision(out) == "ask", out)

out, _ = _run(os.path.join(repo_b, "context", "team", "conventions", "c.md"), cwd=repo_a)
check("cross-repo team-context write asks", _decision(out) == "ask", out)

reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
check("ask reason names both roots",
      repo_b in reason and repo_a in reason, reason)

# --- the reproduced configuration: CWD at a bare workspace root ------------

out, _ = _run(os.path.join(repo_b, "context", "tooling", "board.md"), cwd=ws)
check("workspace-root cwd, child-repo board write asks", _decision(out) == "ask", out)

out, _ = _run(os.path.join(ws, ".awow", "board-session.md"), cwd=ws)
check("artefact write outside any git repo asks", _decision(out) == "ask", out)

# --- non-artefact paths never trigger, even across repos --------------------

out, _ = _run(os.path.join(repo_b, "src", "main.py"), cwd=repo_a)
check("cross-repo non-artefact write allowed", _decision(out) is None, out)

out, _ = _run(os.path.join(repo_b, "src", "context", "AppContext.tsx"), cwd=repo_a)
check("non-awow context/ dir not matched", _decision(out) is None, out)

# --- the mapped hub is an allowed root -------------------------------------

hub = _repo(ws, "hub-clone")
os.makedirs(os.path.join(repo_a, ".awow"), exist_ok=True)
with open(os.path.join(repo_a, ".awow", "hub.json"), "w") as f:
    json.dump({"remote": "git@example.com:org/hub.git", "path": hub}, f)

out, _ = _run(os.path.join(hub, "context", "knowledge-base", "d.md"), cwd=repo_a)
check("hub write allowed via .awow/hub.json", _decision(out) is None, out)

hub2 = _repo(ws, "hub-two")
out, _ = _run(os.path.join(hub2, "context", "knowledge-base", "d.md"), cwd=repo_a,
              extra_env={"AWOW_HUB": hub2})
check("hub write allowed via $AWOW_HUB", _decision(out) is None, out)

out, _ = _run(os.path.join(repo_b, "proposals", "x.md"), cwd=repo_a)
check("non-hub sibling still asks with hub mapped", _decision(out) == "ask", out)

# --- worktree-style .git file counts as a repo boundary ---------------------

wt = _repo(ws, "worktree-repo", gitfile=True)
out, _ = _run(os.path.join(wt, "proposals", "x.md"), cwd=wt)
check("gitfile repo: same-root write allowed", _decision(out) is None, out)

out, _ = _run(os.path.join(wt, "proposals", "x.md"), cwd=repo_a)
check("gitfile repo: cross-root write asks", _decision(out) == "ask", out)

# --- relative paths resolve against the session cwd -------------------------

out, _ = _run(os.path.join("proposals", "x.md"), cwd=repo_a)
check("relative same-repo write allowed", _decision(out) is None, out)

out, _ = _run(os.path.join("..", "repo-b", "proposals", "x.md"), cwd=repo_a)
check("relative cross-repo write asks", _decision(out) == "ask", out)

# --- escape hatch and robustness -------------------------------------------

out, _ = _run(os.path.join(repo_b, "proposals", "x.md"), cwd=repo_a,
              extra_env={"AWOW_WRONG_ROOT_GUARD": "off"})
check("AWOW_WRONG_ROOT_GUARD=off silences the guard", _decision(out) is None, out)

out, _ = _run("", cwd=repo_a, raw="this is not json")
check("malformed payload: silent, non-blocking", out.strip() == "", out)

out, _ = _run("", cwd=repo_a, raw=json.dumps({"tool_name": "Read",
              "tool_input": {"file_path": os.path.join(repo_b, "proposals", "x.md")},
              "cwd": repo_a}))
check("non-write tool ignored", out.strip() == "", out)

out, _ = _run("", cwd=repo_a, raw=json.dumps({"tool_name": "Write",
              "tool_input": {}, "cwd": repo_a}))
check("missing file_path: silent", out.strip() == "", out)

# NotebookEdit uses notebook_path
out, _ = _run("", cwd=repo_a, raw=json.dumps({"tool_name": "NotebookEdit",
              "tool_input": {"notebook_path": os.path.join(repo_b, "proposals", "n.ipynb")},
              "cwd": repo_a}))
check("NotebookEdit cross-repo asks", _decision(out) == "ask", out)

# --- verdict ----------------------------------------------------------------

print()
if failures:
    print(f"{len(failures)} failure(s)")
    sys.exit(1)
print("all passed")
