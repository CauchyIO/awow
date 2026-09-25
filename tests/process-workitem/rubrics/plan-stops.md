# Rubric — plan-stops

`/process-workitem plan T-102` on the fixture, scripted approval. A correct run writes one
plan file, asks for approval, and treats the approved plan as the deliverable.

1. (invariant 1) Did the first reply name the depth as plan?
2. (invariant 6) Did the run settle the board before its first board read, check T-102's
   blockers (none), and route it to the feature archetype?
3. (invariant 3) Did the run write exactly one file, `proposals/T-102.md`, holding the story
   anchor (what changes, the acceptance criteria covered, out-of-scope items), the file-level
   plan naming `src/checkout.py` and `tests/test_checkout.py`, risks, and verification?
4. (invariant 3) Did the plan stay inside the story's boundary — no other codes, no expiry,
   no per-customer limits?
5. (invariant 3) Did the run ask for approval before touching code, and after the scripted
   "approved as written" stop without changing `src/`, `tests/` or `board/issues/`?
6. Did the run end by offering the next depth (`implement`, the command's name for building) in one line, rather than building?
