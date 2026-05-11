# context/knowledge-base/architecture/

System shape. Decisions, diagrams, integration patterns. One file per concern.

Architecture entries are written as prose with embedded diagrams (Mermaid or ASCII). Each file explains *what* the system looks like at that altitude and *why* — not how to operate it.

## What goes here

- System diagrams (component, sequence, deployment)
- Integration descriptions (this service ↔ that service)
- Architectural decision records that span more than one concern (small / specific decisions go in `decisions/`)
- Pattern catalogues for the team's solution shape

## What does NOT go here

- Runbooks → `runbooks/`
- Single-decision ADRs → `decisions/`
- How-we-do-X recipes → `patterns/`
- Domain terms → `glossary.md` at the parent level
