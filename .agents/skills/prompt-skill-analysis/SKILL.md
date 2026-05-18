---
name: prompt-skill-analysis
description: "Assess prompt-engineering quality from a Claude Code session and write a markdown report. Use when the user asks for a prompt-skill review, prompting feedback, prompt-quality assessment, or wants to evaluate how well they (or someone else) prompt Claude Code. Accepts either a raw Claude Code session JSONL file (e.g. `~/.claude/projects/<id>/<session>.jsonl`) or an `mlflow_export` directory produced by the mlflow-export skill. Auto-detects single-session vs multi-session input."
---

# Prompt-Skill Analysis

> **Starter shape — adjust for your harness.** This skill ships supporting two input shapes: raw **Claude Code** session JSONL and the JSON layout produced by the bundled `mlflow-export` skill. Teams running primarily on GitHub Copilot, Cursor, or another harness should extend `scripts/extract_prompts.py` with a reader for their session format during `/setup-awow` Step 8 (Skills review). The report rubric below is harness-agnostic — only the input parsing is tied to a specific shape.

Reads an agent session (or batch of sessions) and produces an honest, evidence-backed markdown assessment of how the user prompts: clarity, specificity, structure, iteration patterns, voice, and concrete suggestions for improvement.

The skill has two parts:
1. A small Python script (`scripts/extract_prompts.py`) that normalizes the input and computes objective stats.
2. Instructions in this file telling the agent how to read the resulting JSON and turn it into a report.

The qualitative judgment lives in the agent. The script only counts and extracts — never grades.

## Inputs to collect from the user

- **Input path** — required. One of:
  - A raw Claude Code session JSONL file (the kind written under `~/.claude/projects/<dir>/<session-id>.jsonl`).
  - An `mlflow_export` directory produced by the `mlflow-export` skill (must contain `traces.jsonl`).
  - (Custom) A reader your team has added for another harness — extend `extract_prompts.py` with a `--input-format <name>` branch and document it in this section.
- **Output path for the report** — optional. Defaults to `<input-dir>/prompt_skill_report.md`.
- **Subject identity** — who the prompts belong to (e.g. "the user themselves", "a teammate named X"). Affects tone of the report. If unclear, ask, or default to "the user".
- **Comparison baseline** — optional. If the user wants a side-by-side, ask for a second input path and run the extractor twice.

If the input path is missing and not obvious from context, ask before running.

## Run the extractor

The script is plain stdlib Python, so any modern interpreter works.

```bash
python3 .agents/skills/prompt-skill-analysis/scripts/extract_prompts.py \
    --input <path-to-jsonl-or-mlflow_export-dir> \
    --out  <path-to-analysis.json>
```

It writes a single JSON file with this shape:

```
{
  "input_type": "raw_jsonl" | "mlflow_export",
  "aggregate_stats": { prompt-length distribution, share metrics, top first-words, tool-use counts, gap stats, token stats, session size distribution },
  "per_session_stats": [ {session_id, n_prompts, share_questions, share_corrections, share_imperative, ...}, ... ],
  "sessions": [ {session_id, working_directory, git_branch, prompts: [ {i, ts, text, response_excerpt, tools, tokens}, ... ] }, ... ]
}
```

The script also prints a short summary to stdout. Read the JSON file with `Read` (it can be large for big exports — read in chunks if needed).

## Writing the report

Save the report to `prompt_skill_report.md` (or wherever the user asked). Follow this rubric.

### Required sections

1. **Header** — input path, input type, total sessions, total prompts, date range, primary working directories.
2. **Snapshot table** — quantitative summary: median prompt length, p25/p75/max, share questions / imperatives / corrections / ticket refs / file refs / polite / emphatic, median inter-prompt gap, top tool calls. Pull these from `aggregate_stats`.
3. **What stands out** — 3-6 distinctive patterns, each with a short evidence quote (5-15 words pulled verbatim from `sessions[*].prompts[*].text`). Quote real prompts, never paraphrase. Anonymize personal data only if the user asks.
4. **Strengths** — what the user does well, with examples.
5. **Weaknesses** — honest, specific, with examples. Don't soften because the data belongs to the user — soft feedback is useless feedback.
6. **Per-session highlights** (only if input has more than 3 sessions) — name 2-3 sessions that are representative or interesting (longest, most corrections, highest token spend) and characterize them in 1-2 sentences each.
7. **Suggestions** — exactly 3-5 concrete, copy-pasteable changes. For each: a "Now" example pulled from the prompts and a "Better" rewrite. Tie each suggestion to a stat or pattern from earlier in the report.
8. **Verdict** — one paragraph. Where this prompter is strong, where they're weak, what kind of work they're best/worst suited to. Avoid "B+" or numeric grades — describe the shape instead.

### Quality bar

- **Quote real prompts.** Every claim about style needs at least one short verbatim snippet. If a behavior happens once, say "once"; if it happens often, give the percentage from `share`.
- **No invented stats.** Every number comes from `aggregate_stats` or `per_session_stats`. Don't make up percentages.
- **Don't conflate prompts with spans.** A user who never names files in prompts but lets Claude fetch them via tools is a different shape than one who is genuinely flying blind. The `tool_use_top15` stat helps distinguish — call this out when relevant.
- **Don't lecture.** Suggestions should read like a peer's feedback, not a style guide. 3-5 items, no more.
- **Calibrate to scope.** If there are <10 prompts, lean qualitative. If there are >100, lean on the distribution stats and pick representative samples.

### Comparison mode (optional)

If the user provided a second input as a baseline:
- Run the extractor twice with different `--out` paths.
- Read both JSONs.
- Produce a single report with a side-by-side table on the snapshot stats and a "where they differ" section. Otherwise follow the same rubric.

## Heuristics for interpretation

These are honest patterns — apply them, but verify in the actual prompts before claiming them.

- **High `share.questions` (>30%) + low `share.imperative_openers` (<10%)** → user delegates decisions to Claude rather than directing it. Often correlates with familiar-domain work where the user is exploring.
- **High `share.correction_markers` (>10%)** → user iterates rather than specifying upfront. Sometimes a feature (cheap to redirect Claude), sometimes a bug (specs were ambiguous).
- **High `share.ticket_refs` + low `share.file_refs` + frequent Linear/Jira tool calls** → user plans externally and references the artifact. This is fine; flag it as a *style* rather than a weakness.
- **Very low median word count (<15) with low corrections** → either a domain expert with high context-density (good) or someone shipping under-specified prompts that Claude happens to handle (risky).
- **Long inter-prompt gaps (>5 min median)** → user is working in parallel with Claude rather than babysitting. Different shape than rapid-fire (<1 min) which is conversational/exploratory.
- **`first_words_top10` dominated by openers like "can", "is", "what"** → question-heavy. Dominated by "create", "build", "fix", "run" → directive.

## After writing the report

Print a 3-bullet summary to the user:
- Path to the saved report.
- The single biggest strength.
- The single biggest improvement opportunity.

Don't restate the whole report in chat. The file is the deliverable.

## Troubleshooting

- **Input is JSONL but parsing returns 0 prompts** — check the file isn't an MLflow trace dump. MLflow traces have `info`/`request`/`response`/`spans` per line; raw Claude Code sessions have `type`/`message`/`uuid` per line. The script auto-detects by file vs directory; pass an `mlflow_export` *directory* (containing `traces.jsonl`) for MLflow.
- **JSON is too large to read in one Read** — read with `offset`/`limit` and skim `aggregate_stats` first; sample `sessions[*].prompts[*].text` selectively rather than dumping all of them.
- **User asks for a different output format** — the JSON is the single source of truth; another report shape is a templating change, not a re-extraction. Adapt the report directly.
