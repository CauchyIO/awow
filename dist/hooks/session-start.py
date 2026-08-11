#!/usr/bin/env python3
"""SessionStart hook for the awow plugin.

Injects the `using-awow` operating reflex into every session, tiered by what
the current repo actually is:

  vendored install  -> full reflex (plus engine nudge when no build engine)
  connected spoke   -> reflex + resolved {HUB} pointer
  unmapped spoke    -> reflex + one-time map-the-hub prompt
  drifted spoke     -> reflex + update-the-link prompt (loud stop headless)
  plain repo        -> reflex + one-time /setup-awow nudge

Invoked through the `session-start` bash shim (same pattern as
lifecycle-seam-check); run-hook.cmd bridges Windows to that shim. Decision
logic lives in small pure functions; user-facing message text lives in the
constants below — keep the two apart.
"""

import glob
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

SPOKE_CONNECTED = (
    "<important-reminder>This repo is the awow spoke \"{project}\" of hub "
    "{hub}. {{HUB}} resolves to: {path} — read the team's shared context, board "
    "config, and conventions from that root. {{PROJECT}} is this repo. Do not "
    "re-derive the hub location or scan for other candidates.</important-reminder>"
)

SPOKE_UNMAPPED = (
    "<important-reminder>This repo is an awow spoke of hub {hub}, but the hub "
    "is not mapped on this machine: no .awow/hub.json and no $AWOW_HUB. IN YOUR "
    "FIRST REPLY, ask the user where their local clone of {hub} lives (offer to "
    "clone it if they have none), verify that clone's git origin matches the "
    "remote, then write .awow/hub.json as {{\"remote\": \"{hub}\", \"path\": "
    "\"<absolute path>\"}}. Never scan for or guess a location. In a headless "
    "run, stop loudly naming this missing link — do not improvise "
    "conventions.</important-reminder>"
)

SPOKE_DRIFTED = (
    "<important-reminder>This repo is an awow spoke of hub {hub}, but the local "
    "hub link is out of sync: the recorded clone at {path} is missing, moved, "
    "or its git origin no longer matches {hub}. IN YOUR FIRST REPLY, prompt the "
    "user to update the link — confirm where the hub clone lives now, verify "
    "its origin against the remote, and rewrite .awow/hub.json. Never silently "
    "re-scan or fall back to another location. In a headless run, stop loudly "
    "instead.</important-reminder>"
)

SETUP_NUDGE = (
    "<important-reminder>This repo has the awow plugin enabled but has not "
    "adopted awow yet (no .agents/AGENTS.md). IN YOUR FIRST REPLY, offer once "
    "to run /setup-awow to bring the board-linked way of working into this repo "
    "— standalone, or connected as a spoke of an existing team hub. If the user "
    "declines, create an empty file at .awow/no-setup-prompt so this nudge "
    "stops, and do not ask again this session.</important-reminder>"
)

ENGINE_NUDGE = (
    "<important-reminder>This awow repo has no inner-loop build engine "
    "installed. superpowers is the recommended optional engine for the build "
    "step (TDD-gated build then review), and the board-aware-development seam "
    "lights up when it is present. IN YOUR FIRST REPLY, mention once that it is "
    "available and can be added via /setup-awow (Step 8 — surface the extras); "
    "awow runs on its baseline without it, so keep it light. If the user is not "
    "interested, create an empty file at .awow/no-engine-prompt so this stops, "
    "and do not raise it again this session.</important-reminder>"
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


def read_hub_link(link_file):
    """(remote, path) from .awow/hub.json; ("", "") when absent or unreadable.
    An unreadable link is logged and then treated as unmapped — the repair
    prompt tells the user to rewrite it."""
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


def spoke_context(repo_dir):
    """Tier message for a spoke repo, or None when this repo is not a spoke.

    A connected spoke commits its identity in root AGENTS.md frontmatter
    (awow: spoke / hub: <git remote URL> / project: <name>). Detection keys on
    the `hub:` key, never on file presence — many repos carry a plain
    AGENTS.md that has nothing to do with awow. The hub's local path is
    machine-local state, resolved once at registration and read from the
    gitignored .awow/hub.json ($AWOW_HUB overrides)."""
    if os.path.isfile(os.path.join(repo_dir, ".agents", "AGENTS.md")):
        return None
    connector = os.path.join(repo_dir, "AGENTS.md")
    hub = frontmatter_value(connector, "hub")
    if not hub:
        return None

    project = frontmatter_value(connector, "project") or os.path.basename(repo_dir)
    want = normalize_remote(hub)

    recorded_remote = ""
    candidate = os.environ.get("AWOW_HUB", "")
    if not candidate:
        recorded_remote, candidate = read_hub_link(
            os.path.join(repo_dir, ".awow", "hub.json"))
    if not candidate:
        return SPOKE_UNMAPPED.format(hub=hub)

    origin_matches = normalize_remote(clone_origin(candidate)) == want
    record_matches = not recorded_remote or normalize_remote(recorded_remote) == want
    if origin_matches and record_matches:
        return SPOKE_CONNECTED.format(project=project, hub=hub, path=candidate)
    return SPOKE_DRIFTED.format(hub=hub, path=candidate)


def engine_installed(repo_dir):
    """An inner-loop build engine (superpowers) anywhere the plugin loader
    looks: marketplace cache, user scope, or project scope."""
    home = os.environ.get("HOME", "")
    patterns = (
        os.path.join(home, ".claude", "plugins", "cache", "*", "superpowers"),
        os.path.join(home, ".claude", "plugins", "*", "superpowers"),
        os.path.join(repo_dir, ".claude", "plugins", "*", "superpowers"),
    )
    return any(os.path.isdir(p) for pat in patterns for p in glob.glob(pat))


def build_context(plugin_root, repo_dir):
    adopted = os.path.isfile(os.path.join(repo_dir, ".agents", "AGENTS.md"))
    spoke = spoke_context(repo_dir)

    sections = [PREAMBLE, read_bootstrap(plugin_root)]
    if spoke is not None:
        sections.append(spoke)
    # One-time setup nudge: only a repo that is neither vendored nor a spoke,
    # and has not opted out. A connectable spoke gets its tier message instead.
    elif not adopted and not os.path.isfile(
            os.path.join(repo_dir, ".awow", "no-setup-prompt")):
        sections.append(SETUP_NUDGE)
    # Soft-dependency nudge: an adopted repo with no build engine. Mutually
    # exclusive with the setup nudge (adopted vs not), so the two never stack.
    if adopted and not engine_installed(repo_dir) and not os.path.isfile(
            os.path.join(repo_dir, ".awow", "no-engine-prompt")):
        sections.append(ENGINE_NUDGE)

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
