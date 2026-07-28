"""Regression test for the command frontmatter contract in tools/gather.py.

parse_frontmatter is line-based, so `description: >-` stores the literal
string '>-' — and every pointer stub, plugin picker entry, and agent-skill
trigger built from that field silently becomes ">-" while `gather.py --check`
stays green. At 30-45 words an implementer reaches for a block scalar by
reflex. Descriptions are single-line and double-quoted (design spec 4.5), and
the parser rejects block scalars rather than storing them.

Later tasks in this PR extend this module with the description and autofire
contracts: the block-scalar rejection, the sixteen descriptions, and autofire.

Pure stdlib; no pytest, no network.

Run:  python3 tests/command-frontmatter/test_frontmatter.py
"""
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

FAILURES = []

# Every YAML block-scalar shape: folded and literal, each with an optional
# indentation indicator and an optional chomping indicator.
BLOCK_SCALARS = [">", ">-", ">+", "|", "|-", "|+", ">2", "|2-", ">4+"]

# The sixteen shipped commands (design spec 7). awowify's source is the
# top-level commands/ dir; the other fifteen live under .agents/commands/.
SHIPPED = [
    "artifact", "awowify", "coaching-review", "daily-checkin", "daily-digest",
    "design-system", "kb-mine", "kb-synthesize", "my-work", "process-retro",
    "process-transcript", "process-workitem", "project-plan",
    "refinement-prep", "setup-awow", "solution-design-flow",
]


# The autofire set (design spec 4.5 Layer 3). The rule, not the list: a command
# autofires unless a misfire is damage (consequential and hard to reverse) or
# noise (trigger too broad). Excluded on those grounds: my-work, daily-digest,
# kb-mine (too broad); setup-awow, awowify, design-system, kb-synthesize
# (consequential).
AUTOFIRE = [
    "artifact", "coaching-review", "daily-checkin", "process-retro",
    "process-transcript", "process-workitem", "project-plan",
    "refinement-prep", "solution-design-flow", "update-context",
]

# update-context ships in PR 5. Selecting by frontmatter rather than a
# hardcoded list is exactly what lets it be absent without a special case.
DEFERRED = {"update-context"}


def source_for(name: str) -> Path:
    """The authoring file for a command. awowify is the one exception."""
    if name == "awowify":
        return REPO_ROOT / "commands" / f"{name}.md"
    return REPO_ROOT / ".agents" / "commands" / f"{name}.md"


def main() -> int:
    for indicator in BLOCK_SCALARS:
        doc = f"---\ndescription: {indicator}\n  folded text here\n---\n\n# Title\n"
        try:
            fields, _ = gather.parse_frontmatter(doc)
        except ValueError:
            continue
        FAILURES.append(
            f"parse_frontmatter accepted block scalar {indicator!r} and stored "
            f"description={fields.get('description')!r}"
        )

    # A single-line double-quoted description must still parse, unchanged.
    doc = '---\ndescription: "Use when the user asks for X."\nphase: seed\n---\n\n# Title\n'
    fields, body = gather.parse_frontmatter(doc)
    if fields.get("description") != "Use when the user asks for X.":
        FAILURES.append(
            f"single-line description mangled: {fields.get('description')!r}"
        )
    if fields.get("phase") != "seed":
        FAILURES.append(f"sibling field lost: {fields!r}")
    if body != "\n# Title\n":
        FAILURES.append(f"body mangled: {body!r}")

    # A bare `key:` introducing a list is not a block scalar and must survive
    # as the existing skip, not as a raise — every command uses this shape.
    doc = '---\nprerequisites:\n  - "Step 0 of /setup-awow complete"\n---\n\n# Title\n'
    try:
        fields, _ = gather.parse_frontmatter(doc)
        if "prerequisites" in fields:
            FAILURES.append(f"list key leaked into fields: {fields!r}")
    except ValueError as exc:
        FAILURES.append(f"list key wrongly rejected as a block scalar: {exc}")

    # The error must name the file, or a build failure sends the implementer
    # grepping 25 command files for a character they cannot see.
    doc = "---\ndescription: >-\n  folded\n---\n\n# Title\n"
    try:
        gather.parse_frontmatter(doc, REPO_ROOT / ".agents" / "commands" / "artifact.md")
    except ValueError as exc:
        if ".agents/commands/artifact.md" not in str(exc):
            FAILURES.append(f"error does not name the source file: {exc}")
    else:
        FAILURES.append("parse_frontmatter did not raise on a block scalar")

    # Every shipped command carries an explicit, single-line, situation-shaped
    # description. Without one, command_description falls back to the H1 — a
    # label ("gated pipeline for meeting transcripts"), not a trigger — and the
    # fallback is invisible in the built output.
    for name in SHIPPED:
        path = source_for(name)
        if not path.is_file():
            FAILURES.append(f"shipped command missing: {path.relative_to(REPO_ROOT)}")
            continue
        fields, _ = gather.parse_frontmatter(path.read_text(), path)
        desc = fields.get("description")
        if not desc:
            FAILURES.append(
                f"{name}: no explicit `description:` — gather would fall back "
                f"to the H1 label"
            )
            continue
        if '"' in desc or "\\" in desc:
            FAILURES.append(
                f"{name}: description contains a double quote or backslash. The "
                f"generated stubs wrap it in double quotes and parse_frontmatter "
                f"does not unescape, so it will not round-trip: {desc!r}"
            )
        if not desc.startswith("Use when"):
            FAILURES.append(
                f"{name}: a description names the situation the user is in — "
                f"start it “Use when”: {desc!r}"
            )
        if len(desc.split()) < 20:
            FAILURES.append(
                f"{name}: description is {len(desc.split())} words; a trigger "
                f"needs the concrete phrasings and artefacts that fire it "
                f"(target 30-45): {desc!r}"
            )

    # autofire is exactly the elected set — no drift in either direction.
    seen = set()
    for root in (REPO_ROOT / ".agents" / "commands", REPO_ROOT / "commands"):
        for path in sorted(root.glob("*.md")):
            if path.name in gather.SKIP_FILENAMES:
                continue
            if gather.is_autofire(path.read_text()):
                seen.add(path.stem)

    absent = {n for n in AUTOFIRE if not source_for(n).is_file()}
    if absent - DEFERRED:
        FAILURES.append(
            f"autofire names a command with no source file: {sorted(absent - DEFERRED)}"
        )
    want = {n for n in AUTOFIRE if n not in absent}
    for missing in sorted(want - seen):
        FAILURES.append(f"{missing}: elected for autofire but carries no `autofire: true`")
    for extra in sorted(seen - want):
        FAILURES.append(f"{extra}: carries `autofire: true` but is not in the elected set")

    # Each elected command is mirrored into dist/skills/, and nothing else is.
    # Without the mirror, autofire buys a better picker on Claude Code and
    # nothing more — the model cannot elect a slash command.
    for name in sorted(want):
        if not (gather.DIST_DIR / "skills" / name / "SKILL.md").is_file():
            FAILURES.append(f"{name}: autofire but no dist/skills/{name}/SKILL.md")
    for name in sorted(set(SHIPPED) - set(AUTOFIRE)):
        if (gather.DIST_DIR / "skills" / name / "SKILL.md").is_file():
            FAILURES.append(
                f"{name}: not elected for autofire but mirrored at "
                f"dist/skills/{name}/SKILL.md"
            )

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Command frontmatter contract OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
