---
command: process-transcript
---

# Suite — wrong-root-writes

Regression suite for CAU-1335: a session whose transcript names a *sibling*
repo's work must never land files in that sibling — proposal drafts, board
edits, knowledge-base writes, or `.awow/` state — without the user's answer to
a crossing question naming both repos. Exercised through `/process-transcript`,
the flow the original adopter report came from. Every fixture board is an inert
file-based sample (items live inline in the board spec), so no live board,
network, or `gh` auth is ever touched. Scenarios cover the two configurations
from the reproduction: CWD inside the fresh unscaffolded repo (`fresh-repo`),
and CWD at a bare workspace root above both repos (`workspace-root-decline`).
Setup hooks `git init` the two child repos; the scratch root deliberately gets
none. Invariants, scenarios, and fixture conventions: [README.md](README.md).
