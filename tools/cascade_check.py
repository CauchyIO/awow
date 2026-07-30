"""Idempotent cascade check for the department layer.

Read-only sweep of a department repo: verifies the team registry, the
Serves: linkage between team quarterly docs and the department OKR doc,
backlinks, and pin freshness. Exit 0 clean, 1 findings, 2 config error.

CLI: `python tools/cascade_check.py [--json] [--root <path>]`, run from the
department repo root (or pass --root for testability; cwd remains the
default when --root is omitted).

Finding class taxonomy is closed by design (downstream stages depend on the
exact set of strings). In particular `registered-missing` is the single
class for every registry row whose submodule state cannot be verified:
directory missing, not a git checkout, or its pin/remote unresolvable via
git — see each finding's `detail` for the specific cause. A team's
`registered-missing` finding short-circuits all remaining checks for that
team (one cause, one finding); other teams are unaffected.
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

    try:
        stale_after_days = int(fields["stale_after_days"])
    except ValueError:
        raise CascadeConfigError(f"{path}: stale_after_days must be an integer, got '{fields['stale_after_days']}'")

    return {
        "teams_root": fields["teams_root"],
        "read_scope": [s.strip() for s in fields["read_scope"].split(",") if s.strip()],
        "decisions_dir": fields["decisions_dir"],
        "stale_after_days": stale_after_days,
    }


def parse_registry(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line looks like a table row (starts and ends with |)
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]

            # Skip header and separator rows
            if cells[0] in ("Team", "---", ":---"):
                continue
            if re.match(r"^-+$", cells[0]):
                continue

            # If it looks like a table row but doesn't have 3 cells, error
            if len(cells) != 3:
                raise CascadeConfigError(f"teams.md: malformed row '{stripped}' (expected 3 cells, got {len(cells)})")

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


class _GitCheckError(Exception):
    """A git command inside a per-team check failed.

    Always caught within run_check and converted into a `registered-missing`
    finding for that team — a team whose gitlink or history can't be read is
    not verifiably checked out, which is exactly what that finding means.
    Never propagates out of run_check; never a silent skip.
    """


def _run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise _GitCheckError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _origin_url(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise CascadeConfigError(
            f"{repo_root}: no 'origin' remote configured (needed to verify team backlinks) — "
            f"fix: git -C {repo_root} remote add origin <url> ({result.stderr.strip()})"
        )
    return result.stdout.strip()


def _normalize_url(url: str) -> str:
    normalized = url.strip()
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def _is_git_checkout(team_path: Path) -> bool:
    return team_path.is_dir() and (team_path / ".git").exists()


def _pin_sha(repo_root: Path, team_path_rel: str) -> str:
    out = _run_git(["-C", str(repo_root), "ls-tree", "HEAD", team_path_rel])
    line = out.strip().splitlines()[0] if out.strip() else ""
    header, _, _path = line.partition("\t")
    parts = header.split()
    if len(parts) != 3 or parts[0] != "160000":
        raise _GitCheckError(f"{team_path_rel} is not a submodule gitlink in HEAD")
    return parts[2]


def _remote_head(team_path: Path) -> str:
    out = _run_git(["-C", str(team_path), "ls-remote", "origin", "HEAD"])
    line = out.strip().splitlines()[0] if out.strip() else ""
    sha, _, _ref = line.partition("\t")
    if not sha:
        raise _GitCheckError(f"{team_path}: ls-remote origin HEAD returned nothing")
    return sha


def _pin_age_days(team_path: Path, pin_sha: str, now: float) -> int:
    out = _run_git(["-C", str(team_path), "log", "-1", "--format=%ct", pin_sha])
    ts = out.strip()
    if not ts:
        raise _GitCheckError(f"{team_path}: git log -1 --format=%ct {pin_sha} returned nothing")
    committed_at = int(ts)
    return int((now - committed_at) // 86400)


def run_check(repo_root: Path, now: float | None = None) -> dict:
    if now is None:
        now = time.time()

    indirection = load_indirection(repo_root)
    teams_root_rel = indirection["teams_root"]
    stale_after_days = indirection["stale_after_days"]

    teams_md_path = repo_root / "context" / "department" / "teams.md"
    if not teams_md_path.is_file():
        raise CascadeConfigError(f"missing {teams_md_path}")
    registry = parse_registry(teams_md_path.read_text())

    quarter_doc = find_quarter_doc(repo_root)
    quarter = quarter_doc.stem.removeprefix("okrs-")
    okr_ids = parse_okr_ids(quarter_doc.read_text())
    objective_ids = {i for i in okr_ids if re.fullmatch(r"O\d+", i)}

    origin_url = _origin_url(repo_root)

    findings: list[dict] = []
    drift: list[dict] = []
    pin_age_days: dict[str, int] = {}
    served_objectives: set[str] = set()

    for row in registry:
        team = row["team"]
        team_path_rel = row["path"]
        team_path = repo_root / team_path_rel

        if not _is_git_checkout(team_path):
            findings.append({
                "class": "registered-missing",
                "team": team,
                "detail": f"{team_path_rel} is missing or not a git checkout",
            })
            continue

        # Resolve all git-derived state up front. ANY failure here means the
        # submodule isn't verifiably checked out — one cause, one finding —
        # so it short-circuits before any content (backlink/Serves) check
        # runs and could otherwise sit alongside a "not checked out" claim.
        try:
            pin_sha = _pin_sha(repo_root, team_path_rel)
            remote_head = _remote_head(team_path)
            age_days = _pin_age_days(team_path, pin_sha, now)
        except _GitCheckError as e:
            findings.append({"class": "registered-missing", "team": team, "detail": str(e)})
            continue

        backlink_path = team_path / "context" / "company" / "department.md"
        if not backlink_path.is_file():
            findings.append({
                "class": "backlink-missing",
                "team": team,
                "detail": f"{team_path_rel}/context/company/department.md not found",
            })
        else:
            backlink_fields = _frontmatter(backlink_path.read_text())
            parent = backlink_fields.get("parent", "")
            if _normalize_url(parent) != _normalize_url(origin_url):
                findings.append({
                    "class": "backlink-mismatch",
                    "team": team,
                    "detail": f"parent={parent!r} does not match origin={origin_url!r}",
                })

        quarterly_dir = team_path / "context" / "quarterly"
        quarterly_files = (
            sorted((p for p in quarterly_dir.glob("*.md") if p.name != "README.md"), key=lambda p: p.name)
            if quarterly_dir.is_dir() else []
        )
        serves_pairs = []
        for f in quarterly_files:
            for served_id in parse_serves_headers(f.read_text()):
                serves_pairs.append((served_id, f))

        if not serves_pairs:
            findings.append({
                "class": "serves-nothing",
                "team": team,
                "detail": f"no Serves: headers found under {team_path_rel}/context/quarterly/*.md",
            })
        else:
            for served_id, f in serves_pairs:
                if served_id not in okr_ids:
                    findings.append({
                        "class": "serves-unknown",
                        "team": team,
                        "detail": f"{served_id} in {f.relative_to(repo_root)}",
                    })
                else:
                    served_objectives.add(served_id.split(".")[0])

        pin_age_days[team] = age_days
        if age_days > stale_after_days:
            findings.append({
                "class": "pin-stale",
                "team": team,
                "detail": f"pin age {age_days}d exceeds stale_after_days={stale_after_days}",
            })

        if remote_head != pin_sha:
            drift.append({"team": team, "pinned": pin_sha, "remote": remote_head})

    for objective_id in sorted(objective_ids):
        if objective_id not in served_objectives:
            findings.append({"class": "orphaned-objective", "team": None, "detail": objective_id})

    registered_paths = {row["path"] for row in registry}
    teams_root_path = repo_root / teams_root_rel
    if teams_root_path.is_dir():
        for entry in sorted(teams_root_path.iterdir(), key=lambda p: p.name):
            if not entry.is_dir():
                continue
            rel = f"{teams_root_rel.rstrip('/')}/{entry.name}"
            if rel not in registered_paths:
                findings.append({
                    "class": "unregistered-present",
                    "team": entry.name,
                    "detail": rel,
                })

    return {
        "quarter": quarter,
        "findings": findings,
        "drift": drift,
        "pin_age_days": pin_age_days,
    }


def _format_table(findings: list[dict]) -> str:
    return "\n".join(f"{f['class']}\t{f['team'] or '-'}\t{f['detail']}" for f in findings)


def main(argv: list[str]) -> int:
    json_output = False
    root = None
    args = list(argv)
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--json":
            json_output = True
        elif arg == "--root":
            i += 1
            if i >= len(args):
                print("error: --root requires a path", file=sys.stderr)
                return 2
            root = Path(args[i])
        else:
            print(f"error: unrecognized argument: {arg}", file=sys.stderr)
            return 2
        i += 1

    repo_root = root if root is not None else Path.cwd()

    try:
        result = run_check(repo_root)
    except CascadeConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if json_output:
        print(json.dumps(result))
    else:
        table = _format_table(result["findings"])
        if table:
            print(table)

    return 1 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
