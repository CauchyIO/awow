"""Build .agents/ into the plugin payloads under dist/ and dist-telemetry/.

.agents/ is the single source of truth. This script renders it into the
distributable payloads every harness installs — full copies, not pointers,
because payload content runs inside an adopter's project where `.agents/`
does not exist. Nothing is mirrored into this repo's own harness folders:
commands and skills reach a maintainer's session through the same plugin an
adopter installs (the marketplace manifest at .claude-plugin/ serves ./dist),
and the root instruction files (AGENTS.md, .claude/CLAUDE.md,
.github/AGENTS.md, .github/copilot-instructions.md) are hand-authored
pointers to .agents/AGENTS.md (AWO-257).

Files named README.md and paths under `_workitem-archetypes/` or
`_meeting-archetypes/` are never rendered as commands; they are documentation
or handlers.

Plugin payload (dist/)
----------------------
    .agents/commands/<name>.md           → dist/commands/<name>.md
    .agents/skills/<name>/**             → dist/skills/<name>/**
    .agents/skills/<name>.md             → dist/skills/<name>/SKILL.md
    (every command AND skill, as a skill) → dist/agent-skills/<name>/SKILL.md
    .agents/commands/_<kind>-archetypes/  → dist/handlers/_<kind>-archetypes/
                                            (router handler registries — data
                                            the routers read, deliberately not
                                            under the auto-discovered
                                            commands/; see AWO-161)
    hooks/**                             → dist/hooks/**
    tools/<runtime allowlist>            → dist/tools/**
    .claude-plugin/plugin.json           → dist/.claude-plugin/plugin.json
                                            (metadata only; commands/skills/
                                            hooks are auto-discovered)

The `agent-skills/` surface is the commands-as-skills payload for harnesses that
consume skills rather than slash commands (Codex, Pi): every command and skill
rendered as `<name>/SKILL.md`. Both harness manifests point at it (WI-5).

`dist/` is wholly owned by this script: any file found there that is not in
the plan is removed. Maintainer tools (gather.py itself, distribute.py, …)
are deliberately excluded from the payload — they resolve REPO_ROOT from
__file__ and would operate on the plugin install dir if shipped.
The build only applies in the awow maintainer repo (gated on
`.claude-plugin/plugin.json`).

Usage
-----
    python tools/gather.py                    # build dist/, dist-telemetry/ and the M365 package
    python tools/gather.py --check            # exit 1 if any payload is out of date
    python tools/gather.py --surface plugin   # only build dist/
    python tools/gather.py --surface telemetry  # only build dist-telemetry/
    python tools/gather.py --surface m365     # only the M365 package under dist/m365/

Orphans
-------
Every payload root is fully generated, so any file found under one that is
not in the plan is an orphan: reported by --check, removed on apply. Nested
git checkouts (a linked worktree below a payload root) are never swept.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".agents"
# Source of the Copilot plugin manifest (.github/plugin/plugin.json); nothing
# is emitted into .github/ itself.
GITHUB_DIR = REPO_ROOT / ".github"
DIST_DIR = REPO_ROOT / "dist"
# Second payload root: the awow-telemetry plugin (design spec 4.3). A sibling of
# dist/, not a child, for two reasons. Claude Code installs from CauchyIO/awow
# and resolves .claude-plugin/marketplace.json's relative `source` against the
# repo root, so "./dist-telemetry" needs no new install mechanism. And
# tools/sync-dist.sh mirrors only dist/ into awow-dist, so a sibling never
# reaches the Codex/Pi channel — which is exactly the Claude-Code-only scope
# constraint, enforced by the publish topology rather than by a rule someone
# has to remember.
DIST_TELEMETRY_DIR = REPO_ROOT / "dist-telemetry"
# Commands-as-skills surface: every command AND skill rendered as <name>/SKILL.md,
# for harnesses that consume skills rather than slash commands (Codex, Pi). Both
# their manifests point here (hub-and-spoke WI-5).
AGENT_SKILLS_DIR = DIST_DIR / "agent-skills"
# Codex plugin + marketplace live at the dist/ root: codex git-clones the plugin
# source, so it must be a repo root (source "./"), and dist/ published as a git repo
# IS the codex marketplace. (Verified against codex 0.144.)
CODEX_MANIFEST = DIST_DIR / ".codex-plugin" / "plugin.json"
CODEX_MARKETPLACE = DIST_DIR / ".agents" / "plugins" / "marketplace.json"
# Pi package manifest at the dist/ root: `pi install` reads the `pi` key and loads the
# commands-as-skills from pi.skills. Pi reads root AGENTS.md and .agents/skills natively,
# so the package is the whole Pi integration — no extension needed.
# One manifest at the dist/ root serves two harnesses. `pi install` reads the `pi`
# key; opencode reads `main`, which points at the plugin module below. Pi reads root
# AGENTS.md and .agents/skills natively, so the package is the whole Pi integration.
PI_MANIFEST = DIST_DIR / "package.json"
# opencode plugin module. opencode plugins are JS hook modules — no manifest field
# can register skills, so the skills directory is registered at runtime through the
# plugin's `config` hook. (Verified against opencode 1.15.2.)
OPENCODE_PLUGIN = DIST_DIR / ".opencode" / "plugins" / "awow.js"
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
HOOKS_DIR = REPO_ROOT / "hooks"

# Runtime tools shipped in a plugin payload, split by which plugin needs them.
# Everything else under tools/ stays maintainer-only: those scripts resolve
# REPO_ROOT from __file__ and would operate on the plugin install dir if
# shipped (hub-and-spoke WI-4).
#
# Base plugin: the pre-push leak scan and its pattern file, plus the 3-way
# lock engine /migrate-to-plugin drives against a vendored repo (AWO-259) —
# shipped so the migration always runs the payload's current engine, never the
# repo's vendored vintage. awow_lock.py takes an explicit --root; the command
# must always pass it, since __file__-relative resolution would point the
# engine at the plugin install dir. cascade_check.py is the department sweep
# /okr-cascade and /setup-department run as {AWOW_TOOLS}/cascade_check.py; it
# resolves the department root from its own cwd, never from __file__, so it is
# safe at the plugin install dir. The three session-analysis tools below served
# only skills that have moved.
#
# tests/payload-tools/ fails the build when a shipped body references a tool
# this list does not carry — add here, never allowlist there.
PLUGIN_TOOL_PATHS = [
    "hooks/leak-patterns.txt",
    "hooks/pre-push",
    "awow_lock.py",
    "cascade_check.py",
]

# awow-telemetry: the session-analysis runtime. project-timeline has no
# scripts/ directory of its own — session_timeline.py plus its HTML template
# ARE its implementation, reached as {AWOW_TOOLS}/… from the skill body. And
# mlflow_reader.py is shared: awow-usage-coach's bundled awow_extract.py
# imports it (scripts/awow_extract.py:52-61), so the two must land in the same
# payload or that import fails at runtime.
TELEMETRY_TOOL_PATHS = [
    "mlflow_reader.py",
    "session_timeline.py",
    "session_timeline_template.html",
]

CONTEXT_DIR = REPO_ROOT / "context"

# Which context/ files ship in the payload. The predicate (design spec 4.1.2):
# a file ships if a default exists that is useful before /setup-awow runs.
#   contract — identical for every adopter, nobody edits it
#   template — ships a working default that /setup-awow tunes
# Entries are POSIX paths relative to context/; a bare directory name covers
# its whole subtree. Addressed in prompt bodies as {AWOW_ROOT}/context/...
PAYLOAD_CONTEXT_PATHS = [
    "kb-inbox/README.md",                 # contract
    "knowledge-base/README.md",           # contract
    "knowledge-base/mining.md",           # contract
    "knowledge-base/synthesis.md",        # contract
    "retros/anti-patterns.md",            # contract
    "retros/canon.md",                    # contract
    "tooling/README.md",                  # contract
    "tooling/activity-collection.md",     # contract
    "tooling/boards",                     # contract (subtree, 35 files)
    "tooling/harnesses",                  # contract (subtree, 5 files)
    "knowledge-base/mining-policy.md",    # template — selectivity: 2
    "tooling/design-system.md",           # template — mode: absent
    "tooling/knowledge-base.md",          # template — default kb_root
    "tooling/knowledge-sources.md",       # contract — canonical-source routing
    "tooling/department.md",              # template — default department indirection
    "department/templates",               # contract (subtree — OKR and PI skeletons)
    "tooling/m365",                       # template — default agent identity/branding, tuned per adopter
    "team/meetings/README.md",            # contract — plain-Markdown meeting guidance shape
    "team/workitem-archetypes/README.md", # contract — team archetype overlay shape
]

# Team data: /setup-awow authors these per adopter. No useful default exists,
# and a generic stub is worse than absence — commands branch on absence
# (see the board fallback, design spec 4.2), but cannot branch on boilerplate.
TEAM_DATA_CONTEXT_PATHS = [
    "README.md",
    "company",
    "department/definition.md",           # MD-authored department description
    "department/teams.md",                # registry written by /setup-department
    "department/decisions",               # governance decisions
    "kb-inbox/_synthesis-log.md",
    "knowledge-base/architecture",
    "knowledge-base/decisions",
    "knowledge-base/glossary.md",
    "knowledge-base/patterns",
    "knowledge-base/runbooks",
    "knowledge-sources",
    "quarterly",
    "team",
    "tooling/architecture.md",
    "tooling/board.md",
]


def _covers(entry: str, rel: str) -> bool:
    """True if manifest `entry` covers `rel` — exact file, or directory prefix."""
    return rel == entry or rel.startswith(entry + "/")


def classify_context_path(rel: str) -> str:
    """'payload', 'team-data', or 'unclassified' for a POSIX path relative to
    context/. Longest matching entry wins, so a file may be carved out of a
    directory-level classification."""
    best, verdict = -1, "unclassified"
    for entry in PAYLOAD_CONTEXT_PATHS:
        if _covers(entry, rel) and len(entry) > best:
            best, verdict = len(entry), "payload"
    for entry in TEAM_DATA_CONTEXT_PATHS:
        if _covers(entry, rel) and len(entry) > best:
            best, verdict = len(entry), "team-data"
    return verdict


def unclassified_context_paths() -> list[str]:
    """Every file under context/ that no manifest entry covers. A new file that
    nobody classified fails the build rather than silently not shipping."""
    if not CONTEXT_DIR.is_dir():
        return []
    stray = []
    for path in sorted(CONTEXT_DIR.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel = path.relative_to(CONTEXT_DIR).as_posix()
        if classify_context_path(rel) == "unclassified":
            stray.append(rel)
    return stray


SKIP_FILENAMES = {"README.md"}
HANDLER_DIR_PARTS = {"_workitem-archetypes", "_meeting-archetypes"}
SKIP_DIR_PARTS = HANDLER_DIR_PARTS
# Where the handler registries land in a payload. A sibling of commands/, not a
# child: the command directories are auto-discovered, and anything under one is
# offered to the user as a command (AWO-161). See plan_archetype_handlers.
HANDLERS_DIR_NAME = "handlers"
# Heads the prose files this script authors into a payload (the dist/ READMEs)
# so a reader knows not to edit them there. Payload *content* — commands,
# skills, handlers — is copied verbatim and never carries it.
GENERATED_MARKER = "<!-- GENERATED by tools/gather.py"

# Payload roots that this script wholly owns: under one of these, EVERY
# unplanned file is an orphan. Payload content carries no marker of its own —
# plugin_command_copy, command_skill_stub, and skill_stubs each emit the source
# body verbatim — so the plan is the only thing the sweep can go on, and a
# payload root missing from this tuple has its orphans silently ignored while
# --check stays green. Add every new payload root here in the same change that
# creates it.
GENERATED_ROOTS = (DIST_DIR, DIST_TELEMETRY_DIR)

# The M365 package: planned by gather_m365.plan_m365 as its own surface, built
# by the default run alongside the two payload roots (AWO-262) and on its own
# via `--surface m365`. It nests inside dist/, so the dist/ sweep must skip it
# — its files are in plan_m365's plan, not plan_plugin's — or a dist-only run
# would delete the package.
M365_ROOT = DIST_DIR / "m365"
INDEPENDENTLY_MANAGED_ROOTS = (M365_ROOT,)


@dataclass(frozen=True)
class Stub:
    target: Path
    content: str
    mode: int | None = None  # exec bits matter for hooks and scripts


@dataclass(frozen=True)
class BinaryStub:
    target: Path
    content: bytes


# ---------- minimal frontmatter parser ----------

_FM_DELIM = "---\n"

# YAML block-scalar headers: folded (>) or literal (|), each with an optional
# indentation indicator and an optional chomping indicator.
_BLOCK_SCALAR = re.compile(r"^[|>][0-9]*[-+]?$")


def parse_frontmatter(
    text: str, source: Path | None = None
) -> tuple[dict[str, str], str]:
    """Return (scalar fields, body). Lists are ignored — we only need top-level
    strings like name, description, removes_pain.

    Block scalars are REJECTED, not ignored. This parser is line-based, so a
    `description: >-` would be stored as the literal two-character string '>-'
    and would propagate to every pointer stub, plugin picker entry, and
    agent-skill trigger built from it — with `--check` green the whole way,
    because the build faithfully mirrors the wrong value. Descriptions are
    single-line and double-quoted (design spec 4.5). Pass `source` so the
    failure names the file.
    """
    if not text.startswith(_FM_DELIM):
        return {}, text
    end = text.find("\n" + _FM_DELIM, len(_FM_DELIM))
    if end == -1:
        return {}, text
    fm_block = text[len(_FM_DELIM):end]
    body = text[end + len("\n" + _FM_DELIM):]
    fields: dict[str, str] = {}
    for line in fm_block.splitlines():
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$', line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if _BLOCK_SCALAR.match(raw):
            where = f"{source.relative_to(REPO_ROOT)}: " if source is not None else ""
            raise ValueError(
                f"{where}frontmatter field {key!r} uses the YAML block scalar "
                f"{raw!r}. tools/gather.py parses frontmatter line by line, so "
                f"the value would be stored as the literal string {raw!r} and "
                f"mirrored into every stub, picker entry, and skill trigger. "
                f"Write it as one double-quoted line instead."
            )
        if raw == "" or raw.startswith("[") or raw.startswith("{"):
            continue
        if (raw.startswith('"') and raw.endswith('"')) or (
            raw.startswith("'") and raw.endswith("'")
        ):
            raw = raw[1:-1]
        fields[key] = raw
    return fields, body


def first_h1(body: str) -> str | None:
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return None


# ---------- command metadata ----------


def command_description(fields: dict[str, str], body: str) -> str:
    """Best-effort one-liner description for a command.

    Priority: explicit `description` field → H1 after the em-dash → H1 → empty.
    """
    if "description" in fields:
        return fields["description"]
    h1 = first_h1(body)
    if h1:
        if "—" in h1:
            return h1.split("—", 1)[1].strip()
        if " - " in h1:
            return h1.split(" - ", 1)[1].strip()
        return h1
    return ""


# ---------- planning ----------


def is_skipped(path: Path) -> bool:
    if path.name in SKIP_FILENAMES:
        return True
    if any(part in SKIP_DIR_PARTS for part in path.relative_to(AGENTS_DIR).parts):
        return True
    return False


def copy_stub(target: Path, source: Path) -> Stub:
    return Stub(target, source.read_text(), source.stat().st_mode & 0o777)


# Path tokens (see .agents/AGENTS.md "Path tokens"): {AWOW_TOOLS} and
# {AWOW_ROOT} resolve at build time for the plugin surface — the payload knows
# where it lives. {ANCHOR} and {PROJECT} ship as-is; the session reflex teaches
# their resolution. {HUB}, the pre-rename spelling of {ANCHOR}, is likewise
# never substituted, so adopter-owned files that still use it render unchanged.
PLUGIN_TOKEN_SUBSTITUTIONS = [
    ("{AWOW_TOOLS}", "${CLAUDE_PLUGIN_ROOT}/tools"),
    ("{AWOW_ROOT}", "${CLAUDE_PLUGIN_ROOT}"),
]


# A prompt body must be able to NAME a token without USING it — using-awow and
# AGENTS.md both document the token vocabulary and are themselves rendered.
# {{TOKEN}} is the escape: protected before substitution, unwrapped after.
# Scoped to the path-token names deliberately: a blanket {{[A-Z_]+}} escape
# would also unwrap the {{PLACEHOLDER}} markers /daily-digest documents for the
# adopter's HTML template, corrupting the syntax that file exists to describe.
# HUB stays listed after the {ANCHOR} rename so prose documenting the
# pre-rename spelling can still escape it.
PATH_TOKEN_NAMES = ("ANCHOR", "HUB", "PROJECT", "AWOW_TOOLS", "AWOW_ROOT")
_ESCAPED_TOKEN = re.compile(r"\{\{(" + "|".join(PATH_TOKEN_NAMES) + r")\}\}")
_ESCAPE_SENTINEL = "\x00"


def _render(text: str, substitutions: list[tuple[str, str]]) -> str:
    text = _ESCAPED_TOKEN.sub(
        lambda m: f"{_ESCAPE_SENTINEL}{m.group(1)}{_ESCAPE_SENTINEL}", text
    )
    for token, replacement in substitutions:
        text = text.replace(token, replacement)
    return re.sub(
        rf"{_ESCAPE_SENTINEL}([A-Z_]+){_ESCAPE_SENTINEL}", r"{\1}", text
    )


def render_plugin_body(text: str) -> str:
    return _render(text, PLUGIN_TOKEN_SUBSTITUTIONS)


# The commands-as-skills surface (Codex/Pi) can't resolve ${CLAUDE_PLUGIN_ROOT}.
# Agent Skills resolve paths relative to the skill dir, so from
# dist/agent-skills/<name>/SKILL.md, ../../tools reaches the payload's dist/tools/.
AGENT_SKILLS_TOKEN_SUBSTITUTIONS = [
    ("{AWOW_TOOLS}", "../../tools"),
    ("{AWOW_ROOT}", "../.."),
]


def render_agent_skills_body(text: str) -> str:
    return _render(text, AGENT_SKILLS_TOKEN_SUBSTITUTIONS)


def declared_channel(text: str) -> str:
    """The `channel:` declared in the leading frontmatter, or 'both'.

    The field is NOT binary — four values are in play, and code that treats it
    as ships/doesn't-ship gets `bootstrap` wrong:

      both       (default)  ships in every payload
      vendored              operates on the vendored install itself; never ships
      bootstrap             ships, but *creates* the vendored tree, so its
                            literal paths are the deliverable (lint-paths.py:36-38)
      telemetry             ships in the awow-telemetry payload only, never in
                            the base plugin (design spec 4.3)

    tools/lint-paths.py carries an independent parser for the same field; the
    two are asserted equal on every source file in tests/telemetry-split/."""
    return parse_frontmatter(text)[0].get("channel", "both")


def is_vendored_channel(text: str) -> bool:
    """channel: vendored files operate on the vendored install itself and are
    excluded from every plugin payload."""
    return declared_channel(text) == "vendored"


def is_telemetry_channel(text: str) -> bool:
    """channel: telemetry files build into dist-telemetry/ (the awow-telemetry
    plugin) and are excluded from dist/ — both its Claude skills surface and
    its Codex/Pi agent-skills surface."""
    return declared_channel(text) == "telemetry"


def is_autofire(text: str) -> bool:
    """`autofire: true` mirrors a command into dist/skills/ on top of the /
    picker, so a Claude session can elect it from the situation the user is in
    rather than waiting to be typed. The selection rule (design spec 4.5
    Layer 3): a command autofires unless a misfire would be damage
    (consequential and hard to reverse) or noise (trigger too broad) — and
    noise is how the whole mechanism gets switched off.

    Claude-surface only. plan_agent_skills emits a skill for EVERY non-vendored
    command, so Codex, Pi, and Copilot see all of them regardless. That
    asymmetry is accepted: suppressing there would make a command invisible to
    three of the four harnesses' triggers.
    """
    return parse_frontmatter(text)[0].get("autofire") == "true"


def plugin_command_copy(target: Path, source: Path, text: str | None = None) -> Stub:
    """Full copy, with a `description:` injected into the frontmatter when the
    source only carries it in the H1 — the plugin picker needs the field. Pass
    `text` to reuse an already-read body and avoid a second read of `source`."""
    text = render_plugin_body(source.read_text() if text is None else text)
    mode = source.stat().st_mode & 0o777
    fields, body = parse_frontmatter(text, source)
    if "description" in fields:
        return Stub(target, text, mode)
    desc = command_description(fields, body)
    if not desc:
        return Stub(target, text, mode)
    desc_line = f'description: "{desc.replace(chr(34), chr(92) + chr(34))}"'
    if text.startswith(_FM_DELIM):
        end = text.find("\n" + _FM_DELIM, len(_FM_DELIM))
        fm_block = text[len(_FM_DELIM):end]
        rest = text[end + len("\n" + _FM_DELIM):]
        content = f"---\n{desc_line}\n{fm_block}\n---\n{rest}"
    else:
        content = f"---\n{desc_line}\n---\n\n{text}"
    return Stub(target, content, mode)


def skill_stubs(
    entry: Path, dest_root: Path, render=render_plugin_body, channel: str = "both"
) -> list[Stub]:
    """Render one `.agents/skills/<entry>` into `dest_root/<name>/…` as full-content
    SKILL.md (+ any bundled files). Shared by the Claude plugin payload (dist/skills),
    the commands-as-skills surface (dist/agent-skills, which passes
    render_agent_skills_body), and the telemetry payload (dist-telemetry/skills).

    `channel` selects which payload is being built: 'both' takes everything that
    is not vendored and not telemetry; 'telemetry' takes exactly the telemetry
    entries. Returns [] for vendored or non-skill entries either way."""
    if entry.is_dir() and (entry / "SKILL.md").exists():
        skill_md = entry / "SKILL.md"
        skill_text = skill_md.read_text()
        if is_vendored_channel(skill_text):
            return []
        if is_telemetry_channel(skill_text) != (channel == "telemetry"):
            return []
        out: list[Stub] = []
        for f in sorted(entry.rglob("*")):
            if not f.is_file():
                continue
            target = dest_root / entry.name / f.relative_to(entry)
            if f.suffix == ".md":
                body = skill_text if f == skill_md else f.read_text()
                out.append(Stub(target, render(body), f.stat().st_mode & 0o777))
            else:
                out.append(copy_stub(target, f))
        return out
    if entry.is_file() and entry.suffix == ".md":
        # Declarative skill: wrap the FULL body (not a pointer) in the dir/SKILL.md
        # form the loader discovers.
        text = entry.read_text()
        if is_vendored_channel(text):
            return []
        if is_telemetry_channel(text) != (channel == "telemetry"):
            return []
        fields, body = parse_frontmatter(text)
        name = fields.get("name", entry.stem)
        description = fields.get("description") or first_h1(body) or ""
        desc_escaped = description.replace(chr(34), chr(92) + chr(34))
        content = (
            f"---\n"
            f"name: {name}\n"
            f'description: "{desc_escaped}"\n'
            f"---\n\n"
            f"{render(body.lstrip())}"
        )
        return [Stub(dest_root / name / "SKILL.md", content)]
    return []


def command_skill_stub(source: Path, dest_root: Path, render=render_plugin_body) -> Stub | None:
    """Render a command as a `<name>/SKILL.md` — name + description frontmatter over
    the full command body. Commands-as-skills: the harness loads it when the user
    names the flow. None for vendored commands."""
    text = source.read_text()
    if is_vendored_channel(text):
        return None
    fields, body = parse_frontmatter(text, source)
    name = source.stem
    description = command_description(fields, body)
    desc_escaped = description.replace(chr(34), chr(92) + chr(34))
    content = (
        f"---\n"
        f"name: {name}\n"
        f'description: "{desc_escaped}"\n'
        f"---\n\n"
        f"{render(body.lstrip())}"
    )
    return Stub(dest_root / name / "SKILL.md", content)


def plan_agent_skills() -> list[Stub]:
    """Commands-as-skills surface under dist/agent-skills/ — every command AND skill
    as <name>/SKILL.md, for Codex and Pi. Full content (the payload ships where
    `.agents/` is absent). Both harness manifests point at this one directory."""
    plans: list[Stub] = []
    for source in sorted((AGENTS_DIR / "commands").rglob("*.md")):
        if is_skipped(source):
            continue
        stub = command_skill_stub(source, AGENT_SKILLS_DIR, render_agent_skills_body)
        if stub is not None:
            plans.append(stub)
    for entry in sorted((AGENTS_DIR / "skills").iterdir()):
        if entry.name in SKIP_FILENAMES:
            continue
        plans.extend(skill_stubs(entry, AGENT_SKILLS_DIR, render_agent_skills_body))
    # No second context/ copy: {AWOW_ROOT} renders to ../.. on this channel,
    # which from dist/agent-skills/<name>/ resolves to dist/ — the same files
    # plan_plugin already ships. Adding a copy here would double the payload
    # and desync the two.
    return plans


def plan_codex() -> list[Stub]:
    """Codex plugin manifest + marketplace, into dist/. dist/ published as a git repo
    IS the codex marketplace: the plugin sits at its root (source "./"), points
    `skills` at the shared agent-skills surface, and carries the load-bearing empty
    `hooks` (without it Codex auto-discovers hooks/hooks.json and re-registers Claude
    Code's SessionStart hook; Codex needs none — root AGENTS.md is the reflex)."""
    src = json.loads(PLUGIN_MANIFEST.read_text())
    plugin = {
        "name": src["name"],
        "version": src["version"],
        "description": src["description"],
        "author": src.get("author", {"name": "awow maintainers"}),
        "license": src.get("license", "MIT"),
        "homepage": src.get("homepage"),
        "repository": src.get("repository"),
        "skills": "./agent-skills/",
        "hooks": {},
        "interface": {
            "displayName": src.get("displayName", src["name"]),
            "shortDescription": "Board-first delivery workflows for coding agents",
            "category": "Developer Tools",
        },
    }
    marketplace = {
        "name": src["name"],
        "plugins": [
            {
                "name": src["name"],
                "source": {"source": "url", "url": "./"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
        ],
    }
    return [
        Stub(CODEX_MANIFEST, json.dumps(plugin, indent=2, ensure_ascii=False) + "\n"),
        Stub(CODEX_MARKETPLACE, json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n"),
    ]


def plan_pi() -> list[Stub]:
    """The shared dist/ package manifest — Pi and opencode read the same file.

    Pi: `pi install <dist>` reads `pi.skills` and surfaces the commands-as-skills.
    Pi discovers root AGENTS.md + the user's own .agents/skills natively, so the
    package is the whole integration — no `.pi/extensions` needed.

    opencode: `opencode plugin awow@git+<awow-dist>` reads `main`, which points at
    the plugin module plan_opencode_plugin emits. `type: module` is required — the
    module uses ESM `import`, and without it opencode's loader rejects the file.

    One manifest, not two: both harnesses expect package.json at the package root,
    so a second file is impossible. The keys are disjoint, so neither constrains
    the other."""
    src = json.loads(PLUGIN_MANIFEST.read_text())
    pkg = {
        "name": src["name"],
        "version": src["version"],
        "description": src["description"],
        "license": src.get("license", "MIT"),
        "homepage": src.get("homepage"),
        "repository": src.get("repository"),
        "keywords": ["pi-package", "opencode-plugin"],
        "type": "module",
        "main": "./" + OPENCODE_PLUGIN.relative_to(DIST_DIR).as_posix(),
        "pi": {"skills": ["./agent-skills"]},
    }
    return [Stub(PI_MANIFEST, json.dumps(pkg, indent=2, ensure_ascii=False) + "\n")]


OPENCODE_PLUGIN_JS = '''\
// GENERATED by tools/gather.py — DO NOT EDIT.
// Edit tools/gather.py (plan_opencode_plugin) and re-run the gather.
/**
 * awow plugin for opencode.
 *
 * Two jobs, mirroring what the Claude Code plugin gets from its SessionStart hook:
 *
 *  1. Register the commands-as-skills payload. opencode plugins are JS hook
 *     modules — no manifest field can declare a skills directory — so the only
 *     way in is the `config` hook, which mutates the cached config singleton
 *     before skills are lazily discovered.
 *  2. Inject the using-awow operating reflex, plus an opencode tool mapping.
 *     A global install lands in repos with no repo-root AGENTS.md; without this
 *     awow would be installed but dormant.
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// .opencode/plugins/ -> the payload root. agent-skills/ is the same directory
// Pi loads via pi.skills, so both harnesses see one copy with one token channel
// ({AWOW_ROOT} -> ../.., {AWOW_TOOLS} -> ../../tools).
const PACKAGE_ROOT = path.resolve(__dirname, '../..');
const SKILLS_DIR = path.join(PACKAGE_ROOT, 'agent-skills');
const BOOTSTRAP_PATH = path.join(SKILLS_DIR, 'using-awow', 'SKILL.md');
const MARKER = 'awow-operating-reflex';

const stripFrontmatter = (text) => {
  const m = text.match(/^---\\n[\\s\\S]*?\\n---\\n([\\s\\S]*)$/);
  return m ? m[1] : text;
};

const TOOL_MAPPING = [
  '**Tool mapping for opencode.** Where awow names a Claude Code tool, use:',
  '- Read / Write / Edit a file -> `read` / `write` / `edit`',
  '- Run a shell command -> `bash`',
  '- Track multi-step work -> `todowrite`',
  '- Dispatch a subagent -> `task`',
  '- Invoke a skill -> the native `skill` tool',
].join('\\n');

// The SKILL.md does not change during a session, so read and parse it once.
let _cache;

const bootstrap = () => {
  if (_cache !== undefined) return _cache;
  if (!fs.existsSync(BOOTSTRAP_PATH)) {
    // Fail loud, not soft. The 0.5.0 payload shipped a one-line error quietly
    // standing in for the whole reflex; a missing bootstrap must be
    // unmistakable both in the injected context and on stderr.
    const err =
      'awow: using-awow bootstrap NOT FOUND at ' + BOOTSTRAP_PATH +
      '. The operating reflex did NOT load — this plugin build is broken.';
    console.error(err);
    _cache = '<' + MARKER + '>\\n' + err + '\\n</' + MARKER + '>';
    return _cache;
  }
  const body = stripFrontmatter(fs.readFileSync(BOOTSTRAP_PATH, 'utf8')).trim();
  _cache = '<' + MARKER + '>\\n' + body + '\\n\\n' + TOOL_MAPPING + '\\n</' + MARKER + '>';
  return _cache;
};

export const AwowPlugin = async () => ({
  config: async (config) => {
    config.skills = config.skills || {};
    config.skills.paths = config.skills.paths || [];
    if (!config.skills.paths.includes(SKILLS_DIR)) {
      config.skills.paths.push(SKILLS_DIR);
    }
  },

  // Inject into the first user message rather than a system message: opencode
  // reloads messages from the DB on every agent step, and repeated system
  // messages both bloat tokens and break some models.
  'experimental.chat.messages.transform': async (_input, output) => {
    const text = bootstrap();
    if (!text || !output.messages || !output.messages.length) return;
    const firstUser = output.messages.find((m) => m.info.role === 'user');
    if (!firstUser || !firstUser.parts.length) return;
    // Guard against double injection when an already-transformed array is
    // passed through the hook again.
    if (firstUser.parts.some((p) => p.type === 'text' && p.text.includes(MARKER))) return;
    const ref = firstUser.parts[0];
    firstUser.parts.unshift({ ...ref, type: 'text', text });
  },
});
'''


def plan_opencode_plugin() -> list[Stub]:
    """opencode plugin module into dist/.

    `opencode plugin awow@git+<awow-dist>` resolves package.json `main` (set in
    plan_pi) to this file. It registers agent-skills/ through the `config` hook
    and injects the using-awow reflex — see the module docstring for why each is
    needed. Verified against opencode 1.15.2."""
    return [Stub(OPENCODE_PLUGIN, OPENCODE_PLUGIN_JS)]


def plan_telemetry() -> list[Stub]:
    """dist-telemetry/ — the awow-telemetry plugin payload (design spec 4.3).

    Claude Code only, this release. Deliberately absent: the Codex manifest,
    the Pi package.json, the agent-skills surface, and hooks/. The SessionStart
    hook reads ${PLUGIN_ROOT}/.agents/skills/using-awow/SKILL.md, and using-awow
    stays in the base plugin — a copy of hooks/ here would emit the error string
    into every session, and double-inject for anyone running both plugins.

    Name, description, and version derive from the one canonical
    .claude-plugin/plugin.json, exactly as plan_codex and plan_pi do, so the two
    plugins version in lockstep with no second file to keep in sync."""
    src = json.loads(PLUGIN_MANIFEST.read_text())
    manifest = {
        "name": "awow-telemetry",
        "displayName": "awow-telemetry — the evidence layer",
        "description": (
            "Session analysis for awow: export agent traces, build a visual "
            "project timeline, score prompt craft, and coach a team or an "
            "individual off what the sessions actually show. Installs beside "
            "awow@awow; neither requires the other."
        ),
        "version": src["version"],
        "author": src.get("author", {"name": "awow maintainers"}),
        "license": src.get("license", "MIT"),
        "homepage": src.get("homepage"),
        "repository": src.get("repository"),
    }
    plans = [
        Stub(
            DIST_TELEMETRY_DIR / ".claude-plugin" / "plugin.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        ),
        Stub(
            DIST_TELEMETRY_DIR / "README.md",
            f"{GENERATED_MARKER} — DO NOT EDIT. -->\n\n"
            "# dist-telemetry/ — built awow-telemetry plugin payload\n\n"
            "This directory is the installable `awow-telemetry` Claude Code "
            "plugin, built by `python tools/gather.py --surface telemetry` from "
            "the `channel: telemetry` skills under `.agents/skills/` plus a "
            "runtime slice of `tools/`. The repo-root "
            "`.claude-plugin/marketplace.json` points installers here as the "
            "second entry, so `/plugin install awow-telemetry@awow` resolves.\n\n"
            "**Claude Code only this release.** `tools/sync-dist.sh` mirrors "
            "only `dist/` into `awow-dist`, which is the Codex and Pi install "
            "source — so nothing here reaches those harnesses. That is the "
            "intended scope, not an omission.\n\n"
            "Do not edit files in this directory — edit the source and re-run "
            "the gather. Any file here that the build did not plan is deleted "
            "on the next run.\n",
        ),
    ]
    for entry in sorted((AGENTS_DIR / "skills").iterdir()):
        if entry.name in SKIP_FILENAMES:
            continue
        plans.extend(
            skill_stubs(entry, DIST_TELEMETRY_DIR / "skills", channel="telemetry")
        )
    for rel in TELEMETRY_TOOL_PATHS:
        plans.append(copy_stub(DIST_TELEMETRY_DIR / "tools" / rel, REPO_ROOT / "tools" / rel))
    return plans


def plan_context_payload(dest_root: Path, render=render_plugin_body) -> list[Stub]:
    """The context/ machinery that ships, rendered for one channel. Commands
    reach these as {AWOW_ROOT}/context/... — {ANCHOR} first so a vendored
    override wins, then {AWOW_ROOT}. See the predicate above PAYLOAD_CONTEXT_PATHS."""
    plans: list[Stub] = []
    for path in sorted(CONTEXT_DIR.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel = path.relative_to(CONTEXT_DIR).as_posix()
        if classify_context_path(rel) != "payload":
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            # A binary asset (e.g. context/tooling/m365/assets/*.png) living
            # under a payload-classified subtree — its own surface reads it
            # directly with read_bytes(); it has no place in this text mirror.
            continue
        plans.append(
            Stub(
                dest_root / "context" / rel,
                render(text),
                path.stat().st_mode & 0o777,
            )
        )
    return plans


def plan_copilot_payload() -> list[Stub]:
    """dist/.github/ — the Copilot slice of the payload. Generated from
    .agents/, not copied from .github/: a copy would ship ci.yml (which would
    run inside awow-dist against a repo with no .agents/), the pointer stubs
    (whose ../.agents/ links resolve to nothing in a payload), and the
    vendored-channel prompts the filter is meant to exclude.

    The manifest declares .github/plugin/skills/, so that directory must ship
    with real content or the installed plugin resolves to zero skills
    (AWO-155). It is filled from .agents/skills/ — the same source and the same
    renderer as the Claude payload's dist/skills/. It used to hold a single
    hand-authored awowify skill instead; that skill went with the vendoring
    route (CAU-1340), and generating from .agents/ is what the manifest always
    promised anyway.

    Uses render_plugin_body via plugin_command_copy: Copilot CLI resolves
    ${CLAUDE_PLUGIN_ROOT}. Only Codex and Pi need render_agent_skills_body."""
    manifest = json.loads((GITHUB_DIR / "plugin" / "plugin.json").read_text())
    # Version is canonical, as in plan_codex/plan_pi/plan_telemetry. Name and
    # description stay as authored: this manifest describes the Copilot surface
    # specifically, the same way plan_telemetry carries its own description.
    manifest["version"] = json.loads(PLUGIN_MANIFEST.read_text())["version"]
    plans = [
        Stub(
            DIST_DIR / ".github" / "plugin" / "plugin.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )
    ]
    copilot_skills = DIST_DIR / ".github" / "plugin" / "skills"
    for entry in sorted((AGENTS_DIR / "skills").iterdir()):
        if entry.name in SKIP_FILENAMES:
            continue
        plans.extend(skill_stubs(entry, copilot_skills))
    for source in sorted((AGENTS_DIR / "commands").rglob("*.md")):
        if is_skipped(source):
            continue
        text = source.read_text()
        if is_vendored_channel(text):
            continue
        plans.append(
            plugin_command_copy(
                DIST_DIR / ".github" / "prompts" / f"{source.stem}.prompt.md",
                source,
                text,
            )
        )
    return plans


def plan_archetype_handlers() -> list[Stub]:
    """Ship router handler registries as runtime data, never picker commands.

    Destination is HANDLERS_DIR_NAME, deliberately NOT `commands/`: Claude Code
    and Copilot auto-discover the command directories from the payload root, so
    a handler landing there becomes a description-less entry in the user's
    picker and a `claude plugin validate --strict` failure (AWO-161). The
    routers reach the registries by the same rooted path — see the
    `{AWOW_ROOT}/handlers/...` references in process-workitem and
    process-transcript, asserted by tests/payload-commands/.

    README.md is registry documentation, not a lens: process-transcript reads
    every file here as a handler, so shipping the README would offer it as one.
    """
    plans: list[Stub] = []
    for registry in sorted(HANDLER_DIR_PARTS):
        src = AGENTS_DIR / "commands" / registry
        if not src.is_dir():
            continue
        plans.extend(
            Stub(
                DIST_DIR / HANDLERS_DIR_NAME / registry / f.name,
                render_plugin_body(f.read_text()),
                f.stat().st_mode & 0o777,
            )
            for f in sorted(src.glob("*.md"))
            if f.name not in SKIP_FILENAMES
        )
    return plans


def plan_plugin() -> list[Stub]:
    """Full-copy payload under dist/ — the installable Claude Code plugin."""
    manifest = json.loads(PLUGIN_MANIFEST.read_text())
    # Metadata only: commands/, skills/, hooks/hooks.json are auto-discovered
    # from the plugin root, so an explicit commands path would be redundant.
    manifest.pop("commands", None)
    plans = [
        Stub(
            DIST_DIR / ".claude-plugin" / "plugin.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        ),
        Stub(
            DIST_DIR / "README.md",
            f"{GENERATED_MARKER} — DO NOT EDIT. -->\n\n"
            "# dist/ — the built awow payload\n\n"
            "awow is the Agentic Way of Working: board-first delivery "
            "workflows for coding agents. This directory is the built "
            "plugin, and it serves four harnesses from one tree — "
            "`commands/` and `skills/` for Claude Code, `agent-skills/` for "
            "Codex and Pi, `.github/` for GitHub Copilot, plus `hooks/`, a "
            "runtime slice of `tools/`, and the `context/` machinery the "
            "commands read.\n\n"
            "Install instructions live in the source repo's README: "
            "https://github.com/CauchyIO/awow\n\n"
            "Built by `python tools/gather.py --surface plugin` from "
            "`.agents/`, so the maintainer surfaces (proposals, guides, "
            "tests, team context) never ships. Do not edit anything here — "
            "edit the source and re-run the gather. Any file the build did "
            "not plan is deleted on the next run.\n",
        ),
    ]
    commands_root = AGENTS_DIR / "commands"
    for source in sorted(commands_root.rglob("*.md")):
        if is_skipped(source):
            continue
        text = source.read_text()
        if is_vendored_channel(text):
            continue
        plans.append(plugin_command_copy(DIST_DIR / "commands" / source.name, source, text))
        if is_autofire(text):
            stub = command_skill_stub(source, DIST_DIR / "skills")
            if stub is not None:
                plans.append(stub)
    skills_root = AGENTS_DIR / "skills"
    for entry in sorted(skills_root.iterdir()):
        if entry.name in SKIP_FILENAMES:
            continue
        plans.extend(skill_stubs(entry, DIST_DIR / "skills"))
    for f in sorted(HOOKS_DIR.rglob("*")):
        if f.is_file():
            plans.append(copy_stub(DIST_DIR / "hooks" / f.relative_to(HOOKS_DIR), f))
    for rel in PLUGIN_TOOL_PATHS:
        source = REPO_ROOT / "tools" / rel
        plans.append(copy_stub(DIST_DIR / "tools" / rel, source))
    plans.extend(plan_context_payload(DIST_DIR, render_plugin_body))
    plans.extend(plan_copilot_payload())
    plans.extend(plan_archetype_handlers())
    return plans


def payload_stamp(root: Path, stubs: list[Stub], version: str) -> str:
    """build.json content for one payload root: the canonical version plus a
    digest of the planned payload, so two rebuilds of the same version are
    distinguishable (CAU-1338). Content-derived only — no clock, no commit —
    keeping the build a deterministic function of the source tree so --check
    cannot flap. Paths hash relative to the payload root and sorted, so
    neither the checkout location nor plan assembly order matters; mode bits
    are excluded (content changes are the vintage signal)."""
    h = hashlib.sha256()
    for stub in sorted(stubs, key=lambda s: s.target.relative_to(root).as_posix()):
        h.update(stub.target.relative_to(root).as_posix().encode())
        h.update(b"\0")
        h.update(stub.content.encode())
        h.update(b"\0")
    return json.dumps(
        {"version": version, "content": f"sha256:{h.hexdigest()[:12]}"},
        indent=2, ensure_ascii=False) + "\n"


def stamp_stub(root: Path, stubs: list[Stub]) -> Stub:
    """The planned stamp file for a payload root, digesting every OTHER stub
    (the stamp cannot be part of its own input or the build never converges)."""
    version = json.loads(PLUGIN_MANIFEST.read_text())["version"]
    return Stub(root / ".claude-plugin" / "build.json",
                payload_stamp(root, stubs, version))


def dist_surface_plans() -> list[Stub]:
    """Every dist/ stub for --surface plugin, plus the build stamp over them.

    m365 (independently managed, nested under dist/) deliberately never enters
    the digest: its stubs join the plan only under --surface m365/all, and a
    surface-dependent digest would make --check disagree between invocations."""
    plans = (plan_plugin() + plan_agent_skills() + plan_codex() + plan_pi()
             + plan_opencode_plugin())
    return plans + [stamp_stub(DIST_DIR, plans)]


def telemetry_surface_plans() -> list[Stub]:
    """The dist-telemetry/ plan plus its build stamp — same mechanism as dist/."""
    plans = plan_telemetry()
    return plans + [stamp_stub(DIST_TELEMETRY_DIR, plans)]


SURFACE_ROOTS = {
    "plugin": [DIST_DIR],
    "telemetry": [DIST_TELEMETRY_DIR],
    "m365": [M365_ROOT],
    "all": [DIST_DIR, DIST_TELEMETRY_DIR, M365_ROOT],
}


# ---------- orphan detection ----------


def nested_checkout_roots(surface: Path) -> tuple[Path, ...]:
    """Directories strictly below `surface` that are their own git checkout.

    A linked worktree or submodule carries a `.git` *file*; a nested clone
    carries a `.git` directory. Either way the tree below it is a copy of this
    repo, so its generated files carry our GENERATED_MARKER and the sweep would
    delete them — destroying tracked files belonging to another checkout, and
    failing --check on paths this run does not own (AWO-62).

    Strictly below: if the surface were itself a checkout this would skip the
    whole surface and silently disable its sweep, so that case is left alone.
    """
    return tuple(
        entry.parent
        for entry in surface.rglob(".git")
        if entry.parent != surface
    )


def find_orphans(planned_targets: set[Path], surfaces: list[Path]) -> list[Path]:
    """Every unplanned file under a surface. Surfaces are wholly generated —
    a payload root, or a subtree like dist/m365 owned by its own --surface
    invocation — so the plan is the only thing that decides."""
    orphans: list[Path] = []
    for surface in surfaces:
        if not surface.exists():
            continue
        nested = nested_checkout_roots(surface)
        for path in surface.rglob("*"):
            if not path.is_file():
                continue
            if any(root in path.parents for root in nested):
                continue
            if path in planned_targets:
                continue
            if surface in GENERATED_ROOTS and any(
                root in path.parents for root in INDEPENDENTLY_MANAGED_ROOTS
            ):
                # Owned by a separate --surface invocation; not this sweep's
                # concern even though it's nested inside a generated root.
                continue
            orphans.append(path)
    return orphans


# ---------- main ----------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 if a payload is out of date")
    parser.add_argument(
        "--surface",
        choices=["m365", "plugin", "telemetry", "all"],
        default="all",
    )
    args = parser.parse_args()

    stray = unclassified_context_paths()
    if stray:
        print(
            "Unclassified path(s) under context/. Add each to "
            "PAYLOAD_CONTEXT_PATHS or TEAM_DATA_CONTEXT_PATHS in tools/gather.py "
            "(see the predicate in the docstring above them):",
            file=sys.stderr,
        )
        for rel in stray:
            print(f"  context/{rel}", file=sys.stderr)
        return 1

    if not AGENTS_DIR.is_dir():
        print(f"error: {AGENTS_DIR} does not exist", file=sys.stderr)
        return 1
    if not PLUGIN_MANIFEST.exists():
        # Only the maintainer repo carries .claude-plugin/plugin.json; both
        # payload roots derive their manifests from it.
        print(f"error: {PLUGIN_MANIFEST} does not exist — not the awow "
              f"maintainer repo, nothing to build", file=sys.stderr)
        return 1

    surfaces = list(SURFACE_ROOTS[args.surface])
    plans: list[Stub] = []
    if DIST_DIR in surfaces:
        plans += dist_surface_plans()
    if DIST_TELEMETRY_DIR in surfaces:
        plans += telemetry_surface_plans()
    binary_plans: list[BinaryStub] = []
    if M365_ROOT in surfaces:
        from gather_m365 import M365BudgetError, M365ConfigError, plan_m365
        try:
            m365_plans, binary_plans = plan_m365(REPO_ROOT)
        except (M365BudgetError, M365ConfigError) as err:
            print(f"error: {err}", file=sys.stderr)
            return 1
        plans += m365_plans
    planned_targets = {p.target for p in plans} | {b.target for b in binary_plans}

    orphans = find_orphans(planned_targets, surfaces)

    drift: list[Stub | BinaryStub] = []
    for plan in plans:
        existing = plan.target.read_text() if plan.target.exists() else None
        stale = existing != plan.content
        if not stale and plan.mode is not None:
            stale = (plan.target.stat().st_mode & 0o777) != plan.mode
        if stale:
            drift.append(plan)
    for plan in binary_plans:
        if not plan.target.exists() or plan.target.read_bytes() != plan.content:
            drift.append(plan)

    if args.check:
        for plan in drift:
            rel = plan.target.relative_to(REPO_ROOT)
            kind = "create" if not plan.target.exists() else "update"
            print(f"{kind}: {rel}")
        for orphan in orphans:
            print(f"orphan: {orphan.relative_to(REPO_ROOT)}")
        if drift or orphans:
            print(
                f"\n{len(drift)} payload file(s) out of date, {len(orphans)} orphan(s). "
                f"Run without --check to apply.",
                file=sys.stderr,
            )
            return 1
        print("All payloads in sync.")
        return 0

    for plan in plans:
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        plan.target.write_text(plan.content)
        if plan.mode is not None:
            plan.target.chmod(plan.mode)
    for plan in binary_plans:
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        plan.target.write_bytes(plan.content)
    for orphan in orphans:
        orphan.unlink()
        print(f"removed orphan: {orphan.relative_to(REPO_ROOT)}")
        parent = orphan.parent
        while parent != REPO_ROOT and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    print(f"wrote {len(plans) + len(binary_plans)} payload file(s); {len(drift)} changed; {len(orphans)} orphan(s) removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
