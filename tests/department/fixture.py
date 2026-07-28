"""Hermetic git-repo fixtures for cascade_check tests.

Builds throwaway git repos on disk (team repos + a department repo wired to
them as submodules) so tests exercise cascade_check.run_check against real
git plumbing — submodule gitlinks, remotes, pin history — rather than mocks.
Extracted from tests/department/test_cascade_check.py (Task 2's inline
helpers) and generalized only as far as later seeds need:
`quarterly_extra` lets a team's focus doc carry extra freeform content
after its Serves: block, and `stale_after_days` lets a department be built
with a non-default staleness threshold.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _git(cwd, *args, env=None):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, env=env)


def make_team(base: Path, name: str, serves: list[str], *, quarterly_extra: str | None = None) -> Path:
    """Create a standalone, committed team repo with one quarterly focus doc.

    `serves` becomes the leading `Serves: <id>` header lines in
    context/quarterly/focus.md. `quarterly_extra`, if given, is appended
    verbatim after the doc's `# Focus` heading.
    """
    repo = base / name
    (repo / "context" / "quarterly").mkdir(parents=True)
    (repo / "context" / "company").mkdir(parents=True)
    lines = "".join(f"Serves: {s}\n" for s in serves)
    body = lines + "\n# Focus\n"
    if quarterly_extra:
        body += quarterly_extra
    (repo / "context" / "quarterly" / "focus.md").write_text(body)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return repo


def make_department(base: Path, teams: list[Path], *, stale_after_days: int = 28) -> Path:
    """Create a department repo with the given teams wired in as submodules.

    Writes the context/tooling/department.md indirection (with
    `stale_after_days`), the teams.md registry, an okrs-2026-Q3.md doc with
    O1/O2 (one KR each), adds each team as a submodule under teams/<name>,
    and writes a matching backlink into each submodule checkout. The
    dept's own `origin` remote is set to its own path so a fresh backlink
    `parent:` matches out of the box.
    """
    dept = base / "dept"
    (dept / "context" / "department").mkdir(parents=True)
    (dept / "context" / "tooling").mkdir(parents=True)
    (dept / "context" / "tooling" / "department.md").write_text(
        "---\nteams_root: teams\nread_scope: context/team, context/quarterly, context/company\n"
        f"decisions_dir: context/department/decisions\nstale_after_days: {stale_after_days}\n---\n")
    rows = "\n".join(f"| {t.name} | teams/{t.name} | Lead |" for t in teams)
    (dept / "context" / "department" / "teams.md").write_text(
        "| Team | Path | Lead |\n|---|---|---|\n" + rows + "\n")
    (dept / "context" / "department" / "okrs-2026-Q3.md").write_text(
        "## O1 — Alpha\n- O1.KR1: x\n## O2 — Beta\n- O2.KR1: y\n")
    subprocess.run(["git", "init", "-q", str(dept)], check=True)
    # The dept's own origin must match what the backlink `parent:` claims, or
    # every team would fail backlink-mismatch even on an otherwise-clean setup.
    # Compute it once and reuse it for both the remote and the backlinks.
    origin_url = f"file://{dept}"
    _git(dept, "remote", "add", "origin", origin_url)
    for t in teams:
        _git(dept, "-c", "protocol.file.allow=always", "submodule", "add", "-q", f"file://{t}", f"teams/{t.name}")
        backlink = dept / "teams" / t.name / "context" / "company" / "department.md"
        backlink.parent.mkdir(parents=True, exist_ok=True)
        backlink.write_text(f"---\ndepartment: Dept\nparent: {origin_url}\n---\n")
    _git(dept, "add", "-A")
    _git(dept, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    return dept
