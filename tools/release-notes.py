#!/usr/bin/env python3
"""Draft release notes for the commit range since the last release tag.

One line per merged PR, grouped by area, scikit-learn style. `main` is PR-only
under branch protection, so every change lands as one squash commit carrying
`(#N)`: the PR is the unit, not the commit. Generating per-commit would emit
paragraph-length WIP subjects next to real entries (AWO-156).

What is exact and what is a draft:

- Exact: the commit range, the PR numbers in it, their titles and merge dates.
- Draft: the change-type tag and the wording. Raw PR titles are not publishable
  as-is (`PR2: Trim the shipped command surface + board fallback`). The tag is a
  keyword guess, and every line is meant to be trimmed before publishing.

Uses `gh` for PR titles when available, falling back to the squash-commit
subject. It never writes to a remote.

Usage:
  tools/release-notes.py                    # since the latest v* tag, to stdout
  tools/release-notes.py --since v0.4.0
  tools/release-notes.py --version v0.9.0   # heading to stamp
  tools/release-notes.py --out NOTES.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")
# Two shapes reach main. Squash merges (current, enforced by branch protection)
# carry a trailing "(#N)". Merge commits predate it and carry the number in the
# subject; their subject is not a usable title, so gh supplies it.
PR_SQUASH = re.compile(r"\(#(\d+)\)\s*$")
PR_MERGE = re.compile(r"^Merge pull request #(\d+) from ")
AWO_REF = re.compile(r"\bAWO-(\d+)\b")

# Ordered: an entry lands in the first section whose pattern it matches, so the
# more specific areas come first.
SECTIONS: tuple[tuple[str, re.Pattern], ...] = (
    ("Harnesses and distribution", re.compile(
        r"harness|opencode|codex|\bpi\b|copilot|m365|plugin|marketplace|payload|dist|package", re.I)),
    ("Commands", re.compile(
        r"command|/\w[\w-]+|skill|autofire|digest|refinement|transcript|workitem|okr|department", re.I)),
    ("Context and contracts", re.compile(
        r"context|token|convention|lockfile|knowledge|board|contract|frontmatter", re.I)),
    ("Build and CI", re.compile(r"\bci\b|test|lint|check|gather|build|hook|workflow", re.I)),
    ("Docs", re.compile(r"doc|readme|guide|spec|proposal", re.I)),
)
FALLBACK_SECTION = "Other"

# Keyword guess only. The release step is expected to correct these.
TAGS: tuple[tuple[str, re.Pattern], ...] = (
    ("API", re.compile(r"\bremove|\bdrop\b|\bdelete\b|rename|split|breaking|deprecat", re.I)),
    # \bfix(es|ed|ing)? and not \bfix — the bare prefix matches "fixtures".
    ("Fix", re.compile(r"\bfix(es|ed|ing)?\b|\bcorrect|\bbug\b|sanitiz|repair", re.I)),
    ("Feature", re.compile(r"\badd\b|\bsupport\b|\bimplement|\bintroduce|\bnew\b|land", re.I)),
)
FALLBACK_TAG = "Enhancement"


def run(*args: str) -> str:
    """Run a command in the repo, raising with full context on failure. No
    silent fallbacks: a broken git or gh invocation must surface, not degrade
    into empty notes that look like a quiet release."""
    result = subprocess.run(
        args, cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def latest_release_tag() -> str:
    tags = [t for t in run("git", "tag").splitlines() if RELEASE_TAG.match(t)]
    if not tags:
        raise RuntimeError(
            "no v<major>.<minor>.<patch> tag found — pass --since explicitly for "
            "the first release"
        )
    return sorted(tags, key=lambda t: [int(p) for p in t[1:].split(".")])[-1]


def merged_prs(since: str, head: str) -> tuple[list[tuple[int, str]], list[str]]:
    """((number, subject) newest first, subjects carrying no PR reference).

    The skipped list is returned rather than dropped: a commit in the range that
    reaches no PR is either pre-branch-protection WIP or a direct push, and the
    caller reports the count so a release can never silently omit work."""
    found: list[tuple[int, str]] = []
    skipped: list[str] = []
    # --first-parent: one entry per merge or squash. Without it a merge commit's
    # constituent commits are counted again as unreferenced, inflating the
    # skipped report with work that is already in the notes.
    log = run("git", "log", "--first-parent", f"{since}..{head}", "--pretty=%s")
    for line in log.splitlines():
        squash = PR_SQUASH.search(line)
        if squash:
            found.append((int(squash.group(1)), PR_SQUASH.sub("", line).strip()))
            continue
        merge = PR_MERGE.match(line)
        if merge:
            # Subject is "Merge pull request #N from branch" — no usable title.
            # pr_titles() replaces it; the placeholder only shows if gh is down.
            found.append((int(merge.group(1)), f"(PR #{merge.group(1)}, title unavailable)"))
            continue
        skipped.append(line)
    return found, skipped


def pr_titles(numbers: list[int]) -> dict[int, str]:
    """Authoritative PR titles from gh. Returns {} when gh is unavailable or
    unauthenticated, and the caller falls back to the commit subject — which is
    the same text for a squash merge, so the fallback loses nothing but the
    guarantee."""
    if not numbers:
        return {}
    try:
        raw = run(
            "gh", "pr", "list", "--state", "merged", "--limit", "200",
            "--json", "number,title",
        )
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"note: gh unavailable, using commit subjects ({exc})", file=sys.stderr)
        return {}
    return {p["number"]: p["title"] for p in json.loads(raw)}


def classify(text: str, table, fallback: str) -> str:
    for name, pattern in table:
        if pattern.search(text):
            return name
    return fallback


def build(version: str, since: str, entries: list[tuple[int, str]]) -> str:
    grouped: dict[str, list[str]] = {}
    for number, title in entries:
        section = classify(title, SECTIONS, FALLBACK_SECTION)
        tag = classify(title, TAGS, FALLBACK_TAG)
        awo = AWO_REF.search(title)
        hint = f"  <!-- {awo.group(0)}: check type: label -->" if awo else ""
        grouped.setdefault(section, []).append(
            f"- **{tag}** {title}. (#{number}){hint}"
        )

    order = [name for name, _ in SECTIONS] + [FALLBACK_SECTION]
    lines = [
        f"## {version}",
        "",
        f"<!-- DRAFT generated by tools/release-notes.py from {since}..HEAD.",
        "     Tags are keyword guesses and titles are raw. Trim every line to one",
        "     terse sentence and correct the tags before publishing. -->",
        "",
    ]
    for section in order:
        if section not in grouped:
            continue
        lines.append(f"### {section}")
        lines.extend(grouped[section])
        lines.append("")
    if not grouped:
        lines.append("_No pull requests merged in this range._")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="base tag (default: latest v* tag)")
    parser.add_argument("--head", default="HEAD", help="range end (default: HEAD)")
    parser.add_argument("--version", help="heading to stamp (default: the local plugin version)")
    parser.add_argument("--out", type=Path, help="write here instead of stdout")
    args = parser.parse_args()

    since = args.since or latest_release_tag()
    version = args.version or "v" + json.loads(
        (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text()
    )["version"]

    entries, skipped = merged_prs(since, args.head)
    titles = pr_titles([n for n, _ in entries])
    entries = [(n, titles.get(n, subject)) for n, subject in entries]

    notes = build(version, since, entries)
    if args.out:
        args.out.write_text(notes)
        print(f"wrote {args.out}: {len(entries)} PR(s) since {since}")
    else:
        print(notes)

    # Never a silent omission: say what the range held that reached no PR.
    if skipped:
        print(
            f"\nnote: {len(skipped)} commit(s) in {since}..{args.head} carry no PR "
            "reference and are not in the notes. Review them before publishing:",
            file=sys.stderr,
        )
        for subject in skipped[:10]:
            print(f"  - {subject[:100]}", file=sys.stderr)
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
