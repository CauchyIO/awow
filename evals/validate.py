#!/usr/bin/env python3
"""Static suite validation — no LLM, no credentials, no submission (night
eval content spec §7). Runs in CI before submit so a malformed suite costs
zero tokens. Checks: scenario asset completeness, rubric question lines in
the judge's '- ' convention, bash -n on any checks.sh, and — the planted-
marker check — `checks.sh pre` run against a fresh copy of the scenario's
fixture/ must exit 0 (a pre that fails or breaks against the pristine
fixture means the fixture's facts drifted out from under the rubric/checks
that assume them). T2 trigger-corpus validation lands with the T2 runner
(needs YAML)."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PRE_CHECK_TIMEOUT_S = 60


def _check_pre_against_pristine_fixture(name: str, checks: Path,
                                        fixture: Path) -> list[str]:
    """Spec §7: 'planted markers exist in fixture', done the principled way —
    actually run `checks.sh pre` against a fresh, untouched copy of the
    fixture rather than grepping for marker strings. `pre` is defined to
    assert the fixture's starting facts (spec §3), so rc 0 here is the real
    proof those facts still hold; rc 1 means they drifted, anything else
    means the check itself is broken."""
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "fixture"
        shutil.copytree(fixture, copy)
        try:
            proc = subprocess.run(["bash", str(checks), "pre"], cwd=copy,
                                  capture_output=True, text=True,
                                  timeout=PRE_CHECK_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return [f"{name}: checks.sh pre broken against the pristine "
                    f"fixture (timed out after {PRE_CHECK_TIMEOUT_S}s)"]
        if proc.returncode == 0:
            return []
        if proc.returncode == 1:
            return [f"{name}: checks.sh pre fails against the pristine "
                    f"fixture (fixture facts drifted)"]
        return [f"{name}: checks.sh pre broken against the pristine "
                f"fixture (rc {proc.returncode})"]


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
        fixture = s / "fixture"
        fixture_ok = fixture.is_dir()
        if not fixture_ok:
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
            elif fixture_ok:
                errors.extend(_check_pre_against_pristine_fixture(s.name, checks, fixture))
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
