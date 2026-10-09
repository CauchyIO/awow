#!/usr/bin/env python3
"""SessionStart hook for the awow plugin.

Injects the `using-awow` operating reflex into every session, tiered by what
the current repo actually is:

  vendored install      -> full reflex
  connected anchored repo -> reflex + resolved {ANCHOR} pointer
  unmapped anchored repo  -> reflex + one-time map-the-anchor prompt
  drifted anchored repo   -> reflex + update-the-link prompt (loud stop headless)
  plain repo            -> reflex + first-run pointer (asks nothing)

An anchored repo names its anchor with `anchor:` in root AGENTS.md; the local
checkout comes from $AWOW_ANCHOR, else the gitignored .awow/anchor.json.

Invoked through the `session-start` bash shim; run-hook.cmd bridges Windows to
that shim. Decision logic lives in small pure functions; user-facing message
text lives in the constants below — keep the two apart.
"""

import json
import os
import subprocess
import sys

# --- message constants -------------------------------------------------------
# {placeholders} are filled by the tier functions. Wording is asserted by
# tests/hooks/test_session_start.py — change text and tests together.

BOOTSTRAP_MISSING = (
    "⚠️ awow: using-awow bootstrap NOT FOUND under {plugin_root} (probed "
    "skills/ and .agents/skills/). The operating reflex did NOT load — this "
    "plugin build is broken. Report against CauchyIO/awow."
)

PREAMBLE = (
    "You are working in a repo governed by awow — the Agentic Way of Working.\n\n"
    "**Below is your 'awow:using-awow' reflex — how awow expects you to work. "
    "For the team's full conventions read .agents/AGENTS.md; for any other awow "
    "command or skill, use the 'Skill' tool or the slash command.**"
)

ANCHORED_CONNECTED = (
    "<important-reminder>This repo is the awow project \"{project}\", anchored "
    "to {anchor}. {{ANCHOR}} resolves to: {path} — read the team's shared "
    "context, board config, and conventions from that root. {{PROJECT}} is this "
    "repo. Do not re-derive the anchor location or scan for other "
    "candidates.</important-reminder>"
)

ANCHORED_UNMAPPED = (
    "<important-reminder>This repo is anchored to {anchor}, but the anchor is "
    "not mapped on this machine: no .awow/anchor.json and no $AWOW_ANCHOR. IN "
    "YOUR FIRST REPLY, ask the user where their local clone of {anchor} lives "
    "(offer to clone it if they have none), verify that clone's git origin "
    "matches the remote, then write .awow/anchor.json as {{\"remote\": "
    "\"{anchor}\", \"path\": \"<absolute path>\"}}. Never scan for or guess a "
    "location. In a headless run, stop loudly naming this missing link — do "
    "not improvise conventions.</important-reminder>"
)

ANCHORED_DRIFTED = (
    "<important-reminder>This repo is anchored to {anchor}, but the local "
    "anchor link is out of sync: the recorded clone at {path} is missing, "
    "moved, or its git origin no longer matches {anchor}. IN YOUR FIRST REPLY, "
    "prompt the user to update the link — confirm where the anchor clone lives "
    "now, verify its origin against the remote, and rewrite .awow/anchor.json. "
    "Never silently re-scan or fall back to another location. In a headless "
    "run, stop loudly instead.</important-reminder>"
)

FIRST_RUN_POINTER = (
    "<important-reminder>awow is installed, but this repo has no board "
    "configuration yet (no context/tooling/board.md). Every awow command works "
    "as it is: the first one that needs the board asks for it once and offers "
    "/setup-awow to make the answer durable. Do what the user asked; do not put "
    "setup in front of it, and do not offer setup unprompted. /awow-help lists "
    "what is available here.</important-reminder>"
)

VENDORED_DRIFT_MAINTAINER = (
    "<important-reminder>awow drift: this checkout's dist/ payload is "
    "{repo_stamp} but the installed plugin payload is {installed_stamp}. "
    "Machinery reads follow this checkout ({{ANCHOR}}-first), so this session "
    "runs the checkout's vintage — if that is unexpected, rebuild and run the "
    "branch payload (python tools/gather.py && claude --plugin-dir dist/claude/awow) or "
    "re-sync the installed plugin.</important-reminder>"
)

def read_bootstrap(plugin_root):
    """The using-awow reflex body. Payload path first: a plugin install ships
    the token-substituted render at skills/using-awow/; the maintainer checkout
    only has .agents/skills/. A missing bootstrap is a loud banner in context
    AND on stderr — never a quiet one-liner standing in for the reflex."""
    for rel in ("skills/using-awow/SKILL.md", ".agents/skills/using-awow/SKILL.md"):
        path = os.path.join(plugin_root, rel)
        try:
            with open(path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            continue
    banner = BOOTSTRAP_MISSING.format(plugin_root=plugin_root)
    print(banner, file=sys.stderr)
    return banner


def frontmatter_value(path, key):
    """First `key:` value inside a file's leading --- frontmatter block."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            return None
        if line.startswith(key + ":"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def normalize_remote(url):
    """host/owner/repo comparison key per the knowledge-sources contract:
    ignore scheme, credentials, the scp-style colon, an optional .git suffix,
    and a trailing slash; compare case-insensitively."""
    r = url.split("://", 1)[-1]
    r = r.split("@", 1)[-1]
    r = r.replace(":", "/", 1)
    r = r.rstrip("/")
    if r.endswith(".git"):
        r = r[: -len(".git")]
    return r.lower()


def anchor_link_file(repo_dir):
    """The machine-local link file, .awow/anchor.json. An unreadable one is
    the explicit signal (logged, treated as unmapped by the reader below)."""
    return os.path.join(repo_dir, ".awow", "anchor.json")


def read_anchor_link(link_file):
    """(remote, path) from the anchor link file; ("", "") when absent or
    unreadable. An unreadable link is logged and then treated as unmapped —
    the repair prompt tells the user to rewrite it."""
    try:
        with open(link_file, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        return "", ""
    except ValueError as exc:
        print(f"awow session-start: unreadable {link_file}: {exc}", file=sys.stderr)
        return "", ""
    return str(data.get("remote", "")), str(data.get("path", ""))


def clone_origin(path):
    """The clone's origin remote, or "" when the path is not such a clone.
    One local git call — resolution never scans and never touches the network."""
    try:
        p = subprocess.run(
            ["git", "-C", path, "config", "--get", "remote.origin.url"],
            capture_output=True, text=True,
        )
    except (OSError, FileNotFoundError) as exc:
        print(f"awow session-start: git unavailable for {path}: {exc}", file=sys.stderr)
        return ""
    return p.stdout.strip() if p.returncode == 0 else ""


def anchored_context(repo_dir):
    """Tier message for an anchored repo, or None when this repo is not one.

    An anchored repo commits its identity in root AGENTS.md frontmatter
    (awow: anchored / anchor: <git remote URL> / project: <name>). Detection
    keys on the `anchor:` key, never on file presence — many repos carry a
    plain AGENTS.md that has nothing to do with awow. The anchor's local path
    is machine-local state, resolved once at registration and read from the
    gitignored .awow/anchor.json ($AWOW_ANCHOR overrides)."""
    if os.path.isfile(os.path.join(repo_dir, ".agents", "AGENTS.md")):
        return None
    connector = os.path.join(repo_dir, "AGENTS.md")
    anchor = frontmatter_value(connector, "anchor")
    if not anchor:
        return None

    project = frontmatter_value(connector, "project") or os.path.basename(repo_dir)
    want = normalize_remote(anchor)

    recorded_remote = ""
    candidate = os.environ.get("AWOW_ANCHOR", "")
    if not candidate:
        recorded_remote, candidate = read_anchor_link(anchor_link_file(repo_dir))
    if not candidate:
        return ANCHORED_UNMAPPED.format(anchor=anchor)

    origin_matches = normalize_remote(clone_origin(candidate)) == want
    record_matches = not recorded_remote or normalize_remote(recorded_remote) == want
    if origin_matches and record_matches:
        return ANCHORED_CONNECTED.format(project=project, anchor=anchor, path=candidate)
    return ANCHORED_DRIFTED.format(anchor=anchor, path=candidate)


def read_json_file(path):
    """Parsed JSON object at path; None when the file is absent (the normal
    case for every optional marker below) or not a JSON object. A present but
    unparseable file is logged, then treated as absent — the drift tier must
    degrade to silence on corruption, never crash the session."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        return None
    except ValueError as exc:
        print(f"awow session-start: unreadable {path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(data, dict):
        print(f"awow session-start: {path} is not a JSON object", file=sys.stderr)
        return None
    return data


def read_stamp(root):
    """(version, digest) from <root>/.claude-plugin/build.json, or None when
    absent or unreadable. Payloads predating the stamp have no file; the
    caller treats None on the installed side as nothing-to-compare."""
    data = read_json_file(os.path.join(root, ".claude-plugin", "build.json"))
    if data is None:
        return None
    version = str(data.get("version", ""))
    digest = str(data.get("content", ""))
    if digest.startswith("sha256:"):
        digest = digest[len("sha256:"):]
    if not version or not digest:
        return None
    return version, digest


def stamp_display(stamp):
    return "%s+%s" % stamp


def maintainer_checkout(repo_dir):
    """True only for the awow maintainer repo: a .claude-plugin/plugin.json
    naming the awow plugin. Bare manifest presence is not enough — a plugin
    repo that vendored awow is an adopter, and must be classified as one."""
    data = read_json_file(os.path.join(repo_dir, ".claude-plugin", "plugin.json"))
    return data is not None and data.get("name") == "awow"


def vendored_drift_context(plugin_root, repo_dir):
    """Tier message when the awow maintainer checkout's dist/ stamp differs
    from the installed payload; None when aligned, undecidable, or when this
    is not the maintainer repo (CAU-1338). A checkout with no dist/ stamp at
    all predates stamping and is behind every stamped payload by definition.
    The compare fires in both directions: a stale plugin cache is as silent
    as a stale branch."""
    installed = read_stamp(plugin_root)
    if installed is None or not maintainer_checkout(repo_dir):
        return None
    # dist/claude/awow/ since the per-harness layout (CAU-1653); dist/ is
    # the layout before it, still what an older branch of the repo builds.
    local = (read_stamp(os.path.join(repo_dir, "dist", "claude", "awow"))
             or read_stamp(os.path.join(repo_dir, "dist")))
    if local is None:
        return VENDORED_DRIFT_MAINTAINER.format(
            repo_stamp="unstamped (predates build stamps)",
            installed_stamp=stamp_display(installed))
    if local != installed:
        return VENDORED_DRIFT_MAINTAINER.format(
            repo_stamp=stamp_display(local),
            installed_stamp=stamp_display(installed))
    return None


def board_configured(repo_dir):
    """Whether this repo names its board: context/tooling/board.md exists.

    A plugin install never has .agents/AGENTS.md — that file IS the vendored
    tree — so "adopted" alone reads every configured plugin install as new
    (CAU-1654). board.md is the one marker: written by /setup-awow, or on first
    need by the first command that asked for the board."""
    return os.path.isfile(os.path.join(repo_dir, "context", "tooling", "board.md"))


def build_context(plugin_root, repo_dir):
    adopted = os.path.isfile(os.path.join(repo_dir, ".agents", "AGENTS.md"))
    anchored = anchored_context(repo_dir)

    sections = [PREAMBLE, read_bootstrap(plugin_root)]
    if anchored is not None:
        sections.append(anchored)
    # First-run pointer: a repo that is neither vendored nor anchored and names
    # no board. It asks nothing, so it needs no opt-out (CAU-1645). A
    # connectable anchored repo gets its tier message instead.
    elif not adopted and not board_configured(repo_dir):
        sections.append(FIRST_RUN_POINTER)
    # Maintainer drift: warn when this checkout's dist/ stamp differs from the
    # installed payload (CAU-1338). Keyed on the awow plugin manifest, not on
    # `adopted`, so the tier is inert for every other repo.
    if anchored is None:
        drift = vendored_drift_context(plugin_root, repo_dir)
        if drift is not None:
            sections.append(drift)
    return "<EXTREMELY_IMPORTANT>\n" + "\n\n".join(sections) + "\n</EXTREMELY_IMPORTANT>"


def main():
    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    context = build_context(plugin_root, repo_dir)

    # Each platform reads a different field:
    #   Cursor       -> additional_context (top-level, snake_case)
    #   Claude Code  -> hookSpecificOutput.additionalContext (nested)
    #   Copilot CLI / SDK standard -> additionalContext (top-level)
    # Claude Code reads BOTH additional_context and hookSpecificOutput without
    # deduplication, so emit only the field the current platform consumes.
    if os.environ.get("CURSOR_PLUGIN_ROOT"):
        payload = {"additional_context": context}
    elif os.environ.get("CLAUDE_PLUGIN_ROOT") and not os.environ.get("COPILOT_CLI"):
        payload = {"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": context}}
    else:
        payload = {"additionalContext": context}
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
