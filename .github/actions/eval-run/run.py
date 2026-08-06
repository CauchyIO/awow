#!/usr/bin/env python3
"""Submit the checked-out eval suite to the night eval service, poll the run
to a terminal status, and write scores to the step summary. Stdlib only —
inputs arrive as EVAL_* env vars (see action.yml). Fail loud: any unexpected
API response raises and fails the step with the real error visible.

Gateway and network faults are the one exception, and they are retried rather
than swallowed. The control plane is a consumption-plan function that scales to
zero between 30-second polls, so an occasional 5xx from the gateway says
nothing about the run itself — a poll loop that dies on the first one throws
away an eval that has already been paid for. A retry that runs out still
raises, with the real error and the count of what was tolerated."""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

POLL_SECONDS = 30
POLL_LIMIT = 120  # 60 minutes — cold starts have run 25-28 min; 30 was too thin a margin
TRANSIENT_STATUS = {500, 502, 503, 504}
RETRY_BACKOFF = (2, 5, 15)  # seconds before retry 1, 2, 3+
MAX_CONSECUTIVE_POLL_FAILURES = 5
DELTA_THRESHOLD_PP = 5.0
QUESTION_ID = re.compile(r"\*\*(Q\d+)\*\*")
CAPABILITY = re.compile(r"^Capability:\s*`([^`]+)`\s*$", re.MULTILINE)
CRITICAL = re.compile(r"^Critical:\s*(.+)$", re.MULTILINE)


class Transient(Exception):
    """A gateway or network fault, which says nothing about the run itself."""


def request(method: str, path: str, body: dict | None = None) -> dict:
    """One HTTP call. Raises Transient for gateway/network faults; anything
    the service itself said propagates unchanged."""
    req = urllib.request.Request(
        os.environ["EVAL_BASE_URL"] + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Ocp-Apim-Subscription-Key": os.environ["EVAL_API_KEY"],
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in TRANSIENT_STATUS:
            raise Transient(f"HTTP {e.code} {e.reason}") from e
        raise
    except urllib.error.URLError as e:
        raise Transient(f"network: {e.reason}") from e


def api(method: str, path: str, body: dict | None = None,
        attempts: int = 1) -> dict:
    """request() with backoff across `attempts` tries. attempts=1 is a single
    shot, which is what POST /runs needs: it is not idempotent, so retrying it
    risks creating a second run and billing the tenant for both."""
    for i in range(1, attempts + 1):
        try:
            return request(method, path, body)
        except Transient as e:
            if i == attempts:
                raise
            delay = RETRY_BACKOFF[min(i - 1, len(RETRY_BACKOFF) - 1)]
            print(f"transient on {method} {path}: {e} — "
                  f"retry {i}/{attempts - 1} in {delay}s", flush=True)
            time.sleep(delay)


def summary(*lines: str) -> None:
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write("\n".join(lines) + "\n")


def md_cell(text: str) -> str:
    """One markdown table cell: no pipes, no newlines."""
    return text.replace("|", "\\|").replace("\n", " ")


def verdict_note(c: dict) -> str:
    v = c.get("verdict")
    if v in (None, "pass"):
        return ""
    stage = f" ({c['stage']})" if c.get("stage") else ""
    return f" — **{v}**{stage}"


def parse_rubric(path: Path) -> dict:
    text = path.read_text()
    capabilities, critical_lines = CAPABILITY.findall(text), CRITICAL.findall(text)
    if len(capabilities) != 1:
        raise ValueError(f"{path}: expected exactly one Capability")
    if len(critical_lines) != 1:
        raise ValueError(f"{path}: expected exactly one Critical line")
    critical = set(re.findall(r"`(Q\d+)`", critical_lines[0]))
    questions, section = {}, None
    headings = {"outcome": 0, "process": 0}
    for line in text.splitlines():
        if line in ("## Outcome", "## Process"):
            section = line[3:].lower()
            headings[section] += 1
        elif line.startswith("## "):
            section = None
        elif line.startswith("- "):
            match = QUESTION_ID.search(line)
            if not match or section is None:
                raise ValueError(f"{path}: unlabeled rubric question: {line}")
            qid = match.group(1)
            if qid in questions:
                raise ValueError(f"{path}: duplicate rubric question {qid}")
            questions[qid] = {"dimension": section, "critical": qid in critical}
    expected = [f"Q{i}" for i in range(1, len(questions) + 1)]
    if headings != {"outcome": 1, "process": 1}:
        raise ValueError(f"{path}: requires exactly one Outcome and Process section")
    if not questions or list(questions) != expected:
        raise ValueError(f"{path}: question IDs must be consecutive from Q1")
    if not critical or not critical <= questions.keys():
        raise ValueError(f"{path}: missing or unknown critical question")
    empty = [name for name in headings
             if not any(q["dimension"] == name for q in questions.values())]
    if empty:
        raise ValueError(f"{path}: {empty[0].title()} has no questions")
    return {"capability": capabilities[0], "critical": critical,
            "questions": questions}


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 2) if values else None


def _scenario_name(cell_id: str, names) -> str:
    matches = [name for name in names if cell_id.startswith(f"eval-{name}-")]
    if not matches:
        raise ValueError(f"{cell_id}: no matching scenario rubric")
    return max(matches, key=len)


def _question_key(question: str) -> str:
    match = QUESTION_ID.search(question)
    if not match:
        raise ValueError(f"rubric answer has no question ID: {question!r}")
    return match.group(1)


def score_run(cells: list[dict], rubric_dir: Path,
              requested_reps: int) -> dict:
    if requested_reps < 1:
        raise ValueError("requested_reps must be positive")
    rubrics = {path.stem: parse_rubric(path)
               for path in sorted(rubric_dir.glob("*.md"))}
    grouped: dict[str, list[dict]] = {}
    for cell in cells:
        grouped.setdefault(_scenario_name(cell["id"], rubrics), []).append(cell)

    scenarios = {}
    for scenario, scenario_cells in sorted(grouped.items()):
        rubric = rubrics[scenario]
        scores = {"outcome": [], "process": []}
        question_values = {qid: [] for qid in rubric["questions"]}
        valid_cells = [c for c in scenario_cells
                       if c.get("verdict") != "indeterminate"]
        strict = []
        for cell in valid_cells:
            answers = {_question_key(a["question"]): a.get("answer")
                       for a in cell["outcome"]["rubric"]}
            if set(answers) != set(rubric["questions"]):
                raise ValueError(f"{cell['id']}: rubric answer mismatch")
            by_dimension = {"outcome": [], "process": []}
            for qid, meta in rubric["questions"].items():
                answer = answers[qid]
                if answer is None or answer == "n/a":
                    continue
                if type(answer) is not bool:
                    raise ValueError(f"{cell['id']}: invalid answer for {qid}")
                by_dimension[meta["dimension"]].append(answer)
                question_values[qid].append(answer)
            for dimension, values in by_dimension.items():
                if values:
                    scores[dimension].append(100 * sum(values) / len(values))
            process = cell.get("process") or {}
            post = (cell.get("checks") or {}).get("post")
            strict.append(
                all(answers.get(qid) is True for qid in rubric["critical"])
                and (post is None or post.get("rc") == 0)
                and not process.get("scope_violations")
                and not process.get("gate_violation", False))
        outcome, process_score = _mean(scores["outcome"]), _mean(scores["process"])
        questions = {qid: {
            "pass_rate": round(sum(values) / len(values), 4) if values else None,
            **rubric["questions"][qid]}
            for qid, values in question_values.items()}
        valid = len(valid_cells)
        scenarios[scenario] = {
            "capability": rubric["capability"],
            "outcome": outcome,
            "process": process_score,
            "balanced": (round((outcome + process_score) / 2, 2)
                         if outcome is not None and process_score is not None
                         else None),
            "strict_pass": valid == requested_reps and all(strict),
            "valid_runs": valid,
            "requested_runs": requested_reps,
            "questions": questions,
        }

    capabilities = {}
    for capability in sorted({s["capability"] for s in scenarios.values()}):
        members = [(name, score) for name, score in scenarios.items()
                   if score["capability"] == capability]
        outcome = _mean([s["outcome"] for _, s in members if s["outcome"] is not None])
        process_score = _mean([s["process"] for _, s in members
                               if s["process"] is not None])
        occurrences = {qid: sum(qid in s["questions"] for _, s in members)
                       for _, s in members for qid in s["questions"]}
        questions = {}
        for scenario, scored in members:
            for qid, value in scored["questions"].items():
                key = qid if occurrences[qid] == 1 else f"{scenario}:{qid}"
                questions[key] = value
        capabilities[capability] = {
            "outcome": outcome,
            "process": process_score,
            "balanced": (round((outcome + process_score) / 2, 2)
                         if outcome is not None and process_score is not None
                         else None),
            "strict_pass": all(s["strict_pass"] for _, s in members),
            "valid_runs": sum(s["valid_runs"] for _, s in members),
            "requested_runs": sum(s["requested_runs"] for _, s in members),
            "questions": questions,
        }

    first = cells[0] if cells else {}
    return {
        "seat": copy.deepcopy(first.get("seat", {})),
        "eval_version": first.get("eval_version"),
        "coverage": {
            "scenarios_executed": len(scenarios),
            "valid_repetitions": sum(s["valid_runs"] for s in scenarios.values()),
            "requested_repetitions": requested_reps * len(scenarios),
        },
        "scenarios": scenarios,
        "capabilities": capabilities,
    }


def _reading(delta: float | None, threshold_pp: float) -> str:
    if delta is None:
        return "unmeasured"
    if delta > threshold_pp:
        return "raised"
    if delta < -threshold_pp:
        return "lowered"
    return "held"


def compare_report(current: dict, baseline: dict,
                   threshold_pp: float = DELTA_THRESHOLD_PP) -> dict:
    compared = copy.deepcopy(current)
    current_seat, baseline_seat = current.get("seat", {}), baseline.get("seat", {})
    incompatible = [key for key in ("id", "model_id", "harness", "effort")
                    if current_seat.get(key) != baseline_seat.get(key)]
    if current.get("eval_version") != baseline.get("eval_version"):
        incompatible.append("eval_version")

    for capability, scored in compared.get("capabilities", {}).items():
        old = baseline.get("capabilities", {}).get(capability)
        reasons = (["incompatible " + ", ".join(incompatible)] if incompatible else [])
        if not reasons and old is None:
            reasons.append("capability absent from baseline")
        elif not reasons and scored.get("valid_runs", 0) < old.get("valid_runs", 0):
            reasons.append("fewer valid repetitions than baseline")
        if reasons:
            scored.update({
                "outcome_delta": None, "process_delta": None,
                "outcome_reading": "unmeasured",
                "process_reading": "unmeasured",
                "reading": "unmeasured", "reasons": reasons,
            })
            continue

        for dimension in ("outcome", "process"):
            before, after = old.get(dimension), scored.get(dimension)
            delta = (round(after - before, 2)
                     if before is not None and after is not None else None)
            scored[f"{dimension}_delta"] = delta
            scored[f"{dimension}_reading"] = _reading(delta, threshold_pp)

        for qid, question in scored.get("questions", {}).items():
            before = old.get("questions", {}).get(qid, {}).get("pass_rate")
            after = question.get("pass_rate")
            question["baseline_pass_rate"] = before
            question["pass_rate_delta"] = (round(after - before, 4)
                                           if None not in (before, after) else None)

        critical_dimensions = []
        for qid, old_question in old.get("questions", {}).items():
            new_question = scored.get("questions", {}).get(qid)
            if (old_question.get("critical")
                    and old_question.get("pass_rate") == 1.0
                    and (new_question is None
                         or new_question.get("pass_rate") is None
                         or new_question.get("pass_rate") < 1.0)):
                critical_dimensions.append(old_question["dimension"])
                reasons.append(f"{qid} critical requirement regressed")
        if old.get("strict_pass") and not scored.get("strict_pass"):
            reasons.append("strict pass regressed")
        for dimension in critical_dimensions:
            scored[f"{dimension}_reading"] = "lowered"

        dimension_readings = [scored[f"{name}_reading"]
                              for name in ("outcome", "process")]
        if reasons or "lowered" in dimension_readings:
            scored["reading"] = "lowered"
        elif "unmeasured" in dimension_readings:
            scored["reading"] = "unmeasured"
        elif "raised" in dimension_readings:
            scored["reading"] = "raised"
        else:
            scored["reading"] = "held"
        scored["reasons"] = reasons
    return compared


def _format_score(value: float | None, delta: bool = False) -> str:
    if value is None:
        return "—"
    if not delta:
        return f"{value:.1f}%"
    if value == 0:
        return "0.0 pp"
    return f"+{value:.1f} pp" if value > 0 else f"−{abs(value):.1f} pp"


def render_scorecard(record: dict, report: dict) -> list[str]:
    """Native Actions Markdown with skill changes first and evidence below."""
    capabilities = report.get("capabilities", {})
    order = {"lowered": 0, "unmeasured": 1, "held": 2, "raised": 3}
    rows = sorted(capabilities.items(),
                  key=lambda item: (order.get(item[1].get("reading"), 9), item[0]))
    counts = {name: sum(c.get("reading") == name for c in capabilities.values())
              for name in order}
    lines = [
        "## Eval skill changes",
        "",
        (f"**{counts['lowered']} lowered · {counts['unmeasured']} unmeasured · "
         f"{counts['held']} held · {counts['raised']} raised**"),
        "",
        "| Capability | Outcome | Delta | Process | Delta | Strict pass | Reading | Reason |",
        "|---|---:|---:|---:|---:|---|---|---|",
    ]
    for name, scored in rows:
        reason = "; ".join(scored.get("reasons", [])) or "—"
        lines.append(
            f"| {md_cell(name)} | {_format_score(scored.get('outcome'))} "
            f"| {_format_score(scored.get('outcome_delta'), True)} "
            f"| {_format_score(scored.get('process'))} "
            f"| {_format_score(scored.get('process_delta'), True)} "
            f"| {'yes' if scored.get('strict_pass') else '**no**'} "
            f"| {scored.get('reading', 'unmeasured')} | {md_cell(reason)} |"
        )

    changes = [
        f"- `{capability}/{qid}` ({question['dimension']}"
        f"{' critical' if question.get('critical') else ''}): {before:.0%} → {after:.0%}"
        for capability, scored in rows
        for qid, question in scored.get("questions", {}).items()
        for before, after in [(question.get("baseline_pass_rate"),
                               question.get("pass_rate"))]
        if before is not None and after is not None and before != after]
    lines += ["", "### Question changes", *(changes or ["- None."])]

    coverage = report.get("coverage", {})
    seat = report.get("seat", {})
    name = seat.get("name") or seat.get("id") or "unresolved seat"
    model_id = seat.get("model_id") or "unresolved model"
    harness = seat.get("harness") or "unresolved harness"
    effort = seat.get("effort")
    effort_text = f" · Effort: **{effort}**" if effort else ""
    sha = (record.get("data_source") or {}).get("sha", "unknown")
    lines += [
        "",
        "### Measurement",
        (f"Valid repetitions: **{coverage.get('valid_repetitions', 0)}/"
         f"{coverage.get('requested_repetitions', 0)}** · "
         f"Scenarios executed: **{coverage.get('scenarios_executed', 0)}**"),
        (f"Seat: **{md_cell(str(name))}** (`{md_cell(str(model_id))}`) · "
         f"Harness: **{md_cell(str(harness))}**{effort_text}"),
        f"Eval version: **{report.get('eval_version') or 'unresolved'}** · Commit: `{sha}`",
        "Compact artifact: `eval-result.json` (uploaded with this run).",
    ]
    branch = (record.get("metadata") or {}).get("result_branch")
    repo = (record.get("data_source") or {}).get("repo")
    if branch and repo:
        lines.append(f"Detailed evidence: [`{branch}`](https://github.com/{repo}/tree/{branch}).")
    return lines


def emit_annotations(report: dict) -> None:
    for capability, scored in report.get("capabilities", {}).items():
        reasons = "; ".join(scored.get("reasons", []))
        safe = (reasons or scored.get("reading", "unmeasured")).replace("\n", " ")
        if scored.get("reading") == "unmeasured":
            print(f"::warning title=eval unmeasured::{capability}: {safe}")
        elif scored.get("reading") == "lowered":
            critical = any("critical" in reason or "strict pass" in reason
                           for reason in scored.get("reasons", []))
            level = "error" if critical else "warning"
            title = "eval critical regression" if critical else "eval regression"
            print(f"::{level} title={title}::{capability}: {safe}")


def compact_result(record: dict, report: dict) -> dict:
    return {"contract": "awow.eval-scorecard/v1", "run_id": record.get("id"),
            "subject_sha": (record.get("data_source") or {}).get("sha"),
            **{key: report.get(key) for key in
               ("seat", "eval_version", "coverage", "capabilities")}}


def _seat_identity(record: dict, resp: dict) -> dict:
    metadata = record.get("metadata") or {}
    seat = copy.deepcopy(resp.get("seat") or metadata.get("seat") or {})
    seat.setdefault("id", metadata.get("seat_id") or os.getenv("EVAL_SEAT_ID"))
    seat.setdefault("name", metadata.get("model_name") or seat.get("id"))
    seat.setdefault("model_id", metadata.get("resolved_model_id")
                    or record.get("model"))
    seat.setdefault("harness", metadata.get("harness"))
    seat.setdefault("effort", metadata.get("effort"))
    return seat


def _write_action_output(name: str, value: str) -> None:
    output = os.getenv("GITHUB_OUTPUT")
    if output:
        with open(output, "a") as stream:
            stream.write(f"{name}={value}\n")


def render_scores(record: dict, cells: list[dict]) -> list[str]:
    branch, repo = record["metadata"].get("result_branch"), record["data_source"]["repo"]
    lines = ["### Cell evidence", "", "<details><summary>Per-cell scores</summary>", ""]
    for cell in cells:
        outcome = cell["outcome"]
        lines.append(f"- `{cell['id']}`: **{outcome['rubric_yes']}/"
                     f"{outcome['rubric_total']}**{verdict_note(cell)}")
    lines += ["", "</details>", "",
              (f"Transcripts + judge output: [`{branch}`]"
               f"(https://github.com/{repo}/tree/{branch})" if branch else
               "Transcripts: result branch missing from the run record")]
    return lines


def calib_str(calib) -> str:
    """Per-flow calibration map ({flow: hash}, AWO-72) rendered for messages."""
    return (", ".join(f"{f}={h}" for f, h in sorted(calib.items()))
            if isinstance(calib, dict) else repr(calib))


def gate_errors(resp: dict, cells: list[dict], gate: dict) -> list[str]:
    """Return capability regressions or unmeasured required capabilities."""
    run_calib = (resp.get("judge") or {}).get("calibration")
    if not gate.get("sabotage_pass"):
        return ["gate.json has no sabotage_pass — the judge is unqualified; "
                "refusing to gate"]
    if run_calib != gate["calibration"]:
        return [f"run calibration {calib_str(run_calib)} != gate "
                f"{calib_str(gate['calibration'])} — re-baseline before gating"]
    if gate.get("schema") != 2:
        return ["gate.json is not schema 2 — re-derive the model-pinned baseline"]

    current = score_run(cells, Path("evals/rubrics"), gate["requested_reps"])
    current["seat"] = copy.deepcopy(resp.get("seat", {}))
    current["eval_version"] = resp.get("eval_version")
    baseline = {
        "seat": gate["automated_regression_seat"],
        "eval_version": gate["eval_version"],
        "capabilities": gate["capabilities"],
    }
    compared = compare_report(current, baseline)
    errors = []
    for capability in gate["capabilities"]:
        scored = compared["capabilities"].get(capability)
        if scored is None:
            errors.append(f"{capability}: unmeasured — no scored cells")
            continue
        if scored["reading"] == "unmeasured":
            reason = "; ".join(scored["reasons"]) or "incomplete measurement"
            errors.append(f"{capability}: unmeasured — {reason}")
        elif scored["reading"] == "lowered":
            dimensions = [name for name in ("outcome", "process")
                          if scored[f"{name}_reading"] == "lowered"]
            reason = "; ".join(scored["reasons"])
            detail = f" ({reason})" if reason else ""
            errors.append(f"{capability}: lowered {', '.join(dimensions)}{detail}")
    return errors


def main() -> int:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], check=True,
                         capture_output=True, text=True).stdout.strip()
    available = sorted(p.name for p in Path("evals/scenarios").iterdir()
                       if p.is_dir())
    selected = [value.strip() for value in os.getenv("EVAL_SCENARIOS", "").split(",")
                if value.strip()]
    unknown = sorted(set(selected) - set(available))
    if unknown:
        raise ValueError(f"unknown eval scenario(s): {', '.join(unknown)}")
    scenarios = selected or available
    reps = int(os.environ["EVAL_REPS"])
    budget = int(os.environ["EVAL_BUDGET_PER_SCENARIO"]) * len(scenarios) * reps

    try:
        run = api("POST", "/runs", {
            "model": os.environ["EVAL_MODEL"],
            "scenarios": scenarios,
            "data_source": {"sha": sha},
            "reps": reps,
            "budget_tokens_total": budget,
        })
    except Transient as e:
        # Deliberately not retried: the gateway can fail after the backend has
        # already committed the run, so a retry risks a second billed run.
        print(f"::error::submission failed on a transient fault ({e}). The run "
              f"may still have been created for {sha} — check before "
              "resubmitting, or it becomes an orphan nobody collects")
        raise

    run_id = run["id"]
    summary(f"submitted `{run_id}` for `{sha}` "
            f"({len(scenarios)} scenario(s), {reps} rep(s))")

    consecutive = 0
    for attempt in range(1, POLL_LIMIT + 1):
        try:
            record = api("GET", f"/runs/{run_id}")
        except Transient as e:
            consecutive += 1
            print(f"[{attempt}] transient: {e} "
                  f"({consecutive}/{MAX_CONSECUTIVE_POLL_FAILURES})",
                  flush=True)
            if consecutive >= MAX_CONSECUTIVE_POLL_FAILURES:
                print(f"::error::eval service unreachable for {consecutive} "
                      f"consecutive polls; run `{run_id}` may still be running")
                raise
            time.sleep(POLL_SECONDS)
            continue
        consecutive = 0
        status = record["status"]
        print(f"[{attempt}] {status}", flush=True)

        if status == "completed":
            # Idempotent, and the eval is already paid for by this point —
            # losing the scores to one blip here would be the worst trade.
            resp = api("GET", f"/runs/{run_id}/output-items",
                       attempts=len(RETRY_BACKOFF) + 1)
            cells = [item["cell"] for item in resp["data"]]
            scored = score_run(cells, Path("evals/rubrics"), reps)
            scored["seat"] = _seat_identity(record, resp)
            scored["eval_version"] = os.getenv("EVAL_VERSION", "1")
            gate_path = Path("evals/gate.json")
            gate = json.loads(gate_path.read_text()) if gate_path.is_file() else None
            baseline = ({"seat": gate["automated_regression_seat"],
                         "eval_version": gate["eval_version"],
                         "capabilities": gate["capabilities"]}
                        if gate else
                        {"seat": scored["seat"],
                         "eval_version": scored["eval_version"],
                         "capabilities": {}})
            report = compare_report(scored, baseline)
            summary(*render_scorecard(record, report), "", *render_scores(record, cells))
            emit_annotations(report)

            result_path = Path(os.getenv("EVAL_RESULT_PATH", "eval-result.json"))
            result_path.write_text(json.dumps(compact_result(record, report), indent=1) + "\n")
            _write_action_output("result-path", str(result_path))

            if gate_path.is_file():
                resp["seat"] = scored["seat"]
                resp["eval_version"] = scored["eval_version"]
                errs = gate_errors(resp, cells, gate)
                if errs:
                    summary("### Gate", *(f"- {e}" for e in errs))
                    if os.getenv("EVAL_ENFORCE", "false").lower() == "true":
                        print("::error::eval gate failed — see summary")
                        return 1
                    print("::warning::eval gate is informational — see summary")
                    return 0
                summary("", "Gate: **clean** vs baseline "
                        f"`{calib_str(gate['calibration'])}`")
            return 0

        if status == "failed":
            summary("### Eval run failed",
                    "```json", json.dumps(record, indent=2), "```")
            print("::error::eval run failed — see summary")
            return 1

        time.sleep(POLL_SECONDS)

    print(f"::error::run not terminal after {POLL_LIMIT * POLL_SECONDS // 60} "
          "minutes — the request record is durable; the next submission "
          "drains it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
