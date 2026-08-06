#!/usr/bin/env python3
"""Static suite validation — no LLM, no credentials, no submission (night
eval content spec §7). Runs in CI before submit so a malformed suite costs
zero tokens. Checks: scenario asset completeness, rubric question lines in
the judge's '- ' convention, bash -n on any checks.sh, and — the planted-
marker check — `checks.sh pre` run against a fresh copy of the scenario's
fixture/ must exit 0 (a pre that fails or breaks against the pristine
fixture means the fixture's facts drifted out from under the rubric/checks
that assume them). Also validates every `evals/sabotage/<flow>/` suite:
bash -n on corruption scripts, manifest index bounds against the flow's
rubric, must_flip/tree_questions subset consistency, and gold/variants
path existence — a bad sabotage manifest is exactly as cheap to catch here
as a bad scenario. T2 trigger-corpus validation lands with the T2 runner
(needs YAML)."""
from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PRE_CHECK_TIMEOUT_S = 60
RUNNER_PATH = (Path(__file__).resolve().parent.parent / ".github" / "actions" /
               "eval-run" / "run.py")


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


def _rubric_question_count(rubric: Path) -> int:
    return len([l for l in rubric.read_text().splitlines()
                if l.startswith("- ")])


def _validate_rubric_contract(name: str, rubric: Path) -> list[str]:
    spec = importlib.util.spec_from_file_location("eval_run_for_validation", RUNNER_PATH)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    try:
        runner.parse_rubric(rubric)
        return []
    except ValueError as error:
        return [f"{name}: {error}"]


def _validate_sabotage_flow(flow: Path, root: Path) -> list[str]:
    """One `evals/sabotage/<flow>/` suite (content spec §9): corruption
    scripts must be syntactically valid, the manifest's question indexes
    must fit the flow's rubric, must_flip must stay inside tree_questions
    when tree_questions narrows the sabotage-scored set, and every path the
    manifest names must actually exist."""
    errors = []
    name = flow.name

    for script in sorted((flow / "corruptions").glob("*.sh")) \
            if (flow / "corruptions").is_dir() else []:
        proc = subprocess.run(["bash", "-n", str(script)],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            errors.append(f"sabotage/{name}: {script.name} fails bash -n: "
                          f"{proc.stderr.strip()}")

    manifest_path = flow / "manifest.json"
    if not manifest_path.is_file():
        errors.append(f"sabotage/{name}: missing manifest.json")
        return errors
    manifest = json.loads(manifest_path.read_text())

    rubric = root / "rubrics" / f"{name}.md"
    if not rubric.is_file():
        errors.append(f"sabotage/{name}: missing rubric "
                      f"evals/rubrics/{name}.md")
        n_questions = None
    else:
        n_questions = _rubric_question_count(rubric)

    tree_questions = manifest.get("tree_questions")
    if n_questions is not None:
        if tree_questions is not None:
            for qi in tree_questions:
                if not (1 <= qi <= n_questions):
                    errors.append(
                        f"sabotage/{name}: tree_questions index {qi} out of "
                        f"range 1..{n_questions}")
        for cor in manifest.get("corruptions", []):
            for qi in cor.get("must_flip", []):
                if not (1 <= qi <= n_questions):
                    errors.append(
                        f"sabotage/{name}: {cor.get('script')} must_flip "
                        f"index {qi} out of range 1..{n_questions}")

    if tree_questions is not None:
        tree_set = set(tree_questions)
        for cor in manifest.get("corruptions", []):
            bad = [qi for qi in cor.get("must_flip", []) if qi not in tree_set]
            if bad:
                errors.append(
                    f"sabotage/{name}: {cor.get('script')} must_flip {bad} "
                    f"not a subset of tree_questions {tree_questions}")

    if not (flow / "gold").is_dir():
        errors.append(f"sabotage/{name}: missing gold/")

    for var_name, rel in manifest.get("variants", {}).items():
        if not (flow / rel).is_dir():
            errors.append(f"sabotage/{name}: variant {var_name!r} path "
                          f"{rel!r} does not exist")

    return errors


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
        else:
            errors.extend(_validate_rubric_contract(s.name, rubric))
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

    sabotage_dir = root / "sabotage"
    flows = sorted(p for p in sabotage_dir.iterdir() if p.is_dir()) \
        if sabotage_dir.is_dir() else []
    for flow in flows:
        errors.extend(_validate_sabotage_flow(flow, root))

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
