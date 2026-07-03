"""Statically validate the eval suites under tests/ — no LLM, no credentials.

Checks, per suite (a directory tests/<suite>/ containing suite.md):
  - suite.md frontmatter names a `command:` that resolves to .agents/commands/<command>.md
  - every scenario (scripts/*.txt ∩ rubrics/*.md) has a fixtures/<name>/ dir and a checks/<name>.sh
  - scripts without a rubric (and vice versa) are reported — a one-sided scenario never runs
  - checks/<name>.sh is NOT executable (it is sourced), passes `bash -n`, and defines pre() and post()
  - rubrics contain at least one numbered question; `(invariant N)` tags are positive integers

Shared machinery:
  - tests/run-checks.sh exists, IS executable, passes `bash -n`
  - tests/checks-prelude.sh exists, is NOT executable, passes `bash -n`

The exec-bit asymmetry is load-bearing: the driver is spawned, everything else
is sourced. Reports findings; does not fix. Exit 1 if anything is wrong, so CI
can gate on it without ever launching an agent.

Usage:
    python tools/validate-evals.py
    python tools/validate-evals.py --json   # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
COMMANDS_DIR = REPO_ROOT / ".agents" / "commands"

INVARIANT_TAG = re.compile(r"\(invariant\s+([^)]*)\)")
QUESTION_LINE = re.compile(r"^\d+\.\s+\S", re.MULTILINE)
FRONTMATTER_COMMAND = re.compile(r"^command:\s*(\S+)\s*$", re.MULTILINE)
PHASE_FUNC = {phase: re.compile(rf"^\s*{phase}\(\)\s*{{", re.MULTILINE) for phase in ("pre", "post")}


def bash_syntax_ok(path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["bash", "-n", str(path)], capture_output=True, text=True, check=False
    )
    return result.returncode == 0, result.stderr.strip()


def is_executable(path: Path) -> bool:
    return os.access(path, os.X_OK)


def frontmatter_command(suite_md: Path) -> str | None:
    text = suite_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    match = FRONTMATTER_COMMAND.search(text[3:end])
    return match.group(1) if match else None


def check_shared_machinery(findings: list[str]) -> None:
    driver = TESTS_DIR / "run-checks.sh"
    prelude = TESTS_DIR / "checks-prelude.sh"
    if not driver.is_file():
        findings.append(f"missing shared driver: {driver.relative_to(REPO_ROOT)}")
    else:
        if not is_executable(driver):
            findings.append("tests/run-checks.sh must be executable (it is spawned)")
        ok, err = bash_syntax_ok(driver)
        if not ok:
            findings.append(f"tests/run-checks.sh fails bash -n: {err}")
    if not prelude.is_file():
        findings.append(f"missing prelude: {prelude.relative_to(REPO_ROOT)}")
    else:
        if is_executable(prelude):
            findings.append("tests/checks-prelude.sh must NOT be executable (it is sourced)")
        ok, err = bash_syntax_ok(prelude)
        if not ok:
            findings.append(f"tests/checks-prelude.sh fails bash -n: {err}")


def check_checks_file(suite: str, name: str, findings: list[str]) -> None:
    checks = TESTS_DIR / suite / "checks" / f"{name}.sh"
    rel = checks.relative_to(REPO_ROOT)
    if not checks.is_file():
        findings.append(f"{suite}/{name}: missing checks file {rel}")
        return
    if is_executable(checks):
        findings.append(f"{rel} must NOT be executable (it is sourced)")
    ok, err = bash_syntax_ok(checks)
    if not ok:
        findings.append(f"{rel} fails bash -n: {err}")
    text = checks.read_text(encoding="utf-8")
    for phase, pattern in PHASE_FUNC.items():
        if not pattern.search(text):
            findings.append(f"{rel} defines no {phase}()")


def check_rubric(suite: str, name: str, findings: list[str]) -> None:
    rubric = TESTS_DIR / suite / "rubrics" / f"{name}.md"
    rel = rubric.relative_to(REPO_ROOT)
    text = rubric.read_text(encoding="utf-8")
    if not QUESTION_LINE.search(text):
        findings.append(f"{rel} contains no numbered rubric question")
    for tag in INVARIANT_TAG.findall(text):
        if not tag.strip().isdigit() or int(tag) < 1:
            findings.append(f"{rel} has malformed invariant tag: (invariant {tag})")


def check_suite(suite_md: Path, findings: list[str]) -> int:
    suite_dir = suite_md.parent
    suite = suite_dir.name

    command = frontmatter_command(suite_md)
    if command is None:
        findings.append(f"{suite}/suite.md has no `command:` in its frontmatter")
    elif not (COMMANDS_DIR / f"{command}.md").is_file():
        findings.append(
            f"{suite}/suite.md names command `{command}` but .agents/commands/{command}.md does not exist"
        )

    scripts = {p.stem for p in (suite_dir / "scripts").glob("*.txt")}
    rubrics = {p.stem for p in (suite_dir / "rubrics").glob("*.md")}
    for orphan in sorted(scripts - rubrics):
        findings.append(f"{suite}: script `{orphan}` has no rubric — scenario will never run")
    for orphan in sorted(rubrics - scripts):
        findings.append(f"{suite}: rubric `{orphan}` has no script — scenario will never run")

    scenarios = sorted(scripts & rubrics)
    if not scenarios:
        findings.append(f"{suite}: no runnable scenarios (scripts ∩ rubrics is empty)")
    for name in scenarios:
        if not (suite_dir / "fixtures" / name).is_dir():
            findings.append(f"{suite}/{name}: missing fixture dir fixtures/{name}/")
        check_checks_file(suite, name, findings)
        check_rubric(suite, name, findings)
    return len(scenarios)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    findings: list[str] = []
    check_shared_machinery(findings)

    suite_files = sorted(TESTS_DIR.glob("*/suite.md"))
    if not suite_files:
        findings.append("no suites found (no tests/*/suite.md)")

    scenario_count = 0
    for suite_md in suite_files:
        scenario_count += check_suite(suite_md, findings)

    if args.json:
        print(
            json.dumps(
                {
                    "suites": [p.parent.name for p in suite_files],
                    "scenarios": scenario_count,
                    "findings": findings,
                    "ok": not findings,
                },
                indent=2,
            )
        )
    else:
        for finding in findings:
            print(f"FINDING: {finding}")
        print(
            f"{'OK' if not findings else 'NOT OK'}: {len(suite_files)} suite(s), "
            f"{scenario_count} scenario(s), {len(findings)} finding(s)"
        )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
