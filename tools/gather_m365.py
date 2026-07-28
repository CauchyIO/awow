"""Render .agents/ + context/ into an M365 Copilot declarative-agent package.

Invoked via `python tools/gather.py --surface m365`. See
docs/superpowers/specs/2026-07-15-m365-copilot-harness-design.md.
"""
from __future__ import annotations

import json
import re
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from gather import command_description, parse_frontmatter

CONFIG_REL = Path("context/tooling/m365/agent.md")
INSTRUCTION_BUDGET = 8000


class M365ConfigError(ValueError):
    pass


class M365BudgetError(ValueError):
    pass


@dataclass(frozen=True)
class M365Config:
    agent_name: str
    agent_description: str
    github_repo: str
    ref: str
    explore_starter: str
    index_roots: tuple[str, ...]
    identity: str


def load_config(repo_root: Path) -> M365Config:
    path = repo_root / CONFIG_REL
    if not path.is_file():
        raise M365ConfigError(f"m365 config missing: {path} — create it or drop --surface m365")
    fields, body = parse_frontmatter(path.read_text())
    required = ["agent_name", "agent_description", "github_repo", "ref", "explore_starter", "index_roots"]
    missing = [k for k in required if not fields.get(k)]
    if missing:
        raise M365ConfigError(f"{path}: missing required field(s): {', '.join(missing)}")
    roots = tuple(r.strip() for r in fields["index_roots"].split(",") if r.strip())
    if not roots:
        raise M365ConfigError(f"{path}: index_roots resolved to no roots")
    return M365Config(
        agent_name=fields["agent_name"],
        agent_description=fields["agent_description"],
        github_repo=fields["github_repo"],
        ref=fields["ref"],
        explore_starter=fields["explore_starter"],
        index_roots=roots,
        identity=body.strip(),
    )


def _tracked_files(repo_root: Path) -> set[str] | None:
    inside = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
    )
    if inside.returncode != 0 or inside.stdout.decode().strip() != "true":
        return None
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        capture_output=True,
    )
    if result.returncode != 0:
        raise M365ConfigError(f"git ls-files failed in {repo_root}: {result.stderr.decode().strip()}")
    return set(result.stdout.decode().rstrip("\0").split("\0")) - {""}


@dataclass(frozen=True)
class CommandEntry:
    name: str
    rel_path: str
    starter: str
    description: str


def parse_m365_block(text: str) -> dict | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    lines = text[4:end].splitlines()
    try:
        start = next(i for i, l in enumerate(lines) if re.match(r"^m365:\s*$", l))
    except StopIteration:
        return None
    block: dict = {}
    for line in lines[start + 1:]:
        m = re.match(r"^  ([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m:
            break
        key, raw = m.group(1), m.group(2).strip().strip('"').strip("'")
        block[key] = {"true": True, "false": False}.get(raw, raw)
    block.setdefault("include", False)
    block.setdefault("conversation_starter", None)
    return block


_COMPUTE_TRACKED = object()


def included_commands(repo_root: Path, tracked: set[str] | None = _COMPUTE_TRACKED) -> list[CommandEntry]:
    if tracked is _COMPUTE_TRACKED:
        tracked = _tracked_files(repo_root)
    entries = []
    commands_root = repo_root / ".agents" / "commands"
    for source in sorted(commands_root.rglob("*.md")):
        if source.name == "README.md" or "_workitem-archetypes" in source.parts:
            continue
        rel_posix = source.relative_to(repo_root).as_posix()
        if tracked is not None and rel_posix not in tracked:
            continue
        text = source.read_text()
        block = parse_m365_block(text)
        if not block:
            continue
        include = block["include"]
        if not isinstance(include, bool):
            raise M365ConfigError(f"{source}: m365.include must be true or false, got {repr(include)}")
        if include is not True:
            continue
        starter = block["conversation_starter"]
        if not starter:
            raise M365ConfigError(f"{source}: m365.include is true but conversation_starter is missing")
        fields, body = parse_frontmatter(text)
        entries.append(CommandEntry(
            name=source.stem,
            rel_path=source.relative_to(repo_root).as_posix(),
            starter=starter,
            description=command_description(fields, body),
        ))
    entries.sort(key=lambda e: e.name)
    return entries


def _describe(path: Path) -> str:
    fields, body = parse_frontmatter(path.read_text())
    desc = fields.get("description") or command_description(fields, body)
    desc = " ".join(desc.split())
    return desc or path.stem


def build_file_index(
    repo_root: Path, roots: tuple[str, ...], tracked: set[str] | None = _COMPUTE_TRACKED
) -> list[tuple[str, str]]:
    if tracked is _COMPUTE_TRACKED:
        tracked = _tracked_files(repo_root)
    seen: dict[str, str] = {}
    for root in roots:
        base = repo_root / root
        if not base.is_dir():
            raise M365ConfigError(f"index root does not exist: {base}")
        for path in sorted(base.rglob("*.md")):
            if "_workitem-archetypes" in path.parts:
                continue
            rel_posix = path.relative_to(repo_root).as_posix()
            if tracked is not None and rel_posix not in tracked:
                continue
            seen[rel_posix] = _describe(path)
    return sorted(seen.items())


def assemble_instructions(config: M365Config, commands: list[CommandEntry], index: list[tuple[str, str]]) -> str:
    lines = [config.identity, "", "## How you work", ""]
    lines.append(
        "On a conversation starter or a matching request: find the playbook path in the "
        "routing table below, call fetchAwowContext with that exact path, and follow the "
        "fetched playbook exactly. If a fetch fails, stop and name the path that failed — "
        "never improvise a procedure from memory. For open questions, fetch the most "
        "relevant file(s) from the index below before answering."
    )
    lines += ["", "## Routing", ""]
    for cmd in commands:
        lines.append(f'- "{cmd.starter}" -> fetch {cmd.rel_path}')
    lines += ["", "## Files you can fetch", ""]
    for rel, desc in index:
        lines.append(f"- {rel} — {desc}")
    text = "\n".join(lines) + "\n"
    if len(text) > INSTRUCTION_BUDGET:
        raise M365BudgetError(
            f"assembled instructions are {len(text)} chars, over the {INSTRUCTION_BUDGET} cap; "
            f"trim index_roots in {CONFIG_REL} or the agent identity block"
        )
    return text


def dump_json(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def build_declarative_agent(config: M365Config, instructions: str, commands: list[CommandEntry]) -> dict:
    starters = [{"title": config.explore_starter, "text": config.explore_starter}]
    starters += [{"title": c.starter, "text": c.starter} for c in commands]
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.7/schema.json",
        "version": "v1.7",
        "name": config.agent_name,
        "description": config.agent_description,
        "instructions": instructions,
        "conversation_starters": starters,
        "actions": [{"id": "awowFetch", "file": "fetchAwowContext.plugin.json"}],
    }


def _short_description(description: str, limit: int = 80) -> str:
    if len(description) <= limit:
        return description
    truncated = description[:limit]
    cut = truncated.rfind(" ")
    return truncated[:cut] if cut != -1 else truncated


def build_teams_manifest(config: M365Config) -> dict:
    app_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://github.com/{config.github_repo}/m365"))
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.19/MicrosoftTeams.schema.json",
        "manifestVersion": "1.19",
        "version": "0.1.0",
        "id": app_id,
        "developer": {
            "name": config.github_repo.split("/")[0],
            "websiteUrl": f"https://github.com/{config.github_repo}",
            "privacyUrl": f"https://github.com/{config.github_repo}",
            "termsOfUseUrl": f"https://github.com/{config.github_repo}",
        },
        "name": {"short": config.agent_name, "full": config.agent_name},
        "description": {"short": _short_description(config.agent_description), "full": config.agent_description},
        "icons": {"color": "color.png", "outline": "outline.png"},
        "accentColor": "#0F62FE",
        "copilotAgents": {
            "declarativeAgents": [{"id": "awowCoach", "file": "declarativeAgent.json"}]
        },
    }


def build_plugin_manifest(config: M365Config) -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/copilot/plugin/v2.3/schema.json",
        "schema_version": "v2.3",
        "name_for_human": f"{config.agent_name} fetch",
        "description_for_human": "Reads awow context and playbook files live from the git repository.",
        "namespace": "awowfetch",
        "functions": [{
            "name": "fetchAwowContext",
            "description": "Fetch the exact markdown file at a repo-relative path from the awow repository. Always fetch a playbook before executing it.",
        }],
        "runtimes": [{
            "type": "OpenApi",
            "auth": {"type": "None"},
            "spec": {"url": "fetchAwowContext.openapi.json"},
            "run_for_functions": ["fetchAwowContext"],
        }],
    }


def build_openapi_spec(config: M365Config) -> dict:
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "awow context fetch",
            "description": "Read-only fetch of markdown files from the public awow repository.",
            "version": "0.1.0",
        },
        "servers": [{"url": "https://raw.githubusercontent.com"}],
        "paths": {
            f"/{config.github_repo}/{config.ref}/{{filePath}}": {
                "get": {
                    "operationId": "fetchAwowContext",
                    "summary": "Fetch one repo file as raw markdown",
                    "parameters": [
                        {
                            "name": "filePath",
                            "in": "path",
                            "required": True,
                            "description": "Repo-relative file path. Encode each '/' as %2F, e.g. .agents%2Fcommands%2Frefinement-prep.md",
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Raw file content",
                            "content": {"text/plain": {"schema": {"type": "string"}}},
                        },
                        "404": {"description": "File not found at this path/ref"},
                    },
                }
            }
        },
    }


def plan_m365(repo_root: Path):
    from gather import BinaryStub, Stub  # local import: gather imports this module lazily
    config = load_config(repo_root)
    tracked = _tracked_files(repo_root)
    commands = included_commands(repo_root, tracked)
    index = build_file_index(repo_root, config.index_roots, tracked)
    instructions = assemble_instructions(config, commands, index)
    pkg = repo_root / "dist" / "m365" / "appPackage"
    text_stubs = [
        Stub(pkg / "declarativeAgent.json", dump_json(build_declarative_agent(config, instructions, commands))),
        Stub(pkg / "manifest.json", dump_json(build_teams_manifest(config))),
        Stub(pkg / "fetchAwowContext.plugin.json", dump_json(build_plugin_manifest(config))),
        Stub(pkg / "fetchAwowContext.openapi.json", dump_json(build_openapi_spec(config))),
    ]
    assets = repo_root / "context" / "tooling" / "m365" / "assets"
    binary_stubs = [
        BinaryStub(pkg / "color.png", (assets / "color.png").read_bytes()),
        BinaryStub(pkg / "outline.png", (assets / "outline.png").read_bytes()),
    ]
    return text_stubs, binary_stubs
