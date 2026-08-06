#!/usr/bin/env python3
"""Run and combine the fixed local awow model campaign. Stdlib only."""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SEATS_PATH = ROOT / "evals" / "model-seats.json"
RUBRICS = ROOT / "evals" / "rubrics"
RUNNER_PATH = ROOT / ".github" / "actions" / "eval-run" / "run.py"
PROFILES = {
    "establishment": {"scenarios": ["setup-awow-walkthrough"], "reps": 10},
    "snapshot": {"scenarios": ["setup-awow-walkthrough"], "reps": 5},
}
HARNESS_IDS = {"Codex": "codex", "Claude Code": "claude-code", "Pi": "pi"}
SNAPSHOT_START = "<!-- eval-snapshot:start -->"
SNAPSHOT_END = "<!-- eval-snapshot:end -->"


def load_seats(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    if data.get("schema") != 1 or not data.get("eval_version"):
        raise ValueError(f"{path}: unsupported model-seat contract")
    seats = data.get("seats")
    if not isinstance(seats, list) or not seats:
        raise ValueError(f"{path}: seats must be a non-empty list")
    required = {"id", "name", "model", "effort", "harness", "manual",
                "weekly", "baseline_eligible"}
    for seat in seats:
        missing = required - seat.keys()
        if missing or seat.get("harness") not in HARNESS_IDS:
            raise ValueError(f"{path}: malformed seat {seat!r}; missing={sorted(missing)}")
        if any(key in seat for key in ("endpoint", "base_url", "provider_url")):
            raise ValueError(f"{path}: serving endpoints do not belong in model seats")
    ids = [seat["id"] for seat in seats]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate seat ID")
    return seats


def _load_runner():
    spec = importlib.util.spec_from_file_location("eval_run_for_campaign", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer at {RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _subject_sha(subject_root: Path) -> str:
    status = subprocess.run(
        ["git", "-C", str(subject_root), "status", "--porcelain"],
        check=True, capture_output=True, text=True).stdout
    if status.strip():
        raise RuntimeError("subject checkout is dirty; commit or move changes before a campaign")
    return subprocess.run(
        ["git", "-C", str(subject_root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True).stdout.strip()


def _metrics(cells: list[dict]) -> dict:
    processes = [cell.get("process") or {} for cell in cells]
    tokens = [p["tokens"] for p in processes if isinstance(p.get("tokens"), (int, float))]
    costs = [p["cost_usd"] for p in processes
             if isinstance(p.get("cost_usd"), (int, float))]
    return {
        "tokens": sum(tokens) if tokens else None,
        "cost_usd": round(sum(costs), 8) if costs else None,
        "wall_s": round(sum(p.get("wall_s", 0) for p in processes), 1),
    }


def _systematic_failure(cells: list[dict]) -> bool:
    return bool(cells) and all(cell.get("verdict") == "indeterminate"
                               and cell.get("stage") == "runner"
                               for cell in cells)


def _resolution(args, seat_id: str) -> str:
    resolved = args.model_resolution.get(seat_id)
    if not isinstance(resolved, str) or not resolved.strip():
        raise ValueError(f"model resolution missing for {seat_id}")
    return resolved


def validate_model_resolution(seats: list[dict], resolution: dict) -> dict:
    if not isinstance(resolution, dict):
        raise ValueError("model resolution must be a seat-ID-to-model-ID object")
    missing = [seat["id"] for seat in seats
               if not isinstance(resolution.get(seat["id"]), str)
               or not resolution[seat["id"]].strip()]
    if missing:
        raise ValueError("model resolution missing: " + ", ".join(missing))
    return resolution


def _evaluator_python() -> str:
    executable = shutil.which("python3.12")
    if executable is None:
        raise RuntimeError("the overnight evaluator requires python3.12")
    return executable


def run_seat(seat: dict, args) -> Path:
    """Generate existing bundles, invoke the existing evaluator, compact once."""
    seat_dir = args.out / seat["id"]
    compact_path = seat_dir / "eval-result.json"
    resolved_model_id = _resolution(args, seat["id"])
    identity = {"id": seat["id"], "name": seat["name"],
                "model_id": resolved_model_id, "harness": seat["harness"],
                "effort": seat["effort"]}
    provenance = {
        "contract": "awow.eval-local-run/v1",
        "subject_sha": args.subject_sha,
        "eval_version": args.eval_version,
        "awow_version": args.awow_version,
        "profile": args.profile,
        "scenarios": args.scenarios,
        "reps": args.reps,
        "seat": identity,
        "requested_model": seat["model"],
    }
    if compact_path.is_file():
        existing = json.loads(compact_path.read_text())
        expected_runs = len(args.scenarios) * args.reps
        compatible = (existing.get("contract") == "awow.eval-scorecard/v1"
                      and existing.get("subject_sha") == args.subject_sha
                      and existing.get("eval_version") == args.eval_version
                      and existing.get("awow_version") == args.awow_version
                      and existing.get("profile") == args.profile
                      and existing.get("scenarios") == args.scenarios
                      and existing.get("requested_model") == seat["model"]
                      and existing.get("seat") == identity
                      and existing.get("coverage", {}).get(
                          "requested_repetitions") == expected_runs)
        if not compatible:
            raise RuntimeError(f"{compact_path}: existing result is for another campaign")
        return compact_path  # a terminal low score is data, never a retry reason
    seat_dir.mkdir(parents=True, exist_ok=True)
    request_path = seat_dir / "request.yaml"
    scenarios = ", ".join(args.scenarios)
    request_path.write_text(
        "contract: eval/v1\n"
        "suite: evals\n"
        f"scenarios: [{scenarios}]\n"
        "tiers: [bulk]\n"
        f"reps: {args.reps}\n"
        f"budget_tokens_total: {400000 * len(args.scenarios) * args.reps}\n")

    bundles = seat_dir / "bundles"
    local_result = seat_dir / "run" / "result.json"
    provenance_path = seat_dir / "run-provenance.json"
    if local_result.is_file():
        prior = (json.loads(provenance_path.read_text())
                 if provenance_path.is_file() else None)
        if prior != provenance:
            raise RuntimeError(
                f"{local_result}: local evaluator result is for another campaign")
    else:
        provenance_path.write_text(json.dumps(provenance, indent=1) + "\n")
        python = _evaluator_python()
        subprocess.run([
            python, str(args.evaluator_root / "make_eval_bundles.py"),
            str(request_path), "--sha", args.subject_sha, "--repo", "CauchyIO/awow",
            "--out", str(bundles), "--root", str(seat_dir / "box"),
            "--clone", str(args.subject_root),
        ], check=True)
        entry = {"seat": HARNESS_IDS[seat["harness"]], "model": seat["model"]}
        if seat["harness"] in ("Codex", "Claude Code"):
            entry["effort"] = seat["effort"]
        seatmap = seat_dir / "seatmap.json"
        seatmap.write_text(json.dumps({"bulk": entry}, indent=1) + "\n")
        subprocess.run([
            python, str(args.evaluator_root / "eval_run_local.py"),
            str(bundles), "--suite-root", str(args.subject_root),
            "--out", str(seat_dir / "run"), "--seatmap", str(seatmap),
        ], check=True)

    local = json.loads(local_result.read_text())
    if local.get("request_sha") not in (None, args.subject_sha):
        raise RuntimeError(f"{local_result}: result is for another subject")
    cells = local.get("cells") or []
    runner = _load_runner()
    runner.validate_resolved_model(cells, identity)
    scored = runner.score_run(cells, RUBRICS, args.reps)
    compact = {
        "contract": "awow.eval-scorecard/v1",
        "subject_sha": args.subject_sha,
        "eval_version": args.eval_version,
        "awow_version": args.awow_version,
        "profile": args.profile,
        "scenarios": args.scenarios,
        "seat": identity,
        "requested_model": seat["model"],
        "coverage": scored["coverage"],
        "capabilities": scored["capabilities"],
        "metrics": _metrics(cells),
        "systematic_failure": _systematic_failure(cells),
    }
    compact_path.write_text(json.dumps(compact, indent=1) + "\n")
    return compact_path


def merge_campaign(paths: list[Path]) -> dict:
    if not paths:
        raise ValueError("campaign has no results")
    runs = [json.loads(path.read_text()) for path in paths]
    if any(run.get("contract") != "awow.eval-scorecard/v1" for run in runs):
        raise ValueError("campaign input has an unknown contract")
    subjects = {run.get("subject_sha") for run in runs}
    versions = {run.get("eval_version") for run in runs}
    awow_versions = {run.get("awow_version") for run in runs}
    profiles = {run.get("profile") for run in runs}
    scenarios = {tuple(run.get("scenarios") or []) for run in runs}
    ids = [run.get("seat", {}).get("id") for run in runs]
    if any(len(values) != 1 or None in values for values in
           (subjects, versions, awow_versions, profiles)) or len(scenarios) != 1:
        raise ValueError("campaign inputs mix subject, version, profile, or scenarios")
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError("campaign inputs have a missing or duplicate seat ID")
    order = {seat["id"]: index for index, seat in enumerate(load_seats(SEATS_PATH))}
    runs.sort(key=lambda run: order.get(run["seat"]["id"], len(order)))
    return {"contract": "awow.eval-campaign/v1",
            "subject_sha": subjects.pop(), "eval_version": versions.pop(),
            "awow_version": awow_versions.pop(), "profile": profiles.pop(),
            "runs": runs}


def summarize_run(run: dict) -> dict:
    capabilities = list((run.get("capabilities") or {}).values())
    values = lambda key: [cap[key] for cap in capabilities
                          if isinstance(cap.get(key), (int, float))]
    outcome, process = values("outcome"), values("process")
    outcome_score = round(sum(outcome) / len(outcome), 2) if outcome else None
    process_score = round(sum(process) / len(process), 2) if process else None
    coverage = run.get("coverage") or {}
    return {**(run.get("seat") or {}),
            "outcome": outcome_score, "process": process_score,
            "balanced": (round((outcome_score + process_score) / 2, 2)
                         if None not in (outcome_score, process_score) else None),
            "strict_pass": bool(capabilities)
                           and all(cap.get("strict_pass") for cap in capabilities),
            "valid_runs": coverage.get("valid_repetitions", 0),
            "requested_runs": coverage.get("requested_repetitions", 0),
            "systematic_failure": bool(run.get("systematic_failure")),
            "metrics": run.get("metrics") or {}}


def qualifies(seat_result: dict) -> tuple[bool, list[str]]:
    reasons = []
    valid, requested = (seat_result.get("valid_runs", 0),
                        seat_result.get("requested_runs", 0))
    if not requested or valid / requested < 0.95:
        reasons.append("valid runs below 95%")
    for dimension in ("outcome", "process"):
        value = seat_result.get(dimension)
        if not isinstance(value, (int, float)) or value < 80:
            reasons.append(f"{dimension} below 80")
    if not seat_result.get("strict_pass"):
        reasons.append("strict pass failed")
    if seat_result.get("systematic_failure"):
        reasons.append("systematic harness or tool failure")
    return not reasons, reasons


def _score(value) -> str:
    return "—" if not isinstance(value, (int, float)) else f"{value:.1f}%"


def _reading(run: dict, previous: dict | None) -> str:
    if previous is None:
        return "unmeasured"
    compared = _load_runner().compare_report(run, previous)
    readings = [cap.get("reading", "unmeasured")
                for cap in compared.get("capabilities", {}).values()]
    for value in ("lowered", "unmeasured", "raised", "held"):
        if value in readings:
            return value
    return "unmeasured"


def validate_campaign(campaign: dict) -> tuple[list[dict], dict[str, dict]]:
    if campaign.get("contract") != "awow.eval-campaign/v1":
        raise ValueError("unsupported campaign contract")
    profile = campaign.get("profile")
    if profile not in PROFILES:
        raise ValueError(f"unsupported campaign profile {profile!r}")

    config = json.loads(SEATS_PATH.read_text())
    roster = load_seats(SEATS_PATH)
    roster_by_id = {seat["id"]: seat for seat in roster}
    expected_ids = set(roster_by_id)
    runs = campaign.get("runs")
    if not isinstance(runs, list):
        raise ValueError("campaign runs must be a list")
    ids = [run.get("seat", {}).get("id") for run in runs]
    if len(ids) != len(set(ids)):
        raise ValueError("campaign has duplicate seat IDs")
    missing, extra = expected_ids - set(ids), set(ids) - expected_ids
    if missing or extra:
        raise ValueError(f"campaign roster mismatch; missing={sorted(missing)}, "
                         f"extra={sorted(extra)}")

    resolution = validate_model_resolution(roster, campaign.get("model_resolution"))
    if set(resolution) != expected_ids:
        raise ValueError("campaign model resolution must match the fixed roster")
    subject = campaign.get("subject_sha")
    eval_version = campaign.get("eval_version")
    awow_version = campaign.get("awow_version")
    if eval_version != config["eval_version"]:
        raise ValueError("campaign eval version is not current")
    if not isinstance(subject, str) or not subject or not awow_version:
        raise ValueError("campaign subject or awow version is missing")

    expected_scenarios = PROFILES[profile]["scenarios"]
    expected_runs = len(expected_scenarios) * PROFILES[profile]["reps"]
    by_id = {}
    for run in runs:
        seat_id = run["seat"]["id"]
        seat = roster_by_id[seat_id]
        identity = {"id": seat_id, "name": seat["name"],
                    "model_id": resolution[seat_id],
                    "harness": seat["harness"], "effort": seat["effort"]}
        if run.get("contract") != "awow.eval-scorecard/v1":
            raise ValueError(f"{seat_id}: unsupported scorecard contract")
        if run.get("seat") != identity or run.get("requested_model") != seat["model"]:
            raise ValueError(f"{seat_id}: scorecard seat identity drifted")
        if (run.get("subject_sha") != subject
                or run.get("eval_version") != eval_version
                or run.get("awow_version") != awow_version
                or run.get("profile") != profile
                or run.get("scenarios") != expected_scenarios):
            raise ValueError(f"{seat_id}: scorecard provenance is incompatible")
        if run.get("coverage", {}).get("requested_repetitions") != expected_runs:
            raise ValueError(f"{seat_id}: scorecard repetition count is incompatible")
        by_id[seat_id] = run
    return roster, by_id


def render_weekly_summary(runs: list[dict], previous: list[dict] | None = None) -> str:
    roster = [seat for seat in load_seats(SEATS_PATH) if seat["weekly"]]
    current = {run.get("seat", {}).get("id"): run for run in runs}
    prior = {run.get("seat", {}).get("id"): run for run in (previous or [])}
    lines = ["## Weekly model support", "",
             "| Model / effort | Harness | Outcome | Process | Balanced | Strict pass | Valid runs | Cost | Latency | Reading |",
             "|---|---|---:|---:|---:|---|---:|---:|---:|---|"]
    for seat in roster:
        run = current.get(seat["id"])
        result = summarize_run(run) if run else {}
        metrics = result.get("metrics") or {}
        cost = metrics.get("cost_usd")
        wall = metrics.get("wall_s")
        lines.append(
            f"| {seat['name']} / {seat['effort']} | {seat['harness']} "
            f"| {_score(result.get('outcome'))} | {_score(result.get('process'))} "
            f"| {_score(result.get('balanced'))} "
            f"| {'yes' if result.get('strict_pass') else ('no' if run else '—')} "
            f"| {result.get('valid_runs', 0)}/{result.get('requested_runs', 0)} "
            f"| {f'${cost:.4f}' if isinstance(cost, (int, float)) else '—'} "
            f"| {f'{wall:.1f}s' if isinstance(wall, (int, float)) else '—'} "
            f"| {_reading(run, prior.get(seat['id'])) if run else 'unmeasured'} |")
    lines += ["", "A reading is calculated only when a compatible prior weekly "
              "snapshot is supplied explicitly."]
    return "\n".join(lines) + "\n"


def render_readme_snapshot(campaign: dict, performance_id: str,
                           automated_id: str) -> str:
    roster, by_id = validate_campaign(campaign)
    for role, seat_id in (("performance baseline", performance_id),
                          ("automated regression", automated_id)):
        if seat_id not in by_id:
            raise ValueError(f"unknown {role} seat {seat_id!r}")
        ok, reasons = qualifies(summarize_run(by_id[seat_id]))
        if not ok:
            raise ValueError(f"{role} seat {seat_id!r} does not qualify: "
                             + "; ".join(reasons))

    order = [performance_id] + [seat["id"] for seat in roster
                                if seat["id"] != performance_id]
    summaries = {seat_id: summarize_run(by_id[seat_id]) for seat_id in order}
    reps = {summary["requested_runs"] for summary in summaries.values()}
    performance = summaries[performance_id]
    lines = ["### Latest full model snapshot", "",
             f"Run date: {campaign['run_date']}",
             f"awow version: {campaign['awow_version']} (`{campaign['subject_sha']}`)",
             f"Eval version: {campaign['eval_version']} · Repetitions: {reps.pop()}",
             (f"**Performance baseline**: {performance['name']} / "
              f"{performance['effort']} — {performance['harness']}")]
    if automated_id != performance_id:
        automated = summaries[automated_id]
        lines.append(f"Automated regression seat: {automated['name']} / "
                     f"{automated['effort']} — {automated['harness']}")
    lines += ["", "| Role | Model / effort | Harness | Outcome | Process | Balanced | Strict pass | Valid runs |",
              "|---|---|---|---:|---:|---:|---|---:|"]
    for seat_id in order:
        result = summaries[seat_id]
        role = ("**Performance baseline**" if seat_id == performance_id else
                "Automated regression" if seat_id == automated_id else "Candidate")
        lines.append(f"| {role} | {result['name']} / {result['effort']} "
                     f"| {result['harness']} | {_score(result['outcome'])} "
                     f"| {_score(result['process'])} | {_score(result['balanced'])} "
                     f"| {'yes' if result['strict_pass'] else 'no'} "
                     f"| {result['valid_runs']}/{result['requested_runs']} |")
    return "\n".join(lines) + "\n"


def replace_snapshot(readme: str, block: str) -> str:
    if readme.count(SNAPSHOT_START) != 1 or readme.count(SNAPSHOT_END) != 1:
        raise ValueError("README requires exactly one eval snapshot marker pair")
    before, tail = readme.split(SNAPSHOT_START)
    _, after = tail.split(SNAPSHOT_END)
    return (before + SNAPSHOT_START + "\n" + block.strip() + "\n"
            + SNAPSHOT_END + after)


def _read_results(path: Path) -> list[dict]:
    paths = [path] if path.is_file() else sorted(path.rglob("eval-result.json"))
    runs = [json.loads(item.read_text()) for item in paths]
    if any(run.get("contract") != "awow.eval-scorecard/v1" for run in runs):
        raise ValueError(f"{path}: unsupported scorecard contract")
    ids = [run.get("seat", {}).get("id") for run in runs]
    if None in ids or len(ids) != len(set(ids)):
        raise ValueError(f"{path}: missing or duplicate seat ID")
    return runs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--evaluator-root", required=True, type=Path)
    run.add_argument("--model-resolution", required=True, type=Path)
    run.add_argument("--profile", choices=sorted(PROFILES), required=True)
    run.add_argument("--out", required=True, type=Path)
    summarize = commands.add_parser("summarize")
    summarize.add_argument("--mode", choices=("weekly",), required=True)
    summarize.add_argument("--inputs", required=True, type=Path)
    summarize.add_argument("--previous", type=Path)
    summarize.add_argument("--github-summary", required=True, type=Path)
    publish = commands.add_parser("publish")
    publish.add_argument("campaign", type=Path)
    publish.add_argument("--performance-baseline", required=True)
    publish.add_argument("--automated-seat", required=True)
    publish.add_argument("--readme", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "summarize":
        text = render_weekly_summary(
            _read_results(args.inputs),
            _read_results(args.previous) if args.previous else None)
        args.github_summary.parent.mkdir(parents=True, exist_ok=True)
        with args.github_summary.open("a") as stream:
            stream.write(text)
        return 0
    if args.command == "publish":
        campaign = json.loads(args.campaign.read_text())
        block = render_readme_snapshot(campaign, args.performance_baseline,
                                       args.automated_seat)
        args.readme.write_text(replace_snapshot(args.readme.read_text(), block))
        print(f"Review with: git diff -- {args.readme}")
        return 0

    profile = PROFILES[args.profile]
    args.subject_root = ROOT
    args.subject_sha = _subject_sha(ROOT)
    args.awow_version = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
    args.scenarios = profile["scenarios"]
    args.reps = profile["reps"]
    args.model_resolution = json.loads(args.model_resolution.read_text())
    config = json.loads(SEATS_PATH.read_text())
    args.eval_version = config["eval_version"]
    seats = [seat for seat in load_seats(SEATS_PATH) if seat["manual"]]
    validate_model_resolution(seats, args.model_resolution)
    paths = [run_seat(seat, args) for seat in seats]
    merged = merge_campaign(paths)
    merged.update({
        "run_date": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "model_resolution": args.model_resolution,
    })
    args.out.mkdir(parents=True, exist_ok=True)
    output = args.out / "campaign.json"
    output.write_text(json.dumps(merged, indent=1) + "\n")
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
