# Rubric — index-form

One repo, index-form `board.md` (product: `app/**`, infra: `infra/**`). The ask
names app/ work, so the scope rung must resolve to product silently.

## Behaviour during the run

1. *(invariant 3)* Did the run announce the resolved target (`targeting board: product`
   or an equivalent one-liner) before citing items?
2. *(invariant 4)* Did the run avoid a board picker entirely (scope match resolved it)?
3. *(invariant 1)* Are PROD-1 and PROD-2 the only board ids cited as "your work"?
4. *(invariant 2)* Is INF-1 (the infra board) never presented as the user's work?
5. *(invariant 5)* Not applicable here (the repo is scaffolded) — did the run
   nonetheless treat it as scaffolded, with no `/setup-awow` offer?

## Post-run state

6. *(invariant 6)* All three board spec files are byte-identical to the fixture.
