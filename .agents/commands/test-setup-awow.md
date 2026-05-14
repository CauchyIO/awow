---
phase: maintenance
prerequisites: []
removes_pain: "wording-change-broke-the-wizard regressions caught only by manual walkthrough"
---

# /test-setup-awow [<scenario>] — execute the regression suite

> **Maintainer-only command.** Part of awow's own regression suite. If you templated this repo and are not maintaining awow itself, delete this file and the `tests/` directory.

You will execute `/setup-awow` scenarios against fresh scratch workspaces with scripted user replies, then grade. The biggest failure mode of this command is that you may try to short-circuit Phase 2 (wizard execution) by self-attesting what the wizard would have done. The structural rules below prevent that — follow them literally, even when they feel redundant.

## Discover scenarios

If the user named a scenario, run only that one. Otherwise list every `<name>` that has both `tests/setup-awow/scripts/<name>.txt` and `tests/setup-awow/rubrics/<name>.md`, and run them in alphabetical order.

## Per scenario — six phases, in order

Each phase begins with a literal marker line you must print. Phase 5 self-checks for the presence of Phase 2's output markers; if they are missing, the run for that scenario is aborted and recorded as such. Do not skip phases.

### Phase 1 — Scratch setup

Print exactly: `=== Scenario: <name> | Phase 1: scratch setup ===`

```bash
SCRATCH=/tmp/awow-test-<scenario>-<UTC-timestamp>
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
cp -R tests/setup-awow/fixtures/<scenario>/. "$SCRATCH/"
```

Confirm via `ls -la "$SCRATCH"` that the fixture's contents are present.

### Phase 2 — Wizard execution (visible, MANDATORY)

Print exactly: `=== Phase 2: wizard run begins ===`

1. **Read the wizard prompt:** `Read .agents/commands/setup-awow.md`. Then print one confirmation line of the form:
   ```
   (setup-awow.md read — first heading: <copy the first ## heading verbatim>)
   ```
   This is your proof to the self-check in Phase 5 that the prompt was actually loaded.

2. **Read the script:** `Read tests/setup-awow/scripts/<scenario>.txt`. Strip comment lines (starting with `#`) and blank lines. The remaining lines are the script.

3. **Execute the wizard against `$SCRATCH`.** Apply `--root $SCRATCH` discipline: every wizard-directed tool call uses an absolute path under `$SCRATCH`. Make real `Read`, `Write`, `Bash` calls.

   For every wizard "ask the user" point, your visible response must contain exactly this structure — not your internal reasoning, your visible output:

   ```
   --- WIZARD TURN <N> ---
   <the wizard's response — the message it would say to the user — produced verbatim, in full, including any plan listings, status markers, questions, and instructions>
   --- END TURN <N> ---

   >>> Script line <K>: <reply, as taken from the script>
   ```

   If you find yourself wanting to skip a `--- WIZARD TURN ---` block because you "know what the wizard would do," **stop and re-read the previous paragraph.** The block is mandatory. Phase 5 will refuse to write a normal run file if no block exists for this scenario.

   Walk until the script is exhausted or the wizard reaches a natural stop (e.g. user declined installer; Step 0 cannot proceed). Do not improvise replies beyond the script.

4. Print exactly: `=== Phase 2: wizard run complete (<count> WIZARD TURN blocks produced) ===` — where `<count>` is the number of `--- WIZARD TURN <N> ---` blocks you actually emitted above.

### Phase 3 — State inspection

Print exactly: `=== Phase 3: post-run state ===`

```bash
ls -laR "$SCRATCH" | head -60
```

This is the ground truth for state assertions in Phase 4.

### Phase 4 — Grade

Print exactly: `=== Phase 4: grading ===`

`Read tests/setup-awow/rubrics/<scenario>.md`. For each question, classify the evidence source:

- **Behavioural** — cite a specific `--- WIZARD TURN <N> ---` block from Phase 2.
- **Tool-call** — cite a specific tool call from your history this turn.
- **State** — cite a specific line from the Phase 3 `ls` output (or a follow-up `Read` of a specific file).

Answer **yes** / **no** / **n/a** with one sentence of evidence. Do not be charitable. If the rubric specifies 10 and your Phase 2 block listed 9, answer **no** with the count.

### Phase 5 — Self-check, then write run file

Print exactly: `=== Phase 5: self-check ===`

Count the `--- WIZARD TURN <N> ---` blocks you produced in Phase 2 for this scenario. Print the count.

- **If the count is 0** (or you cannot find the Phase 2 marker line): the wizard was not actually executed. Write `/tmp/awow-test-runs/<scenario>-<UTC-timestamp>.json` with:
  ```json
  {
    "scenario": "<name>",
    "timestamp": "<ISO 8601 UTC>",
    "scratch": "<path>",
    "status": "ABORTED — no WIZARD TURN blocks detected in Phase 2",
    "rubric": []
  }
  ```
  Print: `ABORTED — Phase 2 produced no wizard execution.` Skip to Phase 6.

- **Otherwise:** write the normal run file at `/tmp/awow-test-runs/<scenario>-<UTC-timestamp>.json`:
  ```json
  {
    "scenario": "<name>",
    "timestamp": "<ISO 8601 UTC>",
    "scratch": "<path>",
    "wizard_turns": <count>,
    "walked_to": "<short label>",
    "status": "OK",
    "rubric": [
      {"q": 1, "invariant": <n>, "answer": "yes|no|n/a", "evidence": "<one sentence>"}
    ]
  }
  ```

Create `/tmp/awow-test-runs/` if it does not exist. Print the file path.

### Phase 6 — Cleanup

Print exactly: `=== Phase 6: cleanup ===`

```bash
rm -rf "$SCRATCH"
```

Skip the `rm` if the user passed `--keep`.

## Final summary

After all scenarios, print:

```
<scenario>: walked to <X>; <Y> yes / <Z> no / <W> n/a → <PASS|FAIL|ABORTED>
```

`PASS` = zero `no` and `status == OK`. `FAIL` = at least one `no`. `ABORTED` = Phase 2 produced no wizard execution. End with `OVERALL: <P>/<N> scenarios pass`.

## Discipline

- Every `=== Phase N ===` marker is required. The Phase 5 self-check depends on them.
- Every wizard "ask the user" point gets a `--- WIZARD TURN <N> ---` block in your visible output, not just in your reasoning. Phase 5 refuses to write a normal run file if none are present.
- The wizard's response inside a WIZARD TURN block must be the **actual response** — full plan listings, full questions, full instructions — not a summary like "[wizard lists steps]".
- Use absolute `$SCRATCH/...` paths for every wizard-directed tool call. Never write to `/Users/casper/repos/awow/` by accident.
- Finish each scenario fully (through Phase 6) before starting the next. No state bleed.
- The rubric answers must be evidenced by what you actually produced or observed this turn — not by what you "know would happen."
