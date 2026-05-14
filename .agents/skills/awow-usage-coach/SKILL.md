---
name: awow-usage-coach
description: "Analyse how a team or an individual works through agent sessions in the awow repo (or a sibling repo as stand-in) and produce one of two markdown reports: (a) team-nudge — proposed additions to .agents/CLAUDE.md / copilot-instructions based on recurring sequence + editing patterns, or (b) self-coach — imperative, encouraging coaching for one developer compared against the team baseline. Uses an intent taxonomy (investigate/plan/propose/implement/refine/verify/document/inform) plus files-modified analysis so it works regardless of whether the team uses awow's exact vocabulary. Use when the user asks for awow usage feedback, adoption review, nudges for CLAUDE.md, or wants to see how they're using the project vs. teammates. Input: an mlflow_export directory (or equivalent — see below)."
---

# awow Usage Coach

> **Starter shape — adjust for your harness and backend.** This skill ships expecting input in the shape produced by the bundled `mlflow-export` skill (Databricks MLflow). Teams on a different harness or tracing backend should either (a) emit the same JSON layout from their backend, or (b) extend `scripts/awow_extract.py` to read their format. The analysis itself — intent taxonomy, sequence patterns, edit footprint — is harness-agnostic and built around `working_directory`, `files_modified`, prompt text, and per-prompt timestamps. Adjust the script's input parser; leave the rubric alone unless the team genuinely wants a different report shape. Customisation lands during `/setup-awow` Step 9 (Skills review).

Reads sessions captured in an `mlflow_export/` directory (or equivalent), filters to the target repo, and produces one of two markdown reports.

The qualitative judgment lives in this skill's instructions, not in the extractor. The script (`scripts/awow_extract.py`) only counts and extracts — it never grades.

## What the skill measures

Three lenses, in priority order:

1. **Intent shape** — every prompt is classified into one of eight labels (`investigate`, `plan`, `propose`, `implement`, `refine`, `verify`, `document`, `inform`, or `other`). Vocabulary-agnostic — works whether or not the team uses awow's slash commands.
2. **Sequence patterns** — bigrams and trigrams of intent transitions per session surface the working rhythm (`investigate→implement→verify`, `propose→implement→refine`, etc.). In self-coach mode, subject vs. team bigrams reveal where rhythms differ.
3. **Edit patterns** — each trace carries a `files.modified` tag. The extractor buckets touched files by location/type (`proposal`, `context`, `agents-config`, `code`, `config`, `markdown`, `data`, `script`, `other`) and crosses this with intent so the report can say things like *"when teammates 'propose', 70% of touched files are .md; when you 'propose', 30% are .md and 50% are code"*.

Awow-specific vocabulary signals (slash commands, proposal-first paths, placement decision tree) are kept as a **secondary lens** — surfaced when present, but never required for a useful report.

## Inputs to collect

- **`--input`** — required. Path to an `mlflow_export/` directory (must contain `traces.jsonl`). If the user hasn't exported recently, suggest running `/mlflow-export` first.
- **`--awow-root`** — optional. Defaults to `../awow` (resolved from cwd). Use when running from a sibling repo.
- **`--include-path`** — optional, **repeatable**. Extra working_directory to treat as a target repo. Use this when the awow repo has no traces yet and you want to evaluate sequence + editing patterns on a sibling repo as a stand-in.
- **`--user`** — optional. Email or short name of the subject developer. Presence of this flag flips into **self-coach mode**. Absent → **team-nudge mode**.
- **Output path** — optional. Defaults to `awow_usage_report.md` in cwd.

If the input path is missing or ambiguous, ask before running.

## Run the extractor

```bash
python3 .agents/skills/awow-usage-coach/scripts/awow_extract.py \
    --input <mlflow_export_dir> \
    --out   /tmp/awow_usage.json \
    [--awow-root ../awow] \
    [--include-path /path/to/sibling/repo] \
    [--user <email-or-short-name>]
```

The script prints a one-line summary to stdout (intent mix, top bigrams, edit footprint, top slash commands) and writes a JSON with this shape:

```
{
  target_sessions, target_users[], target_working_directories[],
  intent_taxonomy[],
  known_commands{},
  team_aggregate{
    n_prompts,
    intent{                        # the primary lens
      intent_counts[(label, n)],
      intent_shares{label: share},
      bigrams_top15[ {seq, count} ],
      trigrams_top10[ {seq, count} ],
      per_intent{                   # how each intent typically plays out
        <label>: {n_prompts, share, n_with_files, files_touch_rate,
                  file_buckets{}, median_words}
      },
      session_shapes[ {session_id, user, n_prompts, first_intent,
                       shape{label:share}, sequence_preview[]} ]
    },
    edit_footprint{               # raw file-modification rollup
      n_prompts_with_files, share_prompts_with_files, total_file_modifications,
      unique_files, file_buckets{}, top_files_top20[(path, n)]
    },
    slash_commands[(name, count)], command_coverage{used,unused,unknown_invoked},
    share{...},                    # secondary awow-vocabulary signals
    proposal_discipline{...}, placement_discipline{...},
    prompt_words{median,p75,max}
  },
  per_user[ {user, n_sessions, n_prompts, intent, edit_footprint, ...} ],
  evidence_quotes{
    "intent:investigate":[5 quotes], "intent:implement":[5], "intent:propose":[5], ...
    "slash:<name>":[...], "proposal_first":[...], "direct_write_to_canonical":[...],
    "story_only_no_placement":[...], "bloat_signal":[...], "brevity_signal":[...]
  },
  subject{...},  baseline{...},     # populated only when --user is set
  sessions[ {session_id, user, working_directory, prompts[ {text, files_modified, file_buckets, ...} ]} ]
}
```

Read the JSON with `Read`. Skim `team_aggregate.intent` and `team_aggregate.edit_footprint` and `evidence_quotes` first; reach into `sessions[*].prompts[*]` only when you need additional verbatim grounding.

If `target_sessions == 0`, stop and tell the user the export contains no sessions from the awow repo or any `--include-path`. They may need to re-export or pass a different path.

---

## Mode A — team-nudge report (no `--user`)

**Goal:** produce proposed additions to `.agents/CLAUDE.md` that an *agent* can read and apply, both as text edits to the file and as rules to follow in the next session. A nudge is a rule for the agent, not advice for the human prompter.

**Length cap:** aim for ≤120 lines total. For thin slices (<30 prompts) cap at ≤60 lines. Every section earns its width.

### Required sections

1. **Header** — input path, total sessions in export, target sessions, distinct target users, working directories, date range, include-paths used. One block, ≤8 lines.
2. **TL;DR** — 3 bullets max:
   - the dominant pattern (one sentence)
   - the number of nudges proposed and where each lands (file → section, no detail yet)
   - the single biggest gap evidence supports
3. **Intent shape** — table of intent counts + shares from `team_aggregate.intent.intent_counts`. One sentence on the dominant labels and one sentence on the size of the `other` bucket (>30% = taxonomy under-captures; flag and sample 2 quotes).
4. **Sequence patterns** — top 5 bigrams + top 3 trigrams from `team_aggregate.intent.bigrams_top15` / `trigrams_top10`. One short sentence per pattern on what it means (≤15 words each).
5. **Edit patterns** — from `team_aggregate.edit_footprint`:
   - share of prompts that modified files
   - file-bucket distribution
   - cross with `per_intent` to surface interesting pairings (e.g. *"`propose` prompts touched 0 markdown files"*)
6. **Awow-vocabulary lens (secondary)** — only if there's signal. If all signals are null/zero, replace the section with a single line: *"No awow-vocabulary signal in this slice."*
7. **Patterns that justify a nudge** — 2-4 patterns. **Three lines each. No more.**
   - **Line 1:** one-sentence description anchored in a sequence/edit pattern
   - **Line 2:** frequency from the JSON (real number, not "often")
   - **Line 3:** one verbatim quote (≤20 words; truncate with `…` if longer)
8. **Proposed nudges** — one nudge per justified pattern. Use this strict format:

   ````markdown
   ### Nudge N — <≤8-word title in imperative voice>
   **Target file:** `.agents/CLAUDE.md`
   **Target section:** `## <existing section name>` or `## <new section name (proposed)>`
   **Insert verbatim:**
   > <one or two sentences, addressed to the AGENT in second person, matching awow's existing CLAUDE.md voice>

   **Evidence:** <frequency> · "<short verbatim quote>" · would change <bigram/trigram/edit-pattern>
   ````

   The `Insert verbatim` block is a **single short paragraph**. No bullets, no sub-headings, no "you should" hedging. It must read as a rule the agent follows during a session.

9. **Don't nudge** — patterns the data shows but that don't deserve a CLAUDE.md addition. One line each, ≤4 items.
10. **Distribution checklist** — three lines max: edit `.agents/CLAUDE.md`, run `tools/gather.py`, do not hand-edit mirrored files.

### How to write the `Insert verbatim` block

This is the load-bearing part. The nudge is **a rule the agent reads at session start and follows during the session.**

Follow the voice rules in [`.agents/skills/agent-directive-voice.md`](../agent-directive-voice.md) — second person, imperative, ≤2 sentences, no evidence inside the rule. That skill carries worked rewrites (human-aimed → agent-directive) you can use as templates.

Nudge-specific addenda:
- **No restating evidence in the rule.** Stats and quotes go in the `Evidence:` line, not in the rule itself.
- **If the rewrite cannot be made agent-actionable, the pattern belongs in coaching (Mode B), not a CLAUDE.md nudge.**

### Quality bar

- **Every nudge is anchored.** A real frequency number AND a verbatim quote in the `Evidence:` line, or it doesn't ship.
- **Sequence > vocabulary.** Prefer nudges driven by bigrams/trigrams or edit patterns over nudges driven only by awow-keyword matching.
- **Propose only what's missing.** Read `.agents/CLAUDE.md` first. If the rule already exists, say so in "Don't nudge" rather than reproposing.
- **Bias toward fewer nudges.** Two sharp nudges that an agent can apply tomorrow beat five soft ones it has to interpret. Borderline patterns go to "Don't nudge".
- **Length discipline.** If the report exceeds the cap, cut analytical prose first, then quotes, then the second-place patterns — never cut the nudge directive itself.

---

## Mode B — self-coach report (`--user` set)

**Goal:** help one developer use the project better. Imperative, peer-tone, growth-oriented. Never judgmental. The point is "here's a thing you can try" — not "here's what you got wrong".

**Voice rules (load-bearing — do not violate):**
- Imperative ("Open more sessions by stating the goal up front …"), not interrogative or hedging.
- Direct comparisons to the team baseline are fine; framing them as punishment is not. *"You start 30% of sessions with `investigate`; teammates start 60% with `plan`"* is fine. *"You don't plan enough"* is not.
- Lead with strengths. Then offer 3-5 concrete moves.
- Second person. Speak to the developer, not about them.

### Required sections

1. **Header** — subject user, n sessions, n prompts, period covered, target paths used.
2. **What the data shows** — 1 short paragraph reading `subject.intent` and `subject.edit_footprint` in plain English. End with a tone-setting sentence: this is a starting point, not a verdict.
3. **Side-by-side snapshot** — small table: subject vs. baseline on
   - prompts/session, median prompt length
   - intent mix (top 5 labels for each, % share)
   - top 3 sequence bigrams (each side)
   - share of prompts that touched files; dominant file bucket
   - awow-vocabulary signals (only if non-null on at least one side)
4. **Strengths** — 2-4 things the subject is doing well, each with a verbatim quote pulled from their prompts (use `evidence_quotes[intent:<label>]` filtered to the subject's sessions, or `subject.sessions[*]`).
5. **Moves to try** — exactly 3-5 imperative suggestions. For each:

   ````markdown
   ### Move N — <short imperative title>
   <one-paragraph case for the move, written to the subject directly>

   **Try:** <concrete prompt or workflow they can copy>
   **Hook in the data:** <one stat from `subject` vs `baseline` (intent share, bigram, or edit pattern), plus a short quote from their own prompts>
   ````

   Each move must be actionable in the next session. Examples of good moves (these are illustrative, not a checklist):
   - "Open the cycle by stating the *goal* before asking Claude to act — your sessions start with `investigate` 60% of the time; opening with `plan` more often correlates with shorter sessions in the team data."
   - "Draft your story body in `proposals/<slug>.md` first, then promote — even when the change feels small."
   - "When you ask for context, point Claude at `context/knowledge-base/` rather than re-pasting it inline."
6. **What you're already doing that teammates aren't** — 0-3 bullets. If nothing stands out, omit the section rather than padding.
7. **Closing line** — one sentence. No grade, no score. Something like "Pick one move and try it in your next refinement session."

### Quality bar

- **No grades, no scores, no "B+".** Describe the shape, point at the next move.
- **Quote real prompts.** Every claim about how the subject prompts needs at least one verbatim snippet from `subject.sessions[*]` or `evidence_quotes`.
- **Numbers come from the JSON.** Never invent percentages. If `baseline` is empty or has only one user (i.e. there's no real comparison group), say so explicitly and switch the report's tone to "patterns in your own sessions" rather than "vs. team".
- **Stay in scope.** General prompt-engineering advice belongs in the `prompt-skill-analysis` skill. This skill is about *workflow shape* (intent sequence, editing rhythm, awow conventions when present).

---

## Interpreting the intent taxonomy

Quick guide for the model when reading bigrams and per-intent stats:

- **`investigate→investigate→investigate`** — deep exploration chain. Useful in unfamiliar territory; expensive when the answer is already in `context/knowledge-base/`.
- **`plan→propose→implement`** — the textbook awow rhythm. Reaching for `proposals/` before touching canonical paths.
- **`implement→verify→refine`** — test-driven loop. Healthy when changes are landing.
- **`implement→implement→implement`** without `verify` — execution without checks. Worth nudging if it correlates with `refine` later (rework).
- **`other` > 30%** — the taxonomy under-captures this team's voice. Quote 3-5 `other` prompts and let the report acknowledge the gap rather than misclassifying.
- **`inform`-heavy** — the developer talks *to* Claude (status updates, observations) rather than directing it. Not inherently bad — common in pair-programming style — but if combined with low `plan`/`propose`, it suggests the working approach is reactive rather than structured.

## After writing the report

Print 3 short bullets to the user:
- Where the report was saved.
- The headline strength (Mode B) or the top nudge (Mode A).
- The single suggested next step.

Do not restate the report in chat. The markdown file is the deliverable.

## Interplay with sister skills

- `mlflow-export` produces the input. If sessions are stale, suggest re-running it first.
- `prompt-skill-analysis` covers generic prompt quality (clarity, specificity, length distribution, voice). If the user wants both styles of feedback, run them as two reports against the same export — they don't overlap. This skill is about *workflow shape*, that one is about *prompt craft*.

## Troubleshooting

- **`target_sessions == 0`** — the export contains no sessions tagged with the awow working directory or any `--include-path`. Confirm: did the user actually run Claude Code from inside the target repo during the export window? Is `--awow-root` correct?
- **All sessions belong to one user** — both subject-vs-baseline comparison and team aggregation collapse. Tell the user and produce a single-user analysis instead of forcing a comparison.
- **`other` intent dominates (>50%)** — the taxonomy is undercapturing. Either the team writes very informal/short prompts, or there's a domain phrasing the patterns don't catch. Sample some `other` prompts in the report and flag the gap rather than overclaiming intent shape.
- **No `files_modified` data** — older mlflow exports may lack this tag. The intent + sequence lenses still work; just say in the header that edit-pattern signals are absent.
- **Subject user not present** — check `target_users` in the JSON. The script normalizes emails to the local-part (e.g. `someone@example.com` → `someone`); pass the matching form.
- **JSON is large** — `sessions[*].prompts[*].text` is truncated to 1200 chars by default. If the file is still big, read `team_aggregate`, `per_user`, and `evidence_quotes` and only dip into `sessions` for verification.
