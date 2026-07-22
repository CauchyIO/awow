# .agents/skills/

"What good looks like." Markdown the agent references during planning and execution.

A *skill* sits between raw prompts and full MCP servers. The skill tells the agent what *output to aim for* — example shapes, naming conventions, anti-patterns. Skills are how team-specific taste gets into the output without re-explaining it every session.

## Two shapes of skill

### Declarative skill — a single markdown file

The original shape. One markdown file at `.agents/skills/<name>.md` whose body describes the target output (an example, a checklist, an anti-pattern list).

Examples shipped with the starter pack:

- [`user-story-template.md`](./user-story-template.md) — the shape of a well-structured user story.
- [`agent-directive-voice.md`](./agent-directive-voice.md) — voice rules for authoring or editing any prompt under `.agents/`.

### Operational skill — a directory with `SKILL.md` and bundled `scripts/`

A skill that bundles a deterministic helper script alongside the rubric. The agent reads `SKILL.md` to know *when* and *how* to invoke the script, then turns its output into the desired shape. Use this when the rubric needs precise inputs (counts, extracted prompts, paginated API calls) the agent shouldn't reproduce inline.

```
.agents/skills/<name>/
├── SKILL.md          # frontmatter (name + description) + invocation + report rubric
└── scripts/
    └── <script>.py   # plain-stdlib by default; documents its own deps in SKILL.md
```

Examples shipped with the starter pack:

- [`mlflow-export/`](./mlflow-export/) — export agent traces + sessions to local JSON. Ships with a Databricks-MLflow exporter; swap the script for your backend's equivalent.
- [`prompt-skill-analysis/`](./prompt-skill-analysis/) — assess prompt quality from an agent session. Ships with parsers for raw Claude Code JSONL and the `mlflow-export` output shape; extend for other harnesses.
- [`awow-usage-coach/`](./awow-usage-coach/) — propose AGENTS.md nudges or coach an individual based on workflow shape. Consumes the `mlflow-export` JSON; rubric is harness-agnostic.

### Two plugins, one source tree

Skills marked `channel: telemetry` in their frontmatter build into the separate **`awow-telemetry`** plugin rather than into `awow` — `mlflow-export`, `prompt-skill-analysis`, `project-timeline`, `awow-usage-coach`, `session-export`. The base plugin keeps the four behavioural skills: `using-awow`, `board-aware-development`, `architecture-aware-development`, `user-story-template`. Different audience, different dependency profile, different privacy posture; and every skill description loads into every session, so a telemetry surface nobody uses is a tax on everybody.

The source stays here either way — `channel:` selects the payload, not the location. Install with `/plugin install awow-telemetry@awow`. **Claude Code only this release:** `tools/sync-dist.sh` publishes only `dist/` to `awow-dist`, which is the Codex and Pi install source, so telemetry does not reach those harnesses.

The script is the deterministic part. The judgement still lives in `SKILL.md`.

### These ship as starters, not as required ingredients

Every operational skill in this folder is opinionated about *some* part of the stack — the tracing backend, the harness session format, the analysis rubric. That is fine for a starter pack; it is not fine for a long-lived team config. `/setup-awow` Step 8 (Skills review) walks the team through each shipped skill and asks: keep as-is, customise to your stack, or drop. Re-run that step whenever the stack changes.

## When to write a skill

- A recurring quality bar the agent keeps missing without explicit guidance.
- A team-specific shape (notebook layout, story template, runbook structure) that can be described in markdown.
- A vocabulary that the team consistently uses one way and the agent occasionally varies.
- A multi-step workflow whose *judgement* should be codified but whose *counting* should be deterministic — that's the operational shape.

## When NOT to write a skill

- One-off correction in a specific session → tell the agent inline, don't codify.
- Pure information retrieval → MCP, not a skill.
- Pure executable plumbing with no judgement step → a script in `tools/` or an MCP server, not a skill.

## Decision rule

| Use case | Right tool |
|---|---|
| Reusable text shape | Declarative skill (`<name>.md`) |
| Workflow with rubric + deterministic helper | Operational skill (`<name>/SKILL.md` + `scripts/`) |
| Pure executable plumbing | Script in `tools/` or MCP server |
| Information to retrieve | MCP server |
| One-shot context | Inline prompt |

## Cross-harness

Claude Code calls these "skills" natively. GitHub Copilot calls the same concept "[agent skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)". `tools/gather.py` mirrors files here into both surface formats.

When mirroring an operational skill, both `SKILL.md` and the bundled `scripts/` directory travel together. Path references inside `SKILL.md` use `.agents/skills/<name>/scripts/...` so they resolve correctly from the repo root regardless of which harness is active.
