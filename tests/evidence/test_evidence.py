"""tests/EVIDENCE.md stays true to the repo (CAU-1628).

The release bar's honesty rule: every command maps to its evidence, and what
is untested is named. A hand-written table rots the day someone adds a
command or a suite, so this test reads the repo and fails on drift. Asserts:

  1. Every command under .agents/commands/ and every skill under
     .agents/skills/ has a row — and no row names one that does not exist.
  2. Every eval suite under tests/ is cited, and a cited suite exists with the
     scenario count the table states.
  3. Every static test path the page cites exists.
  4. A `high` risk row has an eval suite or a named gap; risk is one of
     high / low / —.
  5. Every gap id used in a table is defined in the gap list, and every
     defined gap is used.
  6. Every journey's scenario names exist in the suite it cites.

Pure stdlib; no pytest, no network.

Run:  python3 tests/evidence/test_evidence.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PAGE = REPO_ROOT / "tests" / "EVIDENCE.md"
AGENTS = REPO_ROOT / ".agents"
FAILURES: list[str] = []


def shipped_names() -> set[str]:
    names = {p.stem for p in (AGENTS / "commands").glob("*.md") if p.name != "README.md"}
    for p in (AGENTS / "skills").iterdir():
        if p.is_dir() and (p / "SKILL.md").is_file():
            names.add(p.name)
        elif p.suffix == ".md" and p.name != "README.md":
            names.add(p.stem)
    return names


def suites() -> dict[str, int]:
    """{suite: scenario count} for every tests/<suite>/suite.md."""
    return {
        s.parent.name: len(list((s.parent / "scripts").glob("*.txt")))
        for s in (REPO_ROOT / "tests").glob("*/suite.md")
    }


def rows(block: str, width: int) -> list[list[str]]:
    out = []
    for line in block.split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == width and not set(cells[0]) <= set("-: "):
            out.append(cells)
    return out[1:] if out else []


def main() -> int:
    text = PAGE.read_text()
    real, real_suites = shipped_names(), suites()

    inventory = text[text.index("## Every command and skill"): text.index("### Not built yet")]
    table = []
    for part in inventory.split("\n### ")[1:]:
        table += rows(part, 7)
    listed = {}
    for name, kind, risk, journey, suite, static, gap in table:
        listed[name.strip("`")] = (kind, risk, suite, gap)

    for name in sorted(real - set(listed)):
        FAILURES.append(f"{name} ships in .agents/ and has no row in tests/EVIDENCE.md")
    for name in sorted(set(listed) - real):
        FAILURES.append(f"tests/EVIDENCE.md has a row for {name}, which does not exist — move it to 'Not built yet'")

    cited = {}
    for name, (kind, risk, suite, gap) in listed.items():
        if risk not in ("high", "low", "—"):
            FAILURES.append(f"{name}: risk is {risk!r}, expected high, low or —")
        match = re.fullmatch(r"`tests/([\w-]+)/` \((\d+)\)", suite)
        if match:
            cited[match.group(1)] = int(match.group(2))
        elif suite != "none":
            FAILURES.append(f"{name}: eval suite cell {suite!r} is neither `tests/<suite>/` (N) nor none")
        if risk == "high" and not match and not re.search(r"\bG\d+\b", gap):
            FAILURES.append(f"{name} is high risk with no eval suite and no named gap")

    for suite, count in cited.items():
        if suite not in real_suites:
            FAILURES.append(f"the page cites tests/{suite}/, which is not an eval suite")
        elif real_suites[suite] != count:
            FAILURES.append(f"tests/{suite}/ has {real_suites[suite]} scenarios, the page says {count}")
    for suite in sorted(set(real_suites) - set(cited)):
        FAILURES.append(f"eval suite tests/{suite}/ is cited by no row")

    for path in sorted(set(re.findall(r"`(tests/[\w./-]+)`", text))):
        if not (REPO_ROOT / path).exists():
            FAILURES.append(f"the page cites {path}, which does not exist")

    journeys = rows(text[text.index("## The six journeys"): text.index("## Every command and skill")], 5)
    if len(journeys) != 6:
        FAILURES.append(f"the journey table has {len(journeys)} rows, expected 6")
    for number, journey, evidence, static, gaps in journeys:
        suite = None
        for token in re.findall(r"`([^`]+)`", evidence):
            found = re.fullmatch(r"tests/([\w-]+)/", token)
            if found:
                suite = found.group(1)
            elif suite and not token.endswith("*") and not (REPO_ROOT / "tests" / suite / "scripts" / f"{token}.txt").is_file():
                FAILURES.append(f"journey {number}: tests/{suite}/ has no scenario {token!r}")

    gap_list = text[text.index("## Gaps"): text.index("## Runs on record")]
    defined = set(re.findall(r"^- \*\*(G\d+) ", gap_list, flags=re.M))
    used = set(re.findall(r"\bG\d+\b", text[: text.index("## Gaps")]))
    for g in sorted(used - defined):
        FAILURES.append(f"{g} is used in a table and not defined in the gap list")
    for g in sorted(defined - used):
        FAILURES.append(f"{g} is defined in the gap list and used by no row")

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print(f"Evidence page OK — {len(listed)} commands and skills, {len(cited)} suites, {len(defined)} gaps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
