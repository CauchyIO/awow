# Quarterly inputs

Drop slidedecks, planning docs, OKR exports, and other quarterly-cycle artefacts here. The agent reads them when refining features, picking up new work, or producing digests.

## Naming

- `<YYYY-Q[1-4]>-<source>-<name>.<ext>` — e.g. `2026-Q2-leadership-OKRs.pptx`
- Use ISO dates so chronological sort works

## What to drop here

- Quarterly OKRs / strategic-objective documents
- Roadmap slidedecks
- Stakeholder briefs that span more than one sprint
- Investment-thesis or planning artefacts the team needs to align on

## What NOT to drop here

- Daily standup notes → `transcripts/`
- Code → the codebase
- Story-specific docs → the knowledge base
- Personal notes → not in this repo

## Retention

This folder is tracked in git. Be deliberate about what lands here — once committed, it is in the repo's history. For sensitive inputs, mark them in `.gitignore` and reference rather than commit.
