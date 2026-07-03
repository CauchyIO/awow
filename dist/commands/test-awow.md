---
description: "execute an eval suite"
phase: maintenance
prerequisites: []
removes_pain: "wording-change-broke-the-prompt regressions caught only by manual walkthrough; grading noise from self-attestation and broken fixtures"
---

# /test-awow [<suite>] [<scenario>] [--keep] — execute an eval suite

> **Maintainer-only command.** Part of awow's own regression suite. If you templated this repo and are not maintaining awow itself, delete this file and the `tests/` directory.

You will execute a command prompt against fresh scratch workspaces with scripted user replies, then compose a verdict from two independent witnesses: deterministic checks (`tests/run-checks.sh`) and a grading pass that never sees your execution reasoning. The biggest failure mode of this command is that you may try to short-circuit Phase 3 (command execution) by self-attesting what the command would have done. The structural rules below prevent that — follow them literally, even when they feel redundant.

## Discover suites and scenarios

A suite is a directory `tests/<suite>/` containing a `suite.md` whose frontmatter names the `command:` under test. If the user named a suite, use it; if exactly one suite exists, use that; otherwise list the suites and stop for the user to pick.

Within the suite: if the user named a scenario, run only that one. Otherwise list every `<name>` that has both `tests/<suite>/scripts/<name>.txt` and `tests/<suite>/rubrics/<name>.md`, and run them in alphabetical order.

## Per scenario — eight phases, in order

Each phase begins with a literal marker line you must print. Phase 7 self-checks for the presence of Phase 3's output markers; if they are missing, the run is composed as `indeterminate`, not graded. Do not skip phases.

### Phase 1 — Scratch setup

Print exactly: `=== Scenario: <name> | Phase 1: scratch setup ===`

```bash
SCRATCH=/tmp/awow-test-<suite>-<scenario>-<UTC-timestamp>
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
cp -R tests/<suite>/fixtures/<scenario>/. "$SCRATCH/"
```

Confirm via `ls -la "$SCRATCH"` that the fixture's contents are present.

If `tests/<suite>/setup/<scenario>.sh` exists, run it as `tests/<suite>/setup/<scenario>.sh "$SCRATCH"` — it finishes the fixture build (e.g. re-dating a frozen activity snapshot to today). A non-zero exit means the fixture could not be built: set `final: indeterminate`, `stage: setup`, and skip to Phase 7.

### Phase 2 — Pre-checks (fixture gate)

Print exactly: `=== Phase 2: pre-checks ===`

```bash
tests/run-checks.sh <suite> <scenario> pre "$SCRATCH"
```

Record the exit code and the `CHECK` lines verbatim.

- **Exit 0** — fixture intact; continue to Phase 3.
- **Exit 1** — the fixture does not match its declared starting state. The run cannot be graded: set `final: indeterminate`, `stage: pre-checks`, and skip directly to Phase 7. Do not run the command against a broken fixture.
- **Exit 127** — the check itself is broken (missing file, undefined `pre()`). Set `final: indeterminate`, `stage: checks-broken`, and skip to Phase 7.

### Phase 3 — Command execution (visible, MANDATORY)

Print exactly: `=== Phase 3: command run begins ===`

1. **Resolve the command under test:** read `tests/<suite>/suite.md` frontmatter → `command: <name>`. Then `Read .agents/commands/<name>.md` and print one confirmation line of the form:
   ```
   (<name>.md read — first heading: <copy the first ## heading verbatim>)
   ```
   This is your proof to the self-check in Phase 7 that the prompt was actually loaded.

2. **Read the script:** `Read tests/<suite>/scripts/<scenario>.txt`. Strip comment lines (starting with `#`) and blank lines. The remaining lines are the script.

3. **Execute the command against `$SCRATCH`.** Apply `--root $SCRATCH` discipline: every command-directed tool call uses an absolute path under `$SCRATCH`. Make real `Read`, `Write`, `Bash` calls.

   For every "ask the user" point, your visible response must contain exactly this structure — not your internal reasoning, your visible output:

   ```
   --- AGENT TURN <N> ---
   <the command's response — the message it would say to the user — produced verbatim, in full, including any plan listings, status markers, questions, and instructions>
   --- END TURN <N> ---

   >>> Script line <K>: <reply, as taken from the script>
   ```

   If you find yourself wanting to skip an `--- AGENT TURN ---` block because you "know what the command would do," **stop and re-read the previous paragraph.** The block is mandatory. Phase 7 composes an `indeterminate` verdict if no block exists for this scenario.

   Walk until the script is exhausted or the command reaches a natural stop (e.g. user declined a gate). Do not improvise replies beyond the script.

4. Print exactly: `=== Phase 3: command run complete (<count> AGENT TURN blocks produced) ===` — where `<count>` is the number of `--- AGENT TURN <N> ---` blocks you actually emitted above.

### Phase 4 — State inspection

Print exactly: `=== Phase 4: post-run state ===`

```bash
ls -laR "$SCRATCH" | head -60
```

This is the ground truth for state assertions in Phases 5 and 6.

### Phase 5 — Post-checks (deterministic witness)

Print exactly: `=== Phase 5: post-checks ===`

```bash
tests/run-checks.sh <suite> <scenario> post "$SCRATCH"
```

Record the exit code and the `CHECK` lines verbatim. Exit 127 means the check is broken: note `stage: checks-broken` for Phase 7. Do not re-run, patch, or reinterpret a failing check — its verdict stands as recorded.

### Phase 6 — Blind grading (judged witness)

Print exactly: `=== Phase 6: blind grading ===`

Assemble an evidence bundle at `/tmp/awow-test-runs/<suite>-<scenario>-<ts>-evidence.md` containing, in this order:

1. `## Rubric` — the full text of `tests/<suite>/rubrics/<scenario>.md`.
2. `## Agent turns` — every `--- AGENT TURN <N> ---` block from Phase 3, verbatim.
3. `## Tool calls` — one line per tool call you made during Phase 3 (`Bash: <command>`, `Write: <path>`, `Read: <path>`).
4. `## Post-run state` — the Phase 4 listing.

The bundle must **not** contain the Phase 2/5 check results — the two witnesses stay independent.

Dispatch a subagent whose entire input is that bundle, with these instructions: "Grade each rubric question **yes** / **no** / **n/a** using only the evidence in this bundle. Cite one sentence of evidence per answer — an AGENT TURN block, a tool-call line, or a state line. Do not be charitable: if the rubric specifies 10 and the plan listing shows 9, answer no with the count. Return strict JSON: `[{\"q\": 1, \"invariant\": <n or null>, \"answer\": \"yes|no|n/a\", \"evidence\": \"...\"}]`."

If your harness cannot dispatch subagents, grade the bundle yourself under the same instructions and record `"judge_mode": "inline"` in the run file; otherwise record `"judge_mode": "subagent"`. If the judge returns unparsable output, retry once; if it fails again, note `stage: judge` for Phase 7.

### Phase 7 — Compose verdict, write run file

Print exactly: `=== Phase 7: compose ===`

Count the `--- AGENT TURN <N> ---` blocks you produced in Phase 3 and print the count. Then resolve `final` by the first matching rule — this order is load-bearing:

1. The Phase 1 setup hook exited non-zero → `indeterminate`, `stage: setup`.
2. Phase 2 exited 1 → `indeterminate`, `stage: pre-checks`.
3. Phase 2 or Phase 5 exited 127 → `indeterminate`, `stage: checks-broken`.
4. AGENT TURN count is 0 (or the Phase 3 markers are missing) → `indeterminate`, `stage: execution`.
5. No parsable judge verdict → `indeterminate`, `stage: judge`.
6. Judge has zero `no` AND Phase 5 exited 0 → `pass`.
7. Otherwise → `fail`.

An `indeterminate` is not a graded failure — it means this run could not measure the prompt. Never soften a rule-6 `fail` into `indeterminate` because the failure "looks environmental"; that reclassification is the maintainer's, made from the run file.

For every rubric question that mirrors a deterministic check, compare the two witnesses: any disagreement (judge `yes` but check failed, or judge `no` but check passed) goes into a `triage` list — one line naming the question, the check, and both answers.

Write `/tmp/awow-test-runs/<suite>-<scenario>-<UTC-timestamp>.json` (create the directory if needed):

```json
{
  "schema": 2,
  "suite": "<suite>",
  "scenario": "<name>",
  "timestamp": "<ISO 8601 UTC>",
  "scratch": "<path>",
  "agent_turns": <count>,
  "walked_to": "<short label>",
  "final": "pass|fail|indeterminate",
  "stage": null,
  "judge_mode": "subagent|inline",
  "checks": {
    "pre":  {"exit": 0, "records": ["CHECK\tpass\tfile-absent setup-progress.md"]},
    "post": {"exit": 0, "records": []}
  },
  "rubric": [{"q": 1, "invariant": 2, "answer": "yes", "evidence": "<one sentence>"}],
  "triage": []
}
```

`stage` is null on `pass`/`fail`; on `indeterminate` it names the rule that fired. On an `indeterminate` composed before Phase 3 ran, write the run file with `agent_turns: 0`, an empty `rubric`, and whatever check records exist. Print the file path.

### Phase 8 — Cleanup

Print exactly: `=== Phase 8: cleanup ===`

```bash
rm -rf "$SCRATCH"
```

Skip the `rm` if the user passed `--keep`.

## Final summary

After all scenarios, print one line each:

```
<scenario>: walked to <X>; checks <passed>/<total>; rubric <Y> yes / <Z> no / <W> n/a → <PASS|FAIL|INDETERMINATE(stage)>
```

End with `OVERALL: <P> pass / <F> fail / <I> indeterminate of <N> scenarios`. If any `triage` list is non-empty, print `TRIAGE:` followed by each entry — witness disagreement is a signal that either a rubric question, a check, or the prompt drifted.

## Discipline

- Every `=== Phase N ===` marker is required. The Phase 7 self-check depends on them.
- Every "ask the user" point gets an `--- AGENT TURN <N> ---` block in your visible output, not just in your reasoning. Phase 7 composes `indeterminate` if none are present.
- The response inside an AGENT TURN block must be the **actual response** — full plan listings, full questions, full instructions — not a summary like "[wizard lists steps]".
- Use absolute `$SCRATCH/...` paths for every command-directed tool call. Never write to the repo checkout by accident.
- Run the check driver exactly as written; never assert a check's outcome yourself, and never edit a checks file mid-run.
- Finish each scenario fully (through Phase 8) before starting the next. No state bleed.
- The evidence bundle is the judge's entire world: if something belongs in the grading, it must be in the bundle, produced during this run — not from what you "know would happen."
