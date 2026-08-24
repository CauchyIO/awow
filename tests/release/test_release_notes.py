"""Regression tests for tools/release-notes.py against a real scratch git repo.

Three breaks, each of which produced or would produce a release with the
wrong record:

  1. Empty notes on the release itself (v0.9.2). The range base was "the
     highest v* tag", which is the tag being released when the generator runs
     on it, so the range was empty. The base must be the PREVIOUS release: a
     tag that is neither the version being generated nor at HEAD.
  2. A CHANGELOG section that is not idempotent — re-running the generator in
     the bump PR must replace the section, never duplicate it — and an extract
     that hands the release the wrong body.
  3. --verify passing for a version with no section, which would let a bump
     merge to main with nothing for the release to publish.

Pure stdlib; no pytest, no network (gh is expected to be absent or fail in the
scratch repo, and the generator falls back to commit subjects). Builds one
scratch repo with real commits and tags; removes it afterwards.

Run:  python3 tests/release/test_release_notes.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "release-notes.py"

FAILURES: list[str] = []


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True,
        env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
             "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(repo)},
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def notes(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
        cwd=REPO_ROOT,
    )


def squash(repo: Path, subject: str) -> None:
    """One squash-merge-shaped commit, the shape branch protection lands."""
    marker = repo / "log.txt"
    with marker.open("a") as f:
        f.write(subject + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", subject)


def build_scratch_repo(root: Path) -> Path:
    """v0.1.0 -> two merged PRs -> v0.2.0 at HEAD. Generating notes for
    v0.2.0 here reproduces the v0.9.2 situation exactly: the workflow runs on
    the tag it is releasing."""
    repo = root / "scratch"
    repo.mkdir()
    git(repo, "init", "-q")
    squash(repo, "Initial (#1)")
    git(repo, "tag", "v0.1.0")
    squash(repo, "AWO-1: Add the first feature (#2)")
    squash(repo, "AWO-2: Fix the second thing (#3)")
    git(repo, "tag", "v0.2.0")
    return repo


def check_range_base_is_previous_release(repo: Path) -> None:
    result = notes("--repo", str(repo), "--version", "v0.2.0")
    if result.returncode != 0:
        FAILURES.append(f"generator failed on the release tag: {result.stderr.strip()}")
        return
    out = result.stdout
    if "(#2)" not in out or "(#3)" not in out:
        FAILURES.append(
            "notes generated ON v0.2.0 do not list the PRs since v0.1.0 — the "
            f"range base is not the previous release. Output:\n{out}"
        )
    if "(#1)" in out:
        FAILURES.append("notes for v0.2.0 include PR #1, which shipped in v0.1.0")
    if "v0.1.0.." not in out:
        FAILURES.append(f"expected the range to start at v0.1.0; output:\n{out}")

    # The next release, drafted from the same HEAD, has nothing yet.
    nxt = notes("--repo", str(repo), "--version", "v0.3.0")
    if nxt.returncode != 0 or "No pull requests" not in nxt.stdout:
        FAILURES.append(
            "notes for a not-yet-cut v0.3.0 from HEAD=v0.2.0 should be empty "
            f"(base v0.2.0); got rc={nxt.returncode}:\n{nxt.stdout}{nxt.stderr}"
        )


def check_changelog_section_and_extract(repo: Path, changelog: Path) -> None:
    changelog.write_text("# Changelog\n\nIntro paragraph.\n\n## v0.1.0\n\n- Initial. (#1)\n")
    for _ in range(2):  # idempotent: the second run replaces, never duplicates
        result = notes("--repo", str(repo), "--version", "v0.2.0", "--changelog", str(changelog))
        if result.returncode != 0:
            FAILURES.append(f"--changelog failed: {result.stderr.strip()}")
            return
    text = changelog.read_text()
    if text.count("## v0.2.0") != 1:
        FAILURES.append(f"expected exactly one v0.2.0 section after two runs; got:\n{text}")
    if text.index("## v0.2.0") > text.index("## v0.1.0"):
        FAILURES.append("new section must be inserted above the previous release")
    if "Intro paragraph." not in text.split("## v0.2.0")[0]:
        FAILURES.append("the changelog intro above the first section was lost")
    if "<!--" in text:
        FAILURES.append("committed changelog sections must carry no draft HTML comments")

    out = changelog.parent / "RELEASE_NOTES.md"
    result = notes("--version", "v0.2.0", "--extract-from", str(changelog), "--out", str(out))
    if result.returncode != 0:
        FAILURES.append(f"--extract-from failed: {result.stderr.strip()}")
        return
    body = out.read_text()
    if "(#2)" not in body or "(#3)" not in body:
        FAILURES.append(f"extracted body is missing the section's entries:\n{body}")
    if "## v0.2.0" in body or "## v0.1.0" in body or "(#1)" in body:
        FAILURES.append(f"extracted body must be the v0.2.0 section only, without its heading:\n{body}")


def check_verify_gate(changelog: Path) -> None:
    ok = notes("--version", "v0.2.0", "--verify", str(changelog))
    if ok.returncode != 0:
        FAILURES.append(f"--verify rejected a present section: {ok.stdout}{ok.stderr}")
    missing = notes("--version", "v9.9.9", "--verify", str(changelog))
    if missing.returncode == 0:
        FAILURES.append("--verify passed for a version with no CHANGELOG section")


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="awow-release-notes-"))
    try:
        repo = build_scratch_repo(root)
        check_range_base_is_previous_release(repo)
        check_changelog_section_and_extract(repo, root / "CHANGELOG.md")
        check_verify_gate(root / "CHANGELOG.md")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Release notes generator OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
