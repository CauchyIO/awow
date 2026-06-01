# context/quarterly/

Quarterly-cycle inputs that the agent reads when refining features, picking up new work, or producing digests.

Drop slidedecks, planning documents, OKR exports, and stakeholder briefs here. The agent treats this folder as long-form context that survives across the quarter.

## What quarter planning produces — the *what* that feeds refinement

The artefacts here are the output of quarter planning, which sets **what** the team will build and **why** — never the *how*. The chain runs outcome-down:

- **OKRs** — owned by the program board and PO. The quarter's outcomes: the customer or business change being chased, stated as objectives with measurable key results.
- **Epics** — owned by the PO, each mapped to an OKR. A large slice of value under one outcome.
- **Features** — broken out of an epic by the PO with the tech lead. A feature is the unit that *enters refinement*: small enough to reason about, still bigger than a single story.

Refinement picks up from there — it turns a chosen feature into right-sized stories and works out the *how*; it never re-decides the *what*. So when these inputs are thin (an epic with no features, a feature with no stated outcome), that is a planning gap to close here, not something refinement should paper over by inventing stories. See `/refinement-prep` for the routes that populate the board, and the board hierarchy reference under `context/tooling/boards/` for how outcome → epic → feature → story map onto board primitives.

## Naming

Use ISO dates so chronological sort works:

`<YYYY-Q[1-4]>-<source>-<name>.<ext>`

Examples:
- `2026-Q2-leadership-OKRs.pptx`
- `2026-Q3-roadmap-draft.md`
- `2026-Q2-stakeholder-brief-payments.docx`

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

This folder is tracked in git. Be deliberate about what lands here — once committed, it is in the repo's history. For sensitive inputs, list them in `.gitignore` and reference the location rather than commit.

## Companion: `INPUT.md`

`INPUT.md` in this folder is a one-page guide for users dropping files. It restates the naming and "what / what not" rules above for the benefit of someone landing here without reading this README.
