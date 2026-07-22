"""Guard: no prompt may land an instruction diff in a generated file.

tools/gather.py generates .claude/CLAUDE.md and .github/copilot-instructions.md
from .agents/AGENTS.md on every build (plan_top_level, gather.py:333-341). A
command that tells the agent to write an instruction diff into one of those is
writing to a build artefact: the edit survives until the next
`python tools/gather.py` and is then silently destroyed. /process-retro did
exactly that from the day it shipped.

Three checks:

  A. Only allowlisted commands may name a generated instruction file at all.
     /setup-awow authors them, /design-system verifies its house-style rule
     survived the bootstrap, /update-context names them only to forbid writing
     them. Anything else is a write target and fails.
  B. Inside /update-context, every mention must sit on a line that also says
     "Never write". The prohibition is deliberately kept on one physical line in
     that file so this can stay a line check — do not reflow it.
  C. /process-retro must still target .agents/AGENTS.md. Deleting the
     loop-closing step is not a fix for writing it to the wrong place.

Pure stdlib; no pytest, no network.

Run:  python3 tests/context-writes/test_context_writes.py
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS = REPO_ROOT / ".agents" / "commands"

MIRRORS = ("CLAUDE.md", "copilot-instructions.md")

# filename -> why this command is allowed to name a generated instruction file
ALLOWED = {
    "setup-awow.md": "authors them via the CLAUDE.md / AGENTS.md bootstrap (Step 5)",
    "design-system.md": "checks that its house-style rule survived the bootstrap",
    "update-context.md": "names them only inside its Never-write prohibition",
}

FAILURES: list[str] = []


def check_mirror_mentions() -> None:
    for path in sorted(COMMANDS.rglob("*.md")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if not any(m in line for m in MIRRORS):
                continue
            if path.name not in ALLOWED:
                FAILURES.append(
                    f"{rel}:{n} names a generated instruction file. gather.py "
                    f"rewrites it on every build, so a diff landed there is lost. "
                    f"Target .agents/AGENTS.md or {{HUB}}/context/team/ instead.\n"
                    f"    {line.strip()}"
                )
            elif path.name == "update-context.md" and "Never write" not in line:
                FAILURES.append(
                    f"{rel}:{n} names a generated instruction file outside the "
                    f"prohibition. Keep every mention on the single-line "
                    f'"**Never write ...**" boundary.\n    {line.strip()}'
                )


def check_retro_still_closes_the_loop() -> None:
    retro = COMMANDS / "process-retro.md"
    if ".agents/AGENTS.md" not in retro.read_text():
        FAILURES.append(
            ".agents/commands/process-retro.md targets no instruction file at "
            "all. The fix retargets its diffs to .agents/AGENTS.md; removing the "
            "loop-closing step is not the fix."
        )


def check_update_context_frontmatter() -> None:
    """/update-context's frontmatter is load-bearing three ways: `autofire: true`
    selects it for the dist/skills/ mirror (PR 4), `phase: standardise` makes it
    opt-in via /awow-add, and `description:` is what the harness actually matches
    on. parse_frontmatter is line-based — a block scalar (`>-`) is stored as the
    literal string '>-' and every picker entry silently becomes that."""
    path = COMMANDS / "update-context.md"
    if not path.is_file():
        FAILURES.append(".agents/commands/update-context.md is missing.")
        return
    text = path.read_text()
    if not text.startswith("---\n"):
        FAILURES.append("update-context.md has no frontmatter block.")
        return
    end = text.find("\n---", 4)
    if end == -1:
        FAILURES.append("update-context.md frontmatter block is unterminated.")
        return
    fields = {}
    for line in text[4:end].splitlines():
        if not line or line.startswith((" ", "\t", "-", "#")):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()

    if fields.get("phase") != "standardise":
        FAILURES.append(
            f"update-context.md phase is {fields.get('phase')!r}, expected "
            f"'standardise' so it stays opt-in via /awow-add."
        )
    if fields.get("autofire") != "true":
        FAILURES.append(
            f"update-context.md autofire is {fields.get('autofire')!r}, expected "
            f"'true' — it is the tenth autofire command (design spec 4.5)."
        )
    desc = fields.get("description", "")
    if desc[:1] in (">", "|"):
        FAILURES.append(
            f"update-context.md description uses a block scalar ({desc[:2]!r}). "
            f"parse_frontmatter stores the literal indicator, not the text."
        )
    elif not (len(desc) > 2 and desc.startswith('"') and desc.endswith('"')):
        FAILURES.append(
            f"update-context.md description must be a single-line, "
            f"double-quoted string; got {desc!r}."
        )


def main() -> int:
    check_mirror_mentions()
    check_update_context_frontmatter()
    check_retro_still_closes_the_loop()

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Instruction-file write targets OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
