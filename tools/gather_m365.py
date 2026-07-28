"""Render .agents/ + context/ into an M365 Copilot declarative-agent package.

Invoked via `python tools/gather.py --surface m365`. See
docs/superpowers/specs/2026-07-15-m365-copilot-harness-design.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gather import parse_frontmatter

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
    return M365Config(
        agent_name=fields["agent_name"],
        agent_description=fields["agent_description"],
        github_repo=fields["github_repo"],
        ref=fields["ref"],
        explore_starter=fields["explore_starter"],
        index_roots=roots,
        identity=body.strip(),
    )
