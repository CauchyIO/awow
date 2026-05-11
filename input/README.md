# input/

Audit trail and reference material that informed the design of this repo. Not part of v0.1 operational surface — these are *inputs to the design*, not files the agent operates against day-to-day.

## What's here

| File / folder | Purpose |
|---|---|
| `PROPOSAL.md` | The design proposal for `awow` v0.1, with rationale per section |
| `ADDITIONS_FROM_LINEAR.md` | Structural ideas captured from upstream research, marked horizon or v0.1 |
| `feedback.md` | Raw feedback from the design conversation |
| `prompt.md` | The original brief for what this repo should become |
| `proposal_questionnaire_anwers.md` | Answers to the design questionnaire |
| `research/` | Peer-research synthesis (acai.sh, sprintiq.ai), Linear-research inventory, questionnaire |

## When to read these

- Onboarding a new contributor who needs to understand *why* the repo is shaped the way it is.
- Considering a structural change that touches the design rationale.
- Adopting awow for a new team and wanting to see the trade-offs that were considered.

## When to ignore these

- Day-to-day operation. The agent does not need these files to do its job. The operational surface is `.agents/`, `context/`, and the seed commands.
- Quarterly inputs for refinement / planning → those go in `context/quarterly/`, not here.

## Maintenance

These files are frozen at v0.1. If the design evolves materially in a later version, write a follow-up alongside (e.g. `PROPOSAL-v0.2.md`) rather than rewriting these in place.
