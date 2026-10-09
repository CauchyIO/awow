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
# The hook is a shim + implementation pair (session-start execs session-start.py);
# fixtures carry both so the temp plugin layout matches a real install.
HOOK_FILES = ("session-start", "session-start.py")
HOOK = os.path.join(ROOT, "hooks", "session-start")
# The Claude Code plugin folder — the payload the hooks ship in (CAU-1653).
DIST = os.path.join(ROOT, "dist", "claude", "awow")

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
    for name in HOOK_FILES:
        hook = os.path.join(d, "hooks", name)
        shutil.copy(os.path.join(ROOT, "hooks", name), hook)
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


def _run(plugin_root, project=None, extra_env=None):
    """Invoke the hook; return (context string, stderr, returncode)."""
    # The default project dir is adopted (vendored), suppressing the setup
    # nudge; isolated HOME keeps the engine glob from seeing the real machine.
    # Plugin-root env vars are stripped so the hook takes the platform-neutral
    # additionalContext branch; AWOW_ANCHOR is stripped for hermeticity.
    if project is None:
        project = _tmpdir()
        os.makedirs(os.path.join(project, ".agents"))
        open(os.path.join(project, ".agents", "AGENTS.md"), "w").close()
    env = {k: v for k, v in os.environ.items()
           if k not in ("CURSOR_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT",
                        "COPILOT_CLI", "AWOW_ANCHOR")}
    env["CLAUDE_PROJECT_DIR"] = project
    env["HOME"] = project
    if extra_env:
        env.update(extra_env)
    p = subprocess.run(
        [os.path.join(plugin_root, "hooks", "session-start")],
        capture_output=True, text=True, env=env,
    )
    context = json.loads(p.stdout)["additionalContext"] if p.returncode == 0 else ""
    return context, p.stderr, p.returncode


def _make_hub(remote):
    """A real git repo whose origin is `remote` — stands in for a hub clone."""
    d = _tmpdir()
    subprocess.run(["git", "init", "-q", d], check=True)
    subprocess.run(["git", "-C", d, "remote", "add", "origin", remote], check=True)
    return d


CONNECTOR_REMOTE = "https://github.com/example/team-hub"


def _spoke_project(hub_key=CONNECTOR_REMOTE, link=None):
    """An anchored repo: root AGENTS.md connector (awow: anchored / anchor:),
    optional .awow/anchor.json link. `link` is (recorded_remote,
    recorded_path) or None for an unmapped repo."""
    d = _tmpdir()
    with open(os.path.join(d, "AGENTS.md"), "w") as f:
        f.write("---\nawow: anchored\nanchor: %s\nproject: demo-spoke\n---\n# Demo\n"
                % hub_key)
    if link is not None:
        os.makedirs(os.path.join(d, ".awow"))
        with open(os.path.join(d, ".awow", "anchor.json"), "w") as f:
            json.dump({"remote": link[0], "path": link[1]}, f)
    return d


def _stamped_plugin(version, digest):
    """A plugin root whose payload carries a build stamp (gather.py schema)."""
    d = _plugin(payload_skill="PAYLOAD-SENTINEL")
    os.makedirs(os.path.join(d, ".claude-plugin"))
    with open(os.path.join(d, ".claude-plugin", "build.json"), "w") as f:
        json.dump({"version": version, "content": "sha256:" + digest}, f)
    return d


def _vendored_project(plugin_name=None, dist_stamp=None, legacy_layout=False):
    """An adopted repo: .agents/AGENTS.md always; optionally a plugin
    manifest naming `plugin_name` ("awow" marks the maintainer repo, anything
    else some other plugin repo) and a build stamp — under dist/claude/awow/,
    or the pre-CAU-1653 dist/ when `legacy_layout`."""
    d = _tmpdir()
    os.makedirs(os.path.join(d, ".agents"))
    open(os.path.join(d, ".agents", "AGENTS.md"), "w").close()
    if plugin_name is not None:
        os.makedirs(os.path.join(d, ".claude-plugin"))
        with open(os.path.join(d, ".claude-plugin", "plugin.json"), "w") as f:
            json.dump({"name": plugin_name, "version": "0.0.0"}, f)
    if dist_stamp is not None:
        payload = ("dist",) if legacy_layout else ("dist", "claude", "awow")
        os.makedirs(os.path.join(d, *payload, ".claude-plugin"))
        with open(os.path.join(d, *payload, ".claude-plugin", "build.json"), "w") as f:
            json.dump({"version": dist_stamp[0],
                       "content": "sha256:" + dist_stamp[1]}, f)
    return d


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

# --- Spoke tiers (AWO-133) -------------------------------------------------
# Every spoke fixture carries the reflex body so tier text is asserted against
# a working bootstrap.
SPOKE_PLUGIN = _plugin(payload_skill="PAYLOAD-SENTINEL")

# Connected: valid link, origin matches the connector remote.
hub = _make_hub(CONNECTOR_REMOTE + ".git")
ctx, err, rc = _run(SPOKE_PLUGIN, project=_spoke_project(link=(CONNECTOR_REMOTE, hub)))
check("connected spoke resolves {ANCHOR} to the recorded path", hub in ctx and "resolves to" in ctx)
check("connected spoke names its hub and project",
      CONNECTOR_REMOTE in ctx and "demo-spoke" in ctx)
check("connected spoke injects the reflex", "PAYLOAD-SENTINEL" in ctx)
check("connected spoke gets no setup nudge", "/setup-awow" not in ctx)
# Normalization: ssh-form connector vs https origin with case drift still connects.
hub_n = _make_hub("https://github.com/Example/Team-Hub")
ctx, _, _ = _run(SPOKE_PLUGIN, project=_spoke_project(
    hub_key="git@github.com:example/team-hub.git", link=("git@github.com:example/team-hub.git", hub_n)))
check("remote normalization equates ssh and https forms", "resolves to" in ctx and hub_n in ctx)

# $AWOW_ANCHOR overrides: no link file, env points at a matching clone.
anchor_env = _make_hub(CONNECTOR_REMOTE)
ctx, _, _ = _run(SPOKE_PLUGIN, project=_spoke_project(link=None), extra_env={"AWOW_ANCHOR": anchor_env})
check("AWOW_ANCHOR env override connects an unmapped anchored repo", "resolves to" in ctx and anchor_env in ctx)

# Unmapped: connector, no link, no env — prompt to register, never a scan
# result. The repair prompt tells the model to write .awow/anchor.json.
ctx, _, _ = _run(SPOKE_PLUGIN, project=_spoke_project(link=None))
check("unmapped spoke prompts to map the anchor",
      "not mapped on this machine" in ctx and ".awow/anchor.json" in ctx)
check("unmapped spoke injects the reflex", "PAYLOAD-SENTINEL" in ctx)

# Drift, moved clone: recorded path no longer a git repo with that origin.
gone = _tmpdir()
ctx, _, _ = _run(SPOKE_PLUGIN, project=_spoke_project(link=(CONNECTOR_REMOTE, os.path.join(gone, "moved-away"))))
check("moved hub clone reports the link out of sync",
      "out of sync" in ctx and "moved-away" in ctx)
check("moved hub clone prompts an update, not a re-scan",
      "update" in ctx and ".awow/anchor.json" in ctx)

# Drift, origin mismatch: path exists but is a different repo.
wrong = _make_hub("https://github.com/example/other-repo")
ctx, _, _ = _run(SPOKE_PLUGIN, project=_spoke_project(link=(CONNECTOR_REMOTE, wrong)))
check("origin-mismatched clone reports the link out of sync and names the expected remote",
      "out of sync" in ctx and CONNECTOR_REMOTE in ctx)

# A root AGENTS.md without an anchor: key is NOT a connector — nudge as usual.
plain = _tmpdir()
with open(os.path.join(plain, "AGENTS.md"), "w") as f:
    f.write("# Just docs, not an awow connector\n")
ctx, _, _ = _run(SPOKE_PLUGIN, project=plain)
check("plain root AGENTS.md gets the first-run pointer", "no board configuration yet" in ctx)

# --- First-run pointer vs. a configured plugin install (CAU-1654, CAU-1645) --
# A plugin install never has .agents/AGENTS.md — that file is the vendored
# tree. What marks a configured repo is context/tooling/board.md, written by
# /setup-awow or on first need. An unconfigured repo gets a pointer that asks
# nothing: no first-reply offer, no opt-out file, no setup wall (CAU-1645).
POINTER = "no board configuration yet"


def _plugin_install(board=False, stale_progress=False):
    d = _tmpdir()
    if board:
        os.makedirs(os.path.join(d, "context", "tooling"))
        open(os.path.join(d, "context", "tooling", "board.md"), "w").close()
    if stale_progress:
        open(os.path.join(d, "setup-progress.md"), "w").close()
    return d


ctx, _, _ = _run(SPOKE_PLUGIN, project=_plugin_install())
check("an unconfigured repo gets the first-run pointer", POINTER in ctx)
check("the pointer never instructs a first-reply offer",
      "IN YOUR FIRST REPLY" not in ctx and "offer once" not in ctx)
check("the pointer names no opt-out file", "no-setup-prompt" not in ctx)
check("the pointer says every command works and names /awow-help",
      "Every awow command works" in ctx and "/awow-help" in ctx)
ctx, _, _ = _run(SPOKE_PLUGIN, project=_plugin_install(board=True))
check("a repo with a board.md gets no pointer", POINTER not in ctx)
# setup-progress.md is an earlier awow's state file: it is not a marker of
# anything, so a repo carrying only that one is still unconfigured.
ctx, _, _ = _run(SPOKE_PLUGIN, project=_plugin_install(stale_progress=True))
check("a stale setup-progress.md alone does not count as configured", POINTER in ctx)
# CAU-1639 retired the engine nudge: it argued for an optional plugin every
# session, half on the strength of a seam that no longer exists. No repo gets
# it now — not a configured plugin install, and not the vendored tree it was
# once keyed on.
ctx, _, _ = _run(SPOKE_PLUGIN, project=_plugin_install(board=True))
check("a configured plugin install gets no engine nudge either",
      "inner-loop build engine" not in ctx)
ctx, _, _ = _run(SPOKE_PLUGIN)
check("a vendored repo gets no engine nudge", "inner-loop build engine" not in ctx)

# --- Vendored drift tier (CAU-1338) -----------------------------------------
# Messages begin "awow drift:", the silence sentinel for every negative check.
STAMPED = _stamped_plugin("0.13.0", "aaaa11112222")

# Maintainer checkout whose dist/ stamp differs from the installed payload:
# the recorded incident shape — warn, naming both stamps and the remedies.
ctx, _, _ = _run(STAMPED, project=_vendored_project(
    plugin_name="awow", dist_stamp=("0.12.0", "bbbb33334444")))
check("maintainer drift names both stamps",
      "0.12.0+bbbb33334444" in ctx and "0.13.0+aaaa11112222" in ctx)
check("maintainer drift explains precedence and the remedies",
      "{ANCHOR}-first" in ctx and "--plugin-dir dist/claude/awow" in ctx)

# A checkout still on the pre-CAU-1653 layout stamps dist/ itself: the hook
# must read it there rather than report the branch as unstamped.
ctx, _, _ = _run(STAMPED, project=_vendored_project(
    plugin_name="awow", dist_stamp=("0.12.0", "bbbb33334444"), legacy_layout=True))
check("legacy-layout maintainer stamp is still read",
      "0.12.0+bbbb33334444" in ctx and "unstamped" not in ctx)
ctx, _, _ = _run(STAMPED, project=_vendored_project(
    plugin_name="awow", dist_stamp=("0.13.0", "aaaa11112222"), legacy_layout=True))
check("legacy-layout matching stamps stay silent", "awow drift" not in ctx)

# Matching stamps: silent.
ctx, _, _ = _run(STAMPED, project=_vendored_project(
    plugin_name="awow", dist_stamp=("0.13.0", "aaaa11112222")))
check("matching stamps stay silent", "awow drift" not in ctx)

# A maintainer branch too old to carry a stamp is behind every stamped
# payload by definition: warn, never fall through to the adopter branch.
ctx, _, _ = _run(STAMPED, project=_vendored_project(plugin_name="awow"))
check("unstamped maintainer checkout warns",
      "unstamped" in ctx and "0.13.0+aaaa11112222" in ctx)

# The maintainer marker is the awow plugin manifest, not any plugin manifest:
# a plugin repo that vendored awow is an adopter, and with no lockfile it has
# no vintage to compare — silent, never "unstamped".
ctx, _, _ = _run(STAMPED, project=_vendored_project(plugin_name="other-plugin"))
check("a non-awow plugin repo that vendored awow stays silent",
      "awow drift" not in ctx)

# Pre-stamp installed payload (no build.json): nothing to compare — silent
# even when the repo looks maximally drifty.
ctx, _, _ = _run(_plugin(payload_skill="PAYLOAD-SENTINEL"),
                 project=_vendored_project(plugin_name="awow"))
check("unstamped installed payload stays silent", "awow drift" not in ctx)

# Payload guard: every probe group a dist hook cats resolves inside dist/.
check("dist hooks probe only paths that exist in the payload",
      unresolved_probe_groups(DIST) == {})

# The payload hooks are verbatim copies — a source edit without a gather
# rebuild is a broken ship.
for name in HOOK_FILES:
    with open(os.path.join(ROOT, "hooks", name)) as f_src, \
         open(os.path.join(DIST, "hooks", name)) as f_dist:
        check(f"dist/claude/awow/hooks/{name} matches hooks/{name}", f_src.read() == f_dist.read())

if failures:
    print(f"\n{len(failures)} failing: {failures}")
    sys.exit(1)
print("\nall passed")
sys.exit(0)
