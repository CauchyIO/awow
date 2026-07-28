"""Idempotent cascade check for the department layer.

Read-only sweep of a department repo: verifies the team registry, the
Serves: linkage between team quarterly docs and the department OKR doc,
backlinks, and pin freshness. Exit 0 clean, 1 findings, 2 config error.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path


class CascadeConfigError(ValueError):
    pass


INDIRECTION_REL = Path("context/tooling/department.md")
REQUIRED_FIELDS = ["teams_root", "read_scope", "decisions_dir", "stale_after_days"]


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    fields = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.+)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def load_indirection(repo_root: Path) -> dict:
    path = repo_root / INDIRECTION_REL
    if not path.is_file():
        raise CascadeConfigError(f"missing {path} — run /setup-department first")
    fields = _frontmatter(path.read_text())
    missing = [k for k in REQUIRED_FIELDS if k not in fields]
    if missing:
        raise CascadeConfigError(f"{path}: missing field(s): {', '.join(missing)}")
    return {
        "teams_root": fields["teams_root"],
        "read_scope": [s.strip() for s in fields["read_scope"].split(",") if s.strip()],
        "decisions_dir": fields["decisions_dir"],
        "stale_after_days": int(fields["stale_after_days"]),
    }


def parse_registry(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("Team", "---", ":---"):
            if not re.match(r"^-+$", cells[0]):
                rows.append({"team": cells[0], "path": cells[1], "lead": cells[2]})
    if not rows:
        raise CascadeConfigError("teams.md: no registry rows found (need a | Team | Path | Lead | table)")
    return rows


def parse_okr_ids(text: str) -> set[str]:
    ids = set(re.findall(r"^## (O\d+)\b", text, flags=re.M))
    ids |= set(re.findall(r"^- (O\d+\.KR\d+):", text, flags=re.M))
    return ids


def parse_serves_headers(text: str) -> list[str]:
    serves = []
    for line in text.splitlines():
        m = re.match(r"^Serves: (\S+)$", line)
        if m:
            serves.append(m.group(1))
        elif line.strip():
            break
    return serves


def find_quarter_doc(repo_root: Path) -> Path:
    docs = sorted((repo_root / "context" / "department").glob("okrs-*.md"))
    if not docs:
        raise CascadeConfigError("no context/department/okrs-<quarter>.md found")
    return docs[-1]
