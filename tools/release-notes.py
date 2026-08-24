#!/usr/bin/env python3
"""Release notes from merged PR titles, and the CHANGELOG they live in.

One line per merged PR, grouped by area, scikit-learn style. `main` is PR-only
under branch protection, so every change lands as one squash commit carrying
`(#N)`: the PR is the unit, not the commit. Generating per-commit would emit
paragraph-length WIP subjects next to real entries (AWO-156).

The record lives in git. The PR that bumps `.claude-plugin/plugin.json` runs
`--changelog CHANGELOG.md` to add its section — drafted from the PRs merged
since the previous release, trimmed in review — and the release workflow
extracts that section as the GitHub release body when the bump lands on main
(AWO-261). Nothing is generated at release time, so the notes a reader sees on
GitHub are the notes reviewed in the PR.

Range base: the previous release — the highest v* tag below the version being
generated. "Highest tag" alone made v0.9.2's notes empty: run on the tag it
was releasing, the range was v0.9.2..v0.9.2.

What is exact and what is a draft:

- Exact: the commit range, the PR numbers in it, their titles and merge dates.
- Draft: the change-type tag and the wording. Raw PR titles are not publishable
  as-is (`PR2: Trim the shipped command surface + board fallback`). The tag is a
  keyword guess, and every line is meant to be trimmed before the PR merges.

Uses `gh` for PR titles when available, falling back to the squash-commit
subject. It never writes to a remote.

Usage:
  tools/release-notes.py                                   # draft since the previous release, to stdout
  tools/release-notes.py --changelog CHANGELOG.md          # add or replace the canonical version's section
  tools/release-notes.py --version v0.10.0 --extract-from CHANGELOG.md --out RELEASE_NOTES.md
  tools/release-notes.py --verify CHANGELOG.md             # exit 1 unless the canonical version has a section
  tools/release-notes.py --since v0.4.0 --head v0.9.2 --version v0.9.2 --changelog CHANGELOG.md
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

# Keyword guess only. The author is expected to correct these in the PR.
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


def semver(tag: str) -> list[int]:
    return [int(p) for p in tag[1:].split(".")]


def release_tags() -> list[str]:
    """v<major>.<minor>.<patch> tags, oldest first."""
    tags = [t for t in run("git", "tag").splitlines() if RELEASE_TAG.match(t)]
    return sorted(tags, key=semver)


def base_tag(version: str) -> str:
    """The previous release: the highest release tag below `version`. Keyed on
    the version, not on HEAD, so it is right both on the release tag itself
    (the release workflow's situation — v0.9.2's notes came out empty because
    the base was the highest tag, i.e. v0.9.2) and when the next release is
    drafted from a HEAD that still sits on the last tag (nothing since)."""
    below = semver(version) if RELEASE_TAG.match(version) else None
    candidates = []
    for tag in release_tags():
        if tag == version:
            continue
        if below is not None and semver(tag) >= below:
            continue
        candidates.append(tag)
    if not candidates:
        raise RuntimeError(
            f"no release tag before {version} to start the range from — pass "
            "--since explicitly for the first release"
        )
    return candidates[-1]


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


def build(version: str, since: str, entries: list[tuple[int, str]], draft: bool) -> str:
    """The section for `version`. `draft` adds the markers a stdout draft
    carries — the range comment and the per-line type hints; a section written
    into the committed CHANGELOG carries neither, since the PR review is where
    the trimming happens."""
    grouped: dict[str, list[str]] = {}
    for number, title in entries:
        section = classify(title, SECTIONS, FALLBACK_SECTION)
        tag = classify(title, TAGS, FALLBACK_TAG)
        awo = AWO_REF.search(title)
        hint = f"  <!-- {awo.group(0)}: check type: label -->" if draft and awo else ""
        grouped.setdefault(section, []).append(
            f"- **{tag}** {title}. (#{number}){hint}"
        )

    order = [name for name, _ in SECTIONS] + [FALLBACK_SECTION]
    lines = [f"## {version}", ""]
    if draft:
        lines += [
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


# ---------- CHANGELOG.md ----------

SECTION_HEADING = re.compile(r"^## (\S+)", re.M)


def section_span(text: str, version: str) -> tuple[int, int] | None:
    """(start, end) of `version`'s section: its heading line through the line
    before the next `## ` heading, or the end of the file."""
    for match in SECTION_HEADING.finditer(text):
        if match.group(1) != version:
            continue
        nxt = SECTION_HEADING.search(text, match.end())
        return match.start(), (nxt.start() if nxt else len(text))
    return None


def upsert_section(path: Path, version: str, section: str) -> str:
    """Replace `version`'s section, or insert it above the first section so the
    file stays newest-first. The intro above the first heading is kept.
    Returns 'replaced' or 'added'."""
    text = path.read_text() if path.exists() else "# Changelog\n\n"
    block = section.rstrip("\n") + "\n\n"
    span = section_span(text, version)
    if span:
        start, end = span
        path.write_text(text[:start] + block + text[end:].lstrip("\n"))
        return "replaced"
    first = SECTION_HEADING.search(text)
    if first:
        path.write_text(text[:first.start()].rstrip("\n") + "\n\n" + block + text[first.start():])
    else:
        path.write_text(text.rstrip("\n") + "\n\n" + block)
    return "added"


def extract_section(path: Path, version: str) -> str:
    """The section body — everything below the `## <version>` heading — as the
    release publishes it. Missing or empty is an error, never an empty body: a
    release with no notes is what this file exists to prevent."""
    if not path.exists():
        raise RuntimeError(f"{path} does not exist")
    text = path.read_text()
    span = section_span(text, version)
    if not span:
        raise RuntimeError(
            f"{path} has no '## {version}' section. Add it in the PR that bumps "
            f"the version: python tools/release-notes.py --changelog {path.name}"
        )
    start, end = span
    heading_end = text.index("\n", start) + 1 if "\n" in text[start:end] else end
    body = text[heading_end:end].strip("\n")
    if not body.strip():
        raise RuntimeError(f"{path}: the '## {version}' section is empty")
    return body + "\n"


def canonical_version() -> str:
    return "v" + json.loads(
        (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text()
    )["version"]


def main() -> int:
    global REPO_ROOT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help="repository to read (default: this one)")
    parser.add_argument("--since", help="base tag (default: the previous release tag)")
    parser.add_argument("--head", default="HEAD", help="range end (default: HEAD)")
    parser.add_argument("--version", help="section to stamp (default: the canonical plugin version)")
    parser.add_argument("--out", type=Path, help="write here instead of stdout")
    parser.add_argument("--changelog", type=Path, help="add or replace the version's section in this file")
    parser.add_argument("--extract-from", type=Path, metavar="CHANGELOG",
                        help="write the version's section body from this file; no generation")
    parser.add_argument("--verify", type=Path, metavar="CHANGELOG",
                        help="exit 1 unless the version has a non-empty section in this file")
    args = parser.parse_args()
    REPO_ROOT = args.repo.resolve()

    version = args.version or canonical_version()

    if args.verify:
        try:
            extract_section(args.verify, version)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"{args.verify}: section {version} present.")
        return 0

    if args.extract_from:
        try:
            body = extract_section(args.extract_from, version)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if args.out:
            args.out.write_text(body)
            print(f"wrote {args.out}: the {version} section of {args.extract_from}")
        else:
            print(body, end="")
        return 0

    since = args.since or base_tag(version)
    entries, skipped = merged_prs(since, args.head)
    titles = pr_titles([n for n, _ in entries])
    entries = [(n, titles.get(n, subject)) for n, subject in entries]

    if args.changelog:
        verb = upsert_section(args.changelog, version, build(version, since, entries, draft=False))
        print(f"{verb} section {version} in {args.changelog}: {len(entries)} PR(s) since {since}")
    else:
        notes = build(version, since, entries, draft=True)
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
