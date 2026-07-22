#!/usr/bin/env python3
"""Black-box test for the session-start SessionStart hook.

Stdlib only, no pytest. Copies the hook into a temp plugin layout, runs it as
a subprocess, and asserts on the emitted JSON context. Also guards the built
payload: every skill/command path a dist hook probes must resolve inside
dist/ in at least one of its layout variants. Run:
    python3 tests/hooks/test_session_start.py
Exits 0 if all pass, 1 otherwise.
"""

import atexit
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(ROOT, "hooks", "session-start")
DIST = os.path.join(ROOT, "dist")

failures = []


def check(name, cond):
    if cond:
        print(f"PASS {name}")
    else:
        print(f"FAIL {name}")
        failures.append(name)


def _tmpdir():
    d = tempfile.mkdtemp()
    atexit.register(lambda p=d: shutil.rmtree(p, ignore_errors=True))
    return d


def _plugin(payload_skill=None, source_skill=None):
    """Build a temp plugin root containing the hook and optional SKILL.md bodies."""
    d = _tmpdir()
    os.makedirs(os.path.join(d, "hooks"))
    hook = os.path.join(d, "hooks", "session-start")
    shutil.copy(HOOK, hook)
    os.chmod(hook, os.stat(hook).st_mode | stat.S_IXUSR)
    if payload_skill is not None:
        os.makedirs(os.path.join(d, "skills", "using-awow"))
        with open(os.path.join(d, "skills", "using-awow", "SKILL.md"), "w") as f:
            f.write(payload_skill)
    if source_skill is not None:
        os.makedirs(os.path.join(d, ".agents", "skills", "using-awow"))
        with open(os.path.join(d, ".agents", "skills", "using-awow", "SKILL.md"), "w") as f:
            f.write(source_skill)
    return d


def _run(plugin_root):
    """Invoke the hook; return (context string, stderr, returncode)."""
    # An adopted project dir suppresses the setup nudge; isolated HOME keeps the
    # engine glob from seeing the real machine. Plugin-root env vars are
    # stripped so the hook takes the platform-neutral additionalContext branch.
    project = _tmpdir()
    os.makedirs(os.path.join(project, ".agents"))
    open(os.path.join(project, ".agents", "AGENTS.md"), "w").close()
    env = {k: v for k, v in os.environ.items()
           if k not in ("CURSOR_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "COPILOT_CLI")}
    env["CLAUDE_PROJECT_DIR"] = project
    env["HOME"] = project
    p = subprocess.run(
        [os.path.join(plugin_root, "hooks", "session-start")],
        capture_output=True, text=True, env=env,
    )
    context = json.loads(p.stdout)["additionalContext"] if p.returncode == 0 else ""
    return context, p.stderr, p.returncode


# The path prefixes under which the two layouts (payload dist/, source
# checkout) can carry the same skill or command body.
LAYOUT_PREFIXES = ("skills/", ".agents/skills/", "commands/", ".agents/commands/")


def unresolved_probe_groups(dist_root):
    """Scan dist hooks for ${PLUGIN_ROOT}/...*.md references.

    References to the same body via different layout prefixes form one probe
    group; a group is unresolved when none of its variants exists under
    dist_root. Returns {hook name: [unresolved group keys]}.
    """
    bad = {}
    hooks_dir = os.path.join(dist_root, "hooks")
    for name in sorted(os.listdir(hooks_dir)):
        path = os.path.join(hooks_dir, name)
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            refs = re.findall(r'\$\{PLUGIN_ROOT\}/([^"\s]+?\.md)', f.read())
        groups = {}
        for ref in refs:
            key = ref
            for prefix in LAYOUT_PREFIXES:
                if ref.startswith(prefix):
                    key = ref[len(prefix):]
                    break
            groups.setdefault(key, []).append(ref)
        missing = [k for k, variants in groups.items()
                   if not any(os.path.isfile(os.path.join(dist_root, v)) for v in variants)]
        if missing:
            bad[name] = missing
    return bad


# Payload layout (dist install): skill at skills/using-awow/.
ctx, err, rc = _run(_plugin(payload_skill="PAYLOAD-SENTINEL"))
check("payload layout injects the skill", "PAYLOAD-SENTINEL" in ctx)

# Source layout (maintainer checkout): skill at .agents/skills/using-awow/.
ctx, err, rc = _run(_plugin(source_skill="SOURCE-SENTINEL"))
check("source layout injects the skill", "SOURCE-SENTINEL" in ctx)

# Both present: the payload body wins (it is the token-substituted render).
ctx, err, rc = _run(_plugin(payload_skill="PAYLOAD-SENTINEL", source_skill="SOURCE-SENTINEL"))
check("payload body wins over source body", "PAYLOAD-SENTINEL" in ctx and "SOURCE-SENTINEL" not in ctx)

# Neither present: fail LOUD — banner in context, warning on stderr, and never
# the old quiet one-liner that masked the broken 0.5.0 payload. Exit stays 0
# so a broken build degrades the session instead of bricking it.
ctx, err, rc = _run(_plugin())
check("missing bootstrap puts a NOT FOUND banner in context", "NOT FOUND" in ctx)
check("missing bootstrap warns on stderr", "NOT FOUND" in err)
check("missing bootstrap does not inject the quiet error string",
      "Error reading using-awow skill" not in ctx)
check("missing bootstrap still exits 0", rc == 0)

# Payload guard: every probe group a dist hook cats resolves inside dist/.
check("dist hooks probe only paths that exist in the payload",
      unresolved_probe_groups(DIST) == {})

# The payload hook is a verbatim copy — a source edit without a gather rebuild
# is a broken ship.
with open(HOOK) as f_src, open(os.path.join(DIST, "hooks", "session-start")) as f_dist:
    check("dist/hooks/session-start matches hooks/session-start", f_src.read() == f_dist.read())

if failures:
    print(f"\n{len(failures)} failing: {failures}")
    sys.exit(1)
print("\nall passed")
sys.exit(0)
