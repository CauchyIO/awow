"""/awow-help is the fifth core command (CAU-1644).

It explains what awow can do in this repo and suggests one next step, from
the repo's real state, reading the generated catalog. Static assertions over
the prompt and its wiring:

  1. It ships in core (no channel), with a single-line description.
  2. It reads the catalog by its payload path and says the catalog is the
     only source of command names.
  3. It is read-only and asks nothing: the prompt forbids every write, and
     never depends on setup-progress.md.
  4. It reads state before suggesting: installed capabilities, configuration,
     board state through the board-target skill.
  5. It suggests exactly one next step.
  6. The answer opens with its heading, the next step directly under it.
  7. The reflex routes to it, the catalog lists it under awow, and
     /setup-awow's closing line names it.

Pure stdlib; no pytest, no network.

Run:  python3 tests/awow-help/test_awow_help.py
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
gather = importlib.import_module("gather")

PROMPT = REPO_ROOT / ".agents" / "commands" / "awow-help.md"
FAILURES: list[str] = []


def need(cond: bool, message: str) -> None:
    if not cond:
        FAILURES.append(message)


def main() -> int:
    text = PROMPT.read_text()
    fields, body = gather.parse_frontmatter(text, PROMPT)

    need(gather.ships_in(text, "both") and not gather.is_workflows_channel(text),
         "awow-help does not ship in core")
    desc = fields.get("description", "")
    need(bool(desc) and not desc.startswith((">", "|")), "awow-help has no single-line description")

    need("{AWOW_ROOT}/context/tooling/command-catalog.md" in body, "the prompt does not read the catalog by its payload path")
    need("only source of command names" in body, "the prompt does not make the catalog the only source of command names")

    need("never write" in body.lower() and "Write no file" in body and "make no board write" in body,
         "the prompt does not forbid writes")
    need("install nothing" in body.lower() and "ask" in body.lower() and "never write, install, register or ask" in body,
         "the prompt does not forbid installing or asking")
    need("Ignore `setup-progress.md`" in body, "the prompt does not tell the agent to ignore setup-progress.md")
    for line in body.split("\n"):
        if re.search(r"[Rr]ead `?setup-progress", line):
            FAILURES.append(f"the prompt depends on setup-progress.md: {line.strip()[:80]}")

    for signal in ("skill listing", "board.md", "`board-target` skill", "identity-bearing read", "assigned to the current user"):
        need(signal in body, f"the prompt does not read state through {signal!r}")
    need("## 4. Suggest exactly one next step" in body, "the prompt does not suggest exactly one next step")
    need("--commands" in fields.get("argument-hint", "") and "Without `--commands`" in body and "No table." in body,
         "the full command table is not behind --commands")
    output = body[body.index("## Output"):]
    need("# awow in <repo name>" in output, "the heading is not 'awow in <repo name>'")
    need(0 < output.find("**Next:**") < output.find("## Commands — `awow`"),
         "the next step does not come before the command tables")
    need("**Problems:**" in output, "the default answer has no Problems line")
    # The Codex dry run (CAU-1648): heading first, Next directly under it, on every harness.
    template = output[output.index("```markdown"):]
    need("that line carries one invocation" in body, "the Next line may carry two invocations")
    need("show no table for it" in body, "an uninstalled awow-workflows may still get a full table")
    need("always, on every harness" in output, "the prompt does not require the heading on every harness")
    need(template.find("# awow in <repo name>") < template.find("**Next:**") < template.find("**Problems:**"),
         "the template does not put the heading first and Next directly under it")
    need(re.search(r"^7\. ", body, flags=re.M) is not None, "the next-step ladder is incomplete")

    # Every awow-workflows command named in the prompt is named with its plugin.
    bundle = {p.stem for p in (REPO_ROOT / ".agents" / "commands").glob("*.md")
              if p.name != "README.md" and gather.is_workflows_channel(p.read_text())}
    for n, line in enumerate(text.split("\n"), 1):
        hits = [c for c in bundle if f"/{c}" in line]
        if hits and "awow-workflows" not in line:
            FAILURES.append(f"awow-help.md:{n} names {hits} without its plugin")

    reflex = (REPO_ROOT / ".agents" / "skills" / "using-awow" / "SKILL.md").read_text()
    need("`/awow-help`" in reflex[reflex.index("## Route to the moment"):], "the reflex does not route to /awow-help")
    catalog = (REPO_ROOT / "context" / "tooling" / "command-catalog.md").read_text()
    core = catalog[catalog.index("### `awow`"): catalog.index("### `awow-workflows`")]
    need("| `/awow-help" in core, "the catalog does not list /awow-help under awow")
    setup = (REPO_ROOT / ".agents" / "commands" / "setup-awow.md").read_text()
    need("/awow-help" in setup[setup.index("## Closing line"):], "/setup-awow's closing line does not name /awow-help")

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("awow-help OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
