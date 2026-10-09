"""Regression test for /process-workitem's requested depth (CAU-1636).

The command does as much as was asked, no more: "explain PAY-42" reads and
changes nothing, "implement PAY-42" runs the whole flow. The prompt carries that
as a depth table in front of the flow. This test keeps the table and the flow
telling the same story, because they are edited separately. Asserts:

  1. The depth section sits before the flow, so it is settled before step 1.
  2. The table has the four depths, in order of reach, and `explain` may write
     nothing.
  3. Each depth's step range matches the flow's real headings: `explain` stops
     after Load, `plan` ends on the Plan step, `implement` ends on the flow's
     last step — read from the headings, so a new step that the table does not
     cover fails here.
  4. A bare ID is never read as `implement`, and only the user deepens a run.
  5. Delivering code passes an explicit Review step between Verify and Report,
     the report carries its record, and `not reviewed` is the honest fallback.
  6. The archetype handlers' "`process-workitem` step N" still points at Verify.
  7. The picker description offers the shallow depths, not only the PR.

Pure stdlib; no pytest, no network.

Run:  python3 tests/process-depth/test_depth.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMANDS = REPO_ROOT / ".agents" / "commands"
PROMPT = COMMANDS / "process-workitem.md"
FAILURES: list[str] = []

DEPTHS = ["explain", "refine", "plan", "implement"]


def flow_steps(text: str) -> dict[str, str]:
    """`### 2a. Refine — …` → {"2a": "Refine — …"}, in file order."""
    return dict(re.findall(r"^### (\d+[a-z]?)\. (.+)$", text, flags=re.M))


def depth_rows(section: str) -> dict[str, dict[str, str]]:
    rows = {}
    for line in section.split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.fullmatch(r"`[a-z]+`", cells[1]):
            rows[cells[1].strip("`")] = {"steps": cells[2], "writes": cells[3]}
    return rows


def last_whole_step(cell: str) -> str:
    """The last whole-numbered step a 'Steps you run' cell reaches: '1–4' → '4'."""
    return re.findall(r"\d+", cell.split(",")[0])[-1]


def main() -> int:
    text = PROMPT.read_text()
    steps = flow_steps(text)

    depth_at, flow_at = text.find("\n## Depth"), text.find("\n## Flow")
    if depth_at == -1 or flow_at == -1 or depth_at > flow_at:
        FAILURES.append("the depth section is missing or comes after the flow")
        return report()
    section = text[depth_at:flow_at]
    rows = depth_rows(section)

    if list(rows) != DEPTHS:
        FAILURES.append(f"depth table lists {list(rows)}, expected {DEPTHS}")
        return report()
    if not rows["plan"]["writes"].endswith("and nothing else"):
        FAILURES.append(f"`plan` may write {rows['plan']['writes']!r} — the plan file and nothing else")
    if "write it without asking first, and never leave the plan in chat only" not in text:
        FAILURES.append("plan depth may leave the plan in chat instead of writing the plan file")
    hint = re.search(r'^argument-hint:\s*"([^"]*)"', text, flags=re.M)
    if not hint or not all(d in hint.group(1) for d in DEPTHS):
        FAILURES.append("the argument-hint does not show the item ID and the four depths")
    if "naming the four in one line" not in text:
        FAILURES.append("a bare ID gets a depth question that does not name the depths")
    if "approval writes nothing to the board" not in text:
        FAILURES.append("the plan approval does not say what approving does")
    if "Write the stub only on the user's yes" not in text:
        FAILURES.append("an archetype stub is written without the user's yes")
    if rows["explain"]["writes"] != "nothing":
        FAILURES.append(f"`explain` may write {rows['explain']['writes']!r} — it must write nothing")

    whole = [n for n in steps if n.isdigit()]
    expected_end = {
        "explain": next((n for n in whole if steps[n].startswith("Load")), None),
        "plan": next((n for n in whole if steps[n].startswith("Plan")), None),
        "implement": whole[-1] if whole else None,
    }
    for depth, want in expected_end.items():
        got = last_whole_step(rows[depth]["steps"])
        if want is None:
            FAILURES.append(f"the flow has no step for `{depth}` to end on")
        elif got != want:
            FAILURES.append(
                f"`{depth}` runs to step {got}, but the flow says it should end on "
                f"step {want} ({steps[want]})"
            )
    refine_end = last_whole_step(rows["refine"]["steps"])
    validate = next((n for n in whole if steps[n].startswith("Validate")), None)
    if validate is None or int(refine_end) >= int(validate):
        FAILURES.append("`refine` runs into validation or beyond — it stops before it")
    if "2a" not in rows["refine"]["steps"] or not steps.get("2a", "").startswith("Refine"):
        FAILURES.append("`refine` does not route to a Refine step 2a")
    if "`workitem-write`" not in rows["refine"]["writes"]:
        FAILURES.append("`refine` writes the board without naming the `workitem-write` skill")

    for rule in ("Never read a bare ID as `implement`", "Go deeper only on the user's word",
                 "`explain` changes nothing"):
        if rule not in section:
            FAILURES.append(f"the depth section has lost the rule: {rule!r}")
    plan_body = text[text.find("### 4. Plan"): text.find("### 5.")]
    if "At `plan` depth" not in plan_body or "stop here" not in plan_body:
        FAILURES.append("the Plan step does not tell a `plan`-depth run to stop")

    names = [steps[n].split(" ")[0] for n in whole]
    if "Review" not in names or not (
        names.index("Verify") < names.index("Review") < names.index("Report")
    ):
        FAILURES.append(f"no Review step between Verify and Report — flow is {names}")
    else:
        review_n = whole[names.index("Review")]
        report_body = text[text.find(f"### {whole[names.index('Report')]}. "):]
        if f"step {review_n}" not in report_body.split("\n---")[0]:
            FAILURES.append("the Report step does not carry the review record into the PR")
        review_body = text[text.find(f"### {review_n}. "): text.find(f"### {whole[names.index('Report')]}. ")]
        if "`not reviewed`" not in review_body:
            FAILURES.append("the Review step has no honest fallback (`not reviewed`) when no review ran")

    for handler in sorted((COMMANDS / "_workitem-archetypes").glob("*.md")):
        for n in re.findall(r"`process-workitem` step (\d+)", handler.read_text()):
            if not steps.get(n, "").startswith("Verify"):
                FAILURES.append(
                    f"{handler.relative_to(REPO_ROOT)} cites process-workitem step {n} as "
                    f"verification, but step {n} is {steps.get(n, 'missing')!r}"
                )

    description = re.search(r'^description: "(.+)"$', text, flags=re.M)
    if not description or not all(w in description.group(1) for w in ("explained", "refined", "planned")):
        FAILURES.append("the picker description does not offer the explain / refine / plan depths")

    return report()


def report() -> int:
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Process-workitem depth OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
