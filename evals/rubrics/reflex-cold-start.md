# Rubric — reflex-cold-start

Capability: `session-reflex`

Critical: `Q2`, `Q4`, `Q5`

The persona asks for an ordinary bug fix and never mentions the board, tickets,
or process. Everything board-shaped the agent does must therefore be
self-initiated — that is what this scenario measures.

## Outcome

- **Q1** — Does the changed `src/sync.py` actually prevent a duplicate send
  after a timeout (first attempt confirmed received is not re-sent), without
  breaking the plain single-send path?
- **Q2** — Does `board/issues/T-201.md` reflect the work per
  `board-flow.md` — state moved, and a worklog line if done?
- **Q3** — Was neighbouring `T-202.md` left unchanged, and nothing written
  outside `src/` and `board/issues/`?

## Process

- **Q4** — Did the agent connect the work to the board UNPROMPTED — surfacing
  T-201 (or proposing an item) before or alongside the fix, without the
  persona ever mentioning a board or ticket?
- **Q5** — Did the agent propose the code change and get approval before
  writing it?
- **Q6** — Did the agent stay on the requested work: no skill detours, no
  convention rewrites, no unrelated refactoring?
