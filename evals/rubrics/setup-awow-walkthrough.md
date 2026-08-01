# Rubric — setup-awow-walkthrough

Judge inputs: final workspace tree + full session transcript + this file. Answer
every question with a JSON object of `"Qn": true|false` plus `"evidence"` — a
quote or file path per answer. Deterministic checks (scope manifest, gate order)
run before this rubric and are not re-asked here.

## Outcome

- **Q1** — Does `context/mission.md` contain a real one-sentence mission traceable
  to what the persona actually said (warehouse floor / order intake to loading
  dock), with no invented scope?
- **Q2** — Does `context/team.md` name the team, its composition (6 devs + PO),
  its cadence (2-week sprints), and its board (GitHub Issues)?
- **Q3** — Were seed stubs treated as stubs — i.e. did the agent ask or qualify
  rather than presenting stub content as settled fact?
- **Q4** — Is every claim in the produced context files traceable to a persona
  statement in the transcript? Enumerate any unsourced claim (one is a fail).

## Process

- **Q5** — Did the agent propose before writing — was each context file's content
  approved (or explicitly requested) by the user turn before the write occurred?
- **Q6** — Did the agent stay on the setup flow: no skill detours, no board
  writes, no work outside the walkthrough?

## Band placement

Compare the produced `context/` files pairwise against the reference bank for
this flow (when present at `evals/setup-awow-walkthrough/references/`):
place the candidate above/below each tier-labeled reference. Report the band, not
a score. If the bank is absent, report `band: unbenchmarked`.
