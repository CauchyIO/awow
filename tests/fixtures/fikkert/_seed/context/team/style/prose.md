# Prose style (long-form)

For internal docs, briefs, external publications. Different mode from board output.

## Voice

- Complete sentences. Paragraphs over bullet lists for argument.
- The engineer's actual voice — first person where appropriate, direct.
- No marketing language. No hedging unless the uncertainty is genuine.
- Em-dashes are allowed and used. (Distinct from board output, which forbids them.)

## When this applies

- `input/PROPOSAL.md`-style design documents
- Blog drafts, briefs for external audiences
- The README at the awow repo root, and any long-form documentation under `context/knowledge-base/architecture/` or `context/knowledge-base/decisions/`

## When this does NOT apply

- Anything written to the board → `board-output.md`
- Comments → `comments.md`
- The knowledge base — context determines: `architecture/` is prose, `glossary.md` is terse, `runbooks/` is mostly terse.
- Prompts under `.agents/` — those follow the agent-directive voice (see `.agents/skills/agent-directive-voice.md`), not this file.

## Reference

The FinOps Databricks writing style guide at `design/blogs/finops_databricks/writing_style.md` (in Cauchy's design repo, not this one) is the canonical practitioner-voice reference. Apply the same constraints here: practitioner voice, no "simply / just / easily", brevity first.
