# GitHub Issues — duplicate avoidance reference (skeleton)

GitHub Issues has **no automatic duplicate detection**. Nothing warns you that an issue already exists before you open another one — so preventing duplicates is entirely a search-before-create discipline. This is the board's single biggest noise risk, which is why the wizard always captures a search recipe into `board.md`.

## Native capabilities & limits

- **Search:** `gh issue list --search "<terms>"`, `gh search issues "<terms>" --repo <owner>/<repo>`, or the web search box. Keyword/text only — no semantic similarity, so vary the terms (synonyms, the area label, the component name).
- **Marking a duplicate:** close the newer issue as **not planned** and comment `Duplicate of #<N>` (GitHub renders the reference); optionally add a `duplicate` label. There is no first-class "merge issues" action — the older issue wins, the newer is closed.
- **Projects v2** does not dedup either: two separate issues for the same work both appear on the board.

## Wizard responsibilities

**Mode A (from reference).** Confirm the search command the team will use (CLI vs web) and whether they want a `duplicate` label created (`gh label create duplicate`). Record both in `board.md`.

**Mode B (assess current).** Check whether a `duplicate` label already exists and is in use; capture any existing convention for closing duplicates.

## What lands in `board.md`

```
## Avoiding duplicates

No auto-detection — **search before creating, every time.**
Search: `gh issue list --search "<terms>"` (keyword-only; try several term sets).
Found one? Comment on it or move it forward — do not open a second issue.
Genuine duplicate slipped through: close the newer as *not planned*, comment
`Duplicate of #<N>`, optionally add the `duplicate` label.
```
