#!/usr/bin/env python3
"""Static suite validation — no LLM, no credentials, no submission (night
eval content spec §7). Runs in CI before submit so a malformed suite costs
zero tokens. Checks: scenario asset completeness, rubric question lines in
the judge's '- ' convention, bash -n on any checks.sh. T2 trigger-corpus
validation lands with the T2 runner (needs YAML)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    scenarios_dir = root / "scenarios"
    scenarios = sorted(p for p in scenarios_dir.iterdir() if p.is_dir()) \
        if scenarios_dir.is_dir() else []
    if not scenarios:
        errors.append("no scenario directories under evals/scenarios/")
    for s in scenarios:
        for req in ("persona.md", "opening.md", "observe-writes.txt"):
            if not (s / req).is_file():
                errors.append(f"{s.name}: missing {req}")
        if not (s / "fixture").is_dir():
            errors.append(f"{s.name}: missing fixture/")
        rubric = root / "rubrics" / f"{s.name}.md"
        if not rubric.is_file():
            errors.append(f"{s.name}: missing rubric evals/rubrics/{s.name}.md")
        elif not [l for l in rubric.read_text().splitlines()
                  if l.startswith("- ")]:
            errors.append(f"{s.name}: rubric has no '- ' question lines "
                          f"(the judge's parse_rubric convention)")
        checks = s / "checks.sh"
        if checks.is_file():
            proc = subprocess.run(["bash", "-n", str(checks)],
                                  capture_output=True, text=True)
            if proc.returncode != 0:
                errors.append(f"{s.name}: checks.sh fails bash -n: "
                              f"{proc.stderr.strip()}")
        else:
            warnings.append(f"{s.name}: no checks.sh — judge-only scenario")
    return errors, warnings


def main() -> int:
    errors, warnings = validate(Path(__file__).resolve().parent)
    for w in warnings:
        print(f"warn: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"validate: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
