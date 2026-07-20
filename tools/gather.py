"""Sync .agents/ → .claude/ + .github/ as pointer stubs.

.agents/ is the single source of truth. This script generates tiny pointer
stubs in the harness folders that redirect the agent to the canonical source.
No substantive content is copied — only the frontmatter (name, description)
the harness needs for discovery, plus a one-line body telling the agent to
read the real file under .agents/.

Why pointers (not copies, not symlinks):
- Copies drift the moment someone forgets to re-run gather.
- Symlinks are fragile across platforms and cannot carry harness-specific
  frontmatter.
- Pointers contain no substantive content, so there is nothing to drift.
  The only thing gather syncs is discovery metadata.

Layout produced
---------------
    .agents/AGENTS.md                    → AGENTS.md          (repo root)
                                         → .claude/CLAUDE.md
                                         → .github/copilot-instructions.md
                                         → .github/AGENTS.md

The repo-root `AGENTS.md` is the cross-vendor instruction-file standard: a
harness that reads it natively from the root (Codex among them) is steered to
`.agents/AGENTS.md` with no install step. It is emitted for every in-repo
surface but not for the `dist/` plugin payload.
    .agents/commands/<name>.md           → .claude/commands/<name>.md
                                         → .github/prompts/<name>.prompt.md

The `.prompt.md` extension under .github/prompts/ is required: VS Code's
GitHub Copilot Chat discovers prompt files by that exact suffix; plain `.md`
is silently ignored.
    .agents/skills/<name>/SKILL.md       → .claude/skills/<name>/SKILL.md
                                         → .github/skills/<name>/SKILL.md
    .agents/skills/<name>.md             → .claude/skills/<name>/SKILL.md
                                         → .github/skills/<name>/SKILL.md
                                            (declarative skills are wrapped
                                            in a synthesised SKILL.md stub
                                            so the harness discovers them)

Files named README.md and any path under `_workitem-archetypes/` are not mirrored;
they are documentation, not commands.

Plugin payload (dist/)
----------------------
The `plugin` surface builds the distributable Claude Code plugin under
`dist/` — full copies, not pointers, because plugin content runs inside an
adopter's project where `.agents/` does not exist:

    .agents/commands/<name>.md           → dist/commands/<name>.md
    commands/<name>.md  (legacy /awowify) → dist/commands/<name>.md
    .agents/skills/<name>/**             → dist/skills/<name>/**
    .agents/skills/<name>.md             → dist/skills/<name>/SKILL.md
    (every command AND skill, as a skill) → dist/agent-skills/<name>/SKILL.md
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
This surface only applies in the awow maintainer repo (gated on
`.claude-plugin/plugin.json`); vendored adopter repos skip it.

Usage
-----
    python tools/gather.py                  # write all surfaces (incl. dist/)
    python tools/gather.py --check          # exit 1 if any output is out of date
    python tools/gather.py --surface claude # only emit to .claude/
    python tools/gather.py --surface github # only emit to .github/
    python tools/gather.py --surface plugin # only build dist/
    python tools/gather.py --surface both   # .claude/ + .github/, no dist/

Orphans
-------
Stubs whose source has been removed are reported (and removed in non-check
mode) only if they carry the GENERATED header this script writes, so user-
added files are never deleted. Under dist/ every unplanned file is an orphan
— the payload is fully generated, so nothing user-authored can live there.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".agents"
CLAUDE_DIR = REPO_ROOT / ".claude"
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
PI_MANIFEST = DIST_DIR / "package.json"
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
ROOT_COMMANDS_DIR = REPO_ROOT / "commands"
HOOKS_DIR = REPO_ROOT / "hooks"

# Runtime tools shipped in a plugin payload, split by which plugin needs them.
# Everything else under tools/ stays maintainer-only: those scripts resolve
# REPO_ROOT from __file__ and would operate on the plugin install dir if
# shipped (hub-and-spoke WI-4).
#
# Base plugin: the pre-push leak scan and its pattern file. Nothing else — the
# three session-analysis tools below served only skills that have moved.
PLUGIN_TOOL_PATHS = [
    "hooks/leak-patterns.txt",
    "hooks/pre-push",
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
]

# Team data: /setup-awow authors these per adopter. No useful default exists,
# and a generic stub is worse than absence — commands branch on absence
# (see the board fallback, design spec 4.2), but cannot branch on boilerplate.
TEAM_DATA_CONTEXT_PATHS = [
    "README.md",
    "company",
    "kb-inbox/_synthesis-log.md",
    "knowledge-base/architecture",
    "knowledge-base/decisions",
    "knowledge-base/glossary.md",
    "knowledge-base/patterns",
    "knowledge-base/runbooks",
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
SKIP_DIR_PARTS = {"_workitem-archetypes"}
GENERATED_MARKER = "<!-- GENERATED by tools/gather.py"

# Payload roots that this script wholly owns: under one of these, EVERY
# unplanned file is an orphan, marker or not. That distinction is load-bearing,
# because full-copy payload content carries no GENERATED header at all —
# plugin_command_copy, command_skill_stub, and skill_stubs each emit the source
# body verbatim. A payload root missing from this tuple therefore has its
# orphans silently ignored while --check stays green. Add every new payload
# root here in the same change that creates it.
GENERATED_ROOTS = (DIST_DIR, DIST_TELEMETRY_DIR)


@dataclass(frozen=True)
class Stub:
    target: Path
    content: str
    mode: int | None = None  # exec bits matter for hooks and scripts


# ---------- minimal frontmatter parser ----------

_FM_DELIM = "---\n"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (scalar fields, body). Lists and block scalars are ignored — we
    only need top-level strings like name, description, removes_pain."""
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


# ---------- relative path helpers ----------


def rel_link(stub_target: Path, source: Path) -> str:
    """Markdown-link path from a stub file to its source under .agents/."""
    rel = Path("../" * (len(stub_target.relative_to(REPO_ROOT).parts) - 1)) / source.relative_to(REPO_ROOT)
    return str(rel)


# ---------- stub generators ----------


def header(source: Path) -> str:
    rel = source.relative_to(REPO_ROOT)
    return f"{GENERATED_MARKER} — DO NOT EDIT. Source: {rel} -->"


def command_description(fields: dict[str, str], body: str) -> str:
    """Best-effort one-liner description for a command stub.

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


def gen_command_stub(source: Path, stub_target: Path) -> str:
    text = source.read_text()
    fields, body = parse_frontmatter(text)
    desc = command_description(fields, body)
    link = rel_link(stub_target, source)
    fm_lines = ["---"]
    if desc:
        # YAML-quote (double, with internal quote escape)
        fm_lines.append(f'description: "{desc.replace(chr(34), chr(92) + chr(34))}"')
    fm_lines.append("---")
    fm = "\n".join(fm_lines)
    return (
        f"{fm}\n\n"
        f"{header(source)}\n\n"
        f"Execute the command defined at [`{source.relative_to(REPO_ROOT)}`]({link}). "
        f"Read that file and follow its instructions, applying any arguments the user provided "
        f"to this invocation. The body of this stub carries no substantive content — the real "
        f"prompt lives at the path above.\n\n"
        f"Edits must be made in `{source.relative_to(REPO_ROOT)}` and re-mirrored with "
        f"`python tools/gather.py`.\n"
    )


def gen_skill_stub(source: Path, stub_target: Path, name: str, description: str) -> str:
    link = rel_link(stub_target, source)
    desc_escaped = description.replace(chr(34), chr(92) + chr(34))
    scripts_hint = ""
    if source.name == "SKILL.md" and (source.parent / "scripts").is_dir():
        scripts_rel = (source.parent / "scripts").relative_to(REPO_ROOT)
        scripts_hint = (
            f"\nScripts bundled with this skill live at `{scripts_rel}/` and should be invoked "
            f"from the repo root.\n"
        )
    return (
        f"---\n"
        f"name: {name}\n"
        f'description: "{desc_escaped}"\n'
        f"---\n\n"
        f"{header(source)}\n\n"
        f"# {name}\n\n"
        f"This skill's full rubric lives at [`{source.relative_to(REPO_ROOT)}`]({link}). "
        f"Read that file before acting on this skill. The body of this stub carries no "
        f"substantive content.\n"
        f"{scripts_hint}\n"
        f"Edits must be made in `{source.relative_to(REPO_ROOT)}` and re-mirrored with "
        f"`python tools/gather.py`.\n"
    )


def gen_top_level_instructions(stub_target: Path, harness_label: str) -> str:
    source = AGENTS_DIR / "AGENTS.md"
    link = rel_link(stub_target, source)
    return (
        f"{header(source)}\n\n"
        f"# Agent instructions ({harness_label})\n\n"
        f"This repo uses a single source of truth for agent instructions, commands, and skills: "
        f"the `.agents/` directory. **Before doing anything else, read "
        f"[`.agents/AGENTS.md`]({link}) and follow its instructions.** That file is the canonical "
        f"rule set for both Claude Code and GitHub Copilot working in this repo.\n\n"
        f"- Commands → `.agents/commands/` (also discoverable from this surface as pointer stubs)\n"
        f"- Skills → `.agents/skills/` (also discoverable from this surface as pointer stubs)\n"
        f"- Conventions and context → `context/`\n\n"
        f"Files in this folder are auto-generated pointer stubs produced by `tools/gather.py`. "
        f"They exist only so the harness can discover commands and skills natively; the "
        f"substantive content lives under `.agents/`. Edits made here are overwritten on the "
        f"next gather.\n"
    )


def gen_root_agents_stub(stub_target: Path) -> str:
    """Repo-root `AGENTS.md` — the cross-vendor instruction-file standard.

    Distinct from the per-surface top-level stubs: no harness label, neutral
    wording, and it names AGENTS.md's cross-vendor role (a harness that reads
    the root file natively, e.g. Codex, is steered with no install step)."""
    source = AGENTS_DIR / "AGENTS.md"
    link = rel_link(stub_target, source)
    return (
        f"{header(source)}\n\n"
        f"# Agent instructions\n\n"
        f"This repo uses a single source of truth for agent instructions, commands, and "
        f"skills: the `.agents/` directory. **Before doing anything else, read "
        f"[`.agents/AGENTS.md`]({link}) and follow its instructions.** That file is the "
        f"canonical rule set for every agent working in this repo.\n\n"
        f"`AGENTS.md` is the cross-vendor instruction-file standard. A harness that reads it "
        f"natively from the repo root — Codex among them — is steered to the source above with "
        f"no install step. Commands live under `.agents/commands/`, skills under "
        f"`.agents/skills/`, and conventions and context under `context/`.\n\n"
        f"This file is an auto-generated pointer produced by `tools/gather.py`; the substantive "
        f"content lives under `.agents/`. Edits here are overwritten on the next gather.\n"
    )


def gen_folder_readme(stub_target: Path, source_dir: Path, harness_label: str) -> str:
    link = rel_link(stub_target, source_dir)
    return (
        f"{header(source_dir)}\n\n"
        f"# {stub_target.parent.name}/ — auto-generated pointer stubs\n\n"
        f"Files here are pointer stubs produced by `tools/gather.py`. Each one carries the "
        f"frontmatter the {harness_label} harness needs for discovery plus a one-line body "
        f"pointing to the canonical source under [`{source_dir.relative_to(REPO_ROOT)}/`]({link}).\n\n"
        f"Do not edit files in this folder. Edit the source and re-run "
        f"`python tools/gather.py`.\n"
    )


# ---------- planning ----------


def is_skipped(path: Path) -> bool:
    if path.name in SKIP_FILENAMES:
        return True
    if any(part in SKIP_DIR_PARTS for part in path.relative_to(AGENTS_DIR).parts):
        return True
    return False


def plan_top_level() -> list[Stub]:
    plans = []
    for target, label in [
        (CLAUDE_DIR / "CLAUDE.md", ".claude/"),
        (GITHUB_DIR / "copilot-instructions.md", ".github/"),
        (GITHUB_DIR / "AGENTS.md", ".github/"),
    ]:
        plans.append(Stub(target, gen_top_level_instructions(target, label)))
    root_agents = REPO_ROOT / "AGENTS.md"
    plans.append(Stub(root_agents, gen_root_agents_stub(root_agents)))
    return plans


def plan_commands() -> list[Stub]:
    plans: list[Stub] = []
    commands_root = AGENTS_DIR / "commands"
    for source in sorted(commands_root.rglob("*.md")):
        if is_skipped(source):
            continue
        for target_dir, ext in [
            (CLAUDE_DIR / "commands", ".md"),
            (GITHUB_DIR / "prompts", ".prompt.md"),
        ]:
            target = target_dir / (source.stem + ext)
            plans.append(Stub(target, gen_command_stub(source, target)))
    return plans


def plan_skills() -> list[Stub]:
    plans: list[Stub] = []
    skills_root = AGENTS_DIR / "skills"
    for entry in sorted(skills_root.iterdir()):
        if entry.name in SKIP_FILENAMES:
            continue
        if entry.is_dir():
            skill_file = entry / "SKILL.md"
            if not skill_file.exists():
                continue
            text = skill_file.read_text()
            fields, body = parse_frontmatter(text)
            name = fields.get("name", entry.name)
            description = fields.get("description") or first_h1(body) or ""
            source = skill_file
        elif entry.is_file() and entry.suffix == ".md":
            text = entry.read_text()
            fields, body = parse_frontmatter(text)
            name = fields.get("name", entry.stem)
            description = fields.get("description") or first_h1(body) or ""
            source = entry
        else:
            continue
        for target_dir in [CLAUDE_DIR / "skills", GITHUB_DIR / "skills"]:
            target = target_dir / name / "SKILL.md"
            plans.append(Stub(target, gen_skill_stub(source, target, name, description)))
    return plans


def copy_stub(target: Path, source: Path) -> Stub:
    return Stub(target, source.read_text(), source.stat().st_mode & 0o777)


# Path tokens (see .agents/AGENTS.md "Path tokens"): {AWOW_TOOLS} and
# {AWOW_ROOT} resolve at build time for the plugin surface — the payload knows
# where it lives. {HUB} and {PROJECT} ship as-is; the session reflex teaches
# their resolution.
PLUGIN_TOKEN_SUBSTITUTIONS = [
    ("{AWOW_TOOLS}", "${CLAUDE_PLUGIN_ROOT}/tools"),
    ("{AWOW_ROOT}", "${CLAUDE_PLUGIN_ROOT}"),
]


# A prompt body must be able to NAME a token without USING it — using-awow and
# AGENTS.md both document the token vocabulary and are themselves rendered.
# {{TOKEN}} is the escape: protected before substitution, unwrapped after.
# Scoped to the four path-token names deliberately: a blanket {{[A-Z_]+}} escape
# would also unwrap the {{PLACEHOLDER}} markers /daily-digest documents for the
# adopter's HTML template, corrupting the syntax that file exists to describe.
PATH_TOKEN_NAMES = ("HUB", "PROJECT", "AWOW_TOOLS", "AWOW_ROOT")
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
# (Residual literal ${CLAUDE_PLUGIN_ROOT} in a few Claude-channel command bodies —
# awowify, using-awow — is WI-2 content-sweep debt, tracked separately.)
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


def plugin_command_copy(target: Path, source: Path, text: str | None = None) -> Stub:
    """Full copy, with a `description:` injected into the frontmatter when the
    source only carries it in the H1 — the plugin picker needs the field. Pass
    `text` to reuse an already-read body and avoid a second read of `source`."""
    text = render_plugin_body(source.read_text() if text is None else text)
    mode = source.stat().st_mode & 0o777
    fields, body = parse_frontmatter(text)
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
    fields, body = parse_frontmatter(text)
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
    if ROOT_COMMANDS_DIR.is_dir():
        for source in sorted(ROOT_COMMANDS_DIR.glob("*.md")):
            if source.name in SKIP_FILENAMES:
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
    """Pi package manifest into dist/. `pi install <dist>` reads `pi.skills` and surfaces
    the commands-as-skills. Pi discovers root AGENTS.md + the user's own .agents/skills
    natively, so the package is the whole integration — no `.pi/extensions` needed."""
    src = json.loads(PLUGIN_MANIFEST.read_text())
    pkg = {
        "name": src["name"],
        "version": src["version"],
        "description": src["description"],
        "license": src.get("license", "MIT"),
        "homepage": src.get("homepage"),
        "repository": src.get("repository"),
        "keywords": ["pi-package"],
        "pi": {"skills": ["./agent-skills"]},
    }
    return [Stub(PI_MANIFEST, json.dumps(pkg, indent=2, ensure_ascii=False) + "\n")]


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
    reach these as {AWOW_ROOT}/context/... — {HUB} first so a vendored override
    wins, then {AWOW_ROOT}. See the predicate above PAYLOAD_CONTEXT_PATHS."""
    plans: list[Stub] = []
    for path in sorted(CONTEXT_DIR.rglob("*")):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel = path.relative_to(CONTEXT_DIR).as_posix()
        if classify_context_path(rel) != "payload":
            continue
        plans.append(
            Stub(
                dest_root / "context" / rel,
                render(path.read_text()),
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

    Uses render_plugin_body via plugin_command_copy: Copilot CLI resolves
    ${CLAUDE_PLUGIN_ROOT}. Only Codex and Pi need render_agent_skills_body."""
    manifest = json.loads((GITHUB_DIR / "plugin" / "plugin.json").read_text())
    plans = [
        Stub(
            DIST_DIR / ".github" / "plugin" / "plugin.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )
    ]
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


def plan_workitem_archetypes() -> list[Stub]:
    """The archetype handlers /process-workitem dispatches to. SKIP_DIR_PARTS
    keeps them out of the command surface — they are handlers, not commands, and
    must not appear in the picker — but the payload still needs them on disk, so
    they ship as data under dist/commands/_workitem-archetypes/."""
    src = AGENTS_DIR / "commands" / "_workitem-archetypes"
    if not src.is_dir():
        return []
    return [
        Stub(
            DIST_DIR / "commands" / "_workitem-archetypes" / f.name,
            render_plugin_body(f.read_text()),
            f.stat().st_mode & 0o777,
        )
        for f in sorted(src.glob("*.md"))
    ]


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
            "# dist/ — built awow plugin payload\n\n"
            "This directory is the installable Claude Code plugin, built by "
            "`python tools/gather.py --surface plugin` from `.agents/` (plus "
            "`hooks/`, the legacy `commands/`, and a runtime slice of `tools/`). "
            "`.claude-plugin/marketplace.json` points installers here so the "
            "maintainer workspace (`meta/`, `context/`, guides, tests) never "
            "ships to adopters.\n\n"
            "Do not edit files in this directory — edit the source and re-run "
            "the gather. Any file here that the build did not plan is deleted "
            "on the next run.\n",
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
    if ROOT_COMMANDS_DIR.is_dir():
        for source in sorted(ROOT_COMMANDS_DIR.glob("*.md")):
            if source.name in SKIP_FILENAMES:
                continue
            text = source.read_text()
            if is_vendored_channel(text):
                continue
            plans.append(plugin_command_copy(DIST_DIR / "commands" / source.name, source, text))
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
    plans.extend(plan_workitem_archetypes())
    return plans


def plan_folder_readmes() -> list[Stub]:
    plans: list[Stub] = []
    for target, source_dir, label in [
        (CLAUDE_DIR / "commands" / "README.md", AGENTS_DIR / "commands", "Claude Code"),
        (CLAUDE_DIR / "skills" / "README.md", AGENTS_DIR / "skills", "Claude Code"),
        (GITHUB_DIR / "prompts" / "README.md", AGENTS_DIR / "commands", "GitHub Copilot"),
        (GITHUB_DIR / "skills" / "README.md", AGENTS_DIR / "skills", "GitHub Copilot"),
    ]:
        plans.append(Stub(target, gen_folder_readme(target, source_dir, label)))
    return plans


SURFACE_ROOTS = {
    "claude": [CLAUDE_DIR],
    "github": [GITHUB_DIR],
    "plugin": [DIST_DIR],
    "telemetry": [DIST_TELEMETRY_DIR],
    "both": [CLAUDE_DIR, GITHUB_DIR],
    "all": [CLAUDE_DIR, GITHUB_DIR, DIST_DIR, DIST_TELEMETRY_DIR],
}


def filter_surface(plans: list[Stub], surface: str) -> list[Stub]:
    roots = SURFACE_ROOTS[surface]
    kept: list[Stub] = []
    for p in plans:
        if p.target.parent == REPO_ROOT:
            # Repo-root instruction files (AGENTS.md) are harness-neutral: they
            # belong to every in-repo surface but never to a payload root,
            # which owns only its own tree.
            if surface not in ("plugin", "telemetry"):
                kept.append(p)
        elif any(root in p.target.parents for root in roots):
            kept.append(p)
    return kept


# ---------- orphan detection ----------


def find_orphans(planned_targets: set[Path], surfaces: list[Path]) -> list[Path]:
    orphans: list[Path] = []
    for surface in surfaces:
        if not surface.exists():
            continue
        for path in surface.rglob("*"):
            if not path.is_file():
                continue
            if path in planned_targets:
                continue
            # A payload root is wholly generated — every unplanned file there
            # is an orphan. Elsewhere only files carrying the GENERATED header
            # are, so user-added files are never deleted. Membership, not
            # identity: there is more than one payload root (GENERATED_ROOTS).
            if surface in GENERATED_ROOTS:
                orphans.append(path)
                continue
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            if GENERATED_MARKER in text:
                orphans.append(path)
    return orphans


# ---------- main ----------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="exit 1 if stubs are out of date")
    parser.add_argument(
        "--surface",
        choices=["claude", "github", "plugin", "telemetry", "both", "all"],
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

    surfaces = list(SURFACE_ROOTS[args.surface])
    payload_roots = [r for r in (DIST_DIR, DIST_TELEMETRY_DIR) if r in surfaces]
    if payload_roots and not PLUGIN_MANIFEST.exists():
        # Vendored adopter repos have no plugin manifest and no payload to
        # build; only the maintainer repo carries .claude-plugin/plugin.json.
        # Both payload roots derive their manifests from it.
        if args.surface in ("plugin", "telemetry"):
            print(f"error: {PLUGIN_MANIFEST} does not exist — not the awow "
                  f"maintainer repo, nothing to build", file=sys.stderr)
            return 1
        for root in payload_roots:
            surfaces.remove(root)
        print(f"note: {PLUGIN_MANIFEST.relative_to(REPO_ROOT)} not found — payload surfaces skipped")

    plans = (
        plan_top_level()
        + plan_folder_readmes()
        + plan_commands()
        + plan_skills()
    )
    if DIST_DIR in surfaces:
        plans += plan_plugin()
        plans += plan_agent_skills()
        plans += plan_codex()
        plans += plan_pi()
    if DIST_TELEMETRY_DIR in surfaces:
        plans += plan_telemetry()
    plans = filter_surface(plans, args.surface)
    planned_targets = {p.target for p in plans}

    orphans = find_orphans(planned_targets, surfaces)

    drift: list[Stub] = []
    for plan in plans:
        existing = plan.target.read_text() if plan.target.exists() else None
        stale = existing != plan.content
        if not stale and plan.mode is not None:
            stale = (plan.target.stat().st_mode & 0o777) != plan.mode
        if stale:
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
                f"\n{len(drift)} stub(s) out of date, {len(orphans)} orphan(s). "
                f"Run without --check to apply.",
                file=sys.stderr,
            )
            return 1
        print("All stubs in sync.")
        return 0

    for plan in plans:
        plan.target.parent.mkdir(parents=True, exist_ok=True)
        plan.target.write_text(plan.content)
        if plan.mode is not None:
            plan.target.chmod(plan.mode)
    for orphan in orphans:
        orphan.unlink()
        print(f"removed orphan: {orphan.relative_to(REPO_ROOT)}")
        parent = orphan.parent
        while parent != REPO_ROOT and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    print(f"wrote {len(plans)} stub(s); {len(drift)} changed; {len(orphans)} orphan(s) removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
