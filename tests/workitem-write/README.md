# tests/workitem-write/

Evaluates the `workitem-write` skill (AWO-121): the one convention-wired path for
board item creates and updates. The scenario plants a deliberately
convention-violating ad-hoc request and asserts the skill corrects the draft against
the fixture's conventions **before** anything reaches the board.

## The fixture board

A file-based board, hermetic to the scratch workspace, declared in
`context/tooling/board.md`: one markdown file per issue at `board/issues/<ID>.md`
with `id` / `title` / `state` / `labels` frontmatter. Creating an issue = writing the
next `T-<n>` file. The board has no native blocked-by relation (a `Blocked by:` body
line is the fallback the skill must know about).

## Invariants

1. **Look first.** The board is searched before drafting; the adjacent existing item
   (T-101, the runner-image update) is reported as related rather than duplicated or
   ignored.
2. **Conventions cited.** The draft names which conventions shaped it (title pattern,
   labels, container/board target).
3. **Title corrected.** The user's vague, non-verb-first title is rewritten verb-first
   per the fixture's `issue-titles.md`.
4. **Labels on-taxonomy.** The user's off-taxonomy labels (`URGENT!!`, `logging`) are
   replaced with labels from the fixture's `labels.md`; nothing off-taxonomy lands.
5. **Placement respected.** The standup recap and status musings stay out of the
   issue body; the body is intent + acceptance criteria per `output-discipline.md`.
6. **Gate before write.** No file under `board/issues/` is created or modified before
   the user's explicit `go`.
7. **Write + report.** After `go`, exactly one new issue file exists and a DONE-style
   report is produced.

## Scenarios

- **planted-violation** — the single scenario: an ad-hoc "make a ticket" request
  violating title, label, and placement conventions at once; scripted `go` at the
  gate. Checks assert the mechanical facts (new file, corrected title verb, taxonomy
  labels, no recap prose); the rubric grades search, citation, gating, and report
  behaviour.
