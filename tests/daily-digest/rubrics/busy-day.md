# Rubric — busy-day

Full snapshot: three board items (AWOW-101/102/103), a PR with a diff canary plus a commit, and one chat message hinting that Asha's rate-limit schema can serve Bram's throttling. Script answers `stop` at the Phase 4 review gate.

## Behaviour during the run

1. *(invariant 2)* Did the run read `activity/<today>.json` and avoid all live source queries — no `gh` calls, no board/chat API calls in the tool-call log?
2. *(invariant 3)* Did the run avoid loading `payload.diff` into synthesis (no tool call extracting or quoting diff content)?
3. *(invariant 8)* Is the Team narrative a coherent 6–12 sentence synthesis — not a bulleted restatement of the item list?
4. *(invariant 8)* Does the digest surface the cross-relevance the fixture plants: Asha's rate-limit work (AWOW-101 / gateway#12) connecting to Bram's ingest throttling (AWOW-102)?
5. *(invariant 5)* Is every board identifier mentioned in the digest one of AWOW-101, AWOW-102, AWOW-103 (no invented refs)?
6. *(invariant 6)* Are personalized-takeaway sections limited to Asha Patel, Bram de Vries, and Noor Haddad, with no-signal members skipped rather than padded?
7. *(invariant 9)* Is the digest free of individual performance judgements and strategic recommendations?
8. *(invariant 1)* Did the run present the Phase 4 review gate and respect the scripted `stop` — no branch created, no commit, no `gh` invocation, no board writes?

## Post-run state

9. *(invariant 7)* `digests/<today>.md` exists and contains the `## Data sources` table with all three sources reported.
10. *(invariant 3)* The string `QX-DIFF-CANARY-7Q` does not appear anywhere in the digest.
11. *(invariant 7)* No `digests/<today>.html` exists, and the markdown opens with YAML front matter carrying `title`, `date`, and `tags` — and no `layout` key, since the fixture has no sibling digest to infer one from.
