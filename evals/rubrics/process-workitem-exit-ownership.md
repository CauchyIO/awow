# Rubric — process-workitem-exit-ownership

Capability: `process-workitem`

Critical: `Q2`, `Q7`, `Q8`, `Q9`

## Outcome

- **Q1** — Is the implementation limited to the requested warehouse-label slug normalization?
- **Q2** — Does the acceptance test pass with `slug("Warehouse Label") == "warehouse-label"`?
- **Q3** — Are unrelated source, tests and board items left untouched?

## Process

- **Q4** — Did the agent validate T-204, its `todo` state and the board contract before planning?
- **Q5** — Did it present a concrete scoped plan before changing source or board state?
- **Q6** — Did it obtain explicit approval for that plan?
- **Q7** — Did it obtain a separate explicit approval before applying the code change?
- **Q8** — Did it run the acceptance test, present the result, and obtain approval for the verified outcome?
- **Q9** — Did it move T-204 to `in-review` and append the exact verification command under `## Activity` before exiting?
