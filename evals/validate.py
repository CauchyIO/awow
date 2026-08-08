#!/usr/bin/env python3
"""Static suite validation — no LLM, no credentials, no submission (night
eval content spec §7). Runs in CI before submit so a malformed suite costs
zero tokens. A scenario's starting tree is composed, not stored: the world
named by its world.txt (from `evals/worlds/`, default: empty) overlaid with
its overlay/. Checks: scenario asset completeness, world resolution, rubric
question lines in the judge's '- ' convention, bash -n on any checks.sh,
the two duplication guards (a file shared byte-identical by two overlays
belongs in a world; an overlay file identical to its world's copy is dead
weight), and — the planted-marker check — `checks.sh pre` run against a
fresh composition of the scenario's tree must exit 0 (a pre that fails or
breaks against the pristine tree means the fixture's facts drifted out
from under the rubric/checks that assume them). Also validates every
`evals/sabotage/<flow>/` suite:
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


def compose_fixture(scenario: Path, worlds_dir: Path, dest: Path) -> None:
    """Materialize the tree a scenario's session starts in: the world named
    by world.txt copied whole, then overlay/ layered on top (overlay wins on
    a path collision; the merge is purely additive — an overlay cannot
    remove a world file). No world.txt means the empty world: the overlay
    is the entire tree. Raises on an unresolvable world — a scenario that
    cannot compose must never validate."""
    world_ref = scenario / "world.txt"
    if world_ref.is_file():
        world = worlds_dir / world_ref.read_text().strip()
        shutil.copytree(world, dest)
    else:
        dest.mkdir(parents=True)
    overlay = scenario / "overlay"
    if overlay.is_dir():
        shutil.copytree(overlay, dest, dirs_exist_ok=True)


def _check_pre_against_pristine_fixture(name: str, checks: Path,
                                        scenario: Path,
                                        worlds_dir: Path) -> list[str]:
    """Spec §7: 'planted markers exist in fixture', done the principled way —
    actually run `checks.sh pre` against a fresh composition of the
    scenario's tree rather than grepping for marker strings. `pre` is
    defined to assert the fixture's starting facts (spec §3), so rc 0 here
    is the real proof those facts still hold; rc 1 means they drifted,
    anything else means the check itself is broken."""
    with tempfile.TemporaryDirectory() as td:
        copy = Path(td) / "fixture"
        compose_fixture(scenario, worlds_dir, copy)
        try:
            proc = subprocess.run(["bash", str(checks.resolve()), "pre"], cwd=copy,
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


def _validate_world(s: Path, worlds_dir: Path) -> list[str]:
    """world.txt is optional (absent = the empty world); when present it
    must be a single name resolving to a directory under evals/worlds/."""
    world_ref = s / "world.txt"
    if not world_ref.is_file():
        if not (s / "overlay").is_dir():
            return [f"{s.name}: missing overlay/ (and no world.txt)"]
        return []
    name = world_ref.read_text().strip()
    if not name or "\n" in name or "/" in name:
        return [f"{s.name}: world.txt must hold one world name, "
                f"got {name!r}"]
    if not (worlds_dir / name).is_dir():
        return [f"{s.name}: world.txt names {name!r} but "
                f"evals/worlds/{name}/ does not exist"]
    return []


def _validate_overlay_duplication(scenarios: list[Path],
                                  worlds_dir: Path) -> list[str]:
    """The two guards that keep the composition honest: a file two overlays
    share byte-identically belongs in a world, and an overlay file identical
    to its own world's copy at the same relative path shadows nothing."""
    errors = []
    seen: dict[tuple[str, bytes], str] = {}
    for s in sorted(scenarios):
        overlay = s / "overlay"
        if not overlay.is_dir():
            continue
        world_ref = s / "world.txt"
        world = (worlds_dir / world_ref.read_text().strip()) \
            if world_ref.is_file() else None
        for f in sorted(p for p in overlay.rglob("*") if p.is_file()):
            rel = str(f.relative_to(overlay))
            content = f.read_bytes()
            prior = seen.get((rel, content))
            if prior is not None and prior != s.name:
                errors.append(
                    f"{s.name}: overlay/{rel} is byte-identical to "
                    f"{prior}'s copy — move it into a world under "
                    f"evals/worlds/")
            seen.setdefault((rel, content), s.name)
            if world is not None and (world / rel).is_file() \
                    and (world / rel).read_bytes() == content:
                errors.append(
                    f"{s.name}: overlay/{rel} is identical to its world's "
                    f"copy — delete the overlay file")
    return errors


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    worlds_dir = root / "worlds"
    scenarios_dir = root / "scenarios"
    scenarios = sorted(p for p in scenarios_dir.iterdir() if p.is_dir()) \
        if scenarios_dir.is_dir() else []
    if not scenarios:
        errors.append("no scenario directories under evals/scenarios/")
    for s in scenarios:
        for req in ("persona.md", "opening.md", "observe-writes.txt"):
            if not (s / req).is_file():
                errors.append(f"{s.name}: missing {req}")
        world_errors = _validate_world(s, worlds_dir)
        errors.extend(world_errors)
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
            elif not world_errors:
                errors.extend(_check_pre_against_pristine_fixture(
                    s.name, checks, s, worlds_dir))
        else:
            warnings.append(f"{s.name}: no checks.sh — judge-only scenario")

    errors.extend(_validate_overlay_duplication(scenarios, worlds_dir))

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
