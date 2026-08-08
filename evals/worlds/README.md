# evals/worlds/ — shared scenario bases

A world is a complete starting repo for one fictional team. A scenario names
its world in `world.txt` and layers its `overlay/` on top; see
[`../scenarios/README.md`](../scenarios/README.md) for the composition rule.

Editing a world edits every scenario built on it. That is the point — a
convention fix lands everywhere at once instead of forking across copies — and
it is guarded: `evals/validate.py` re-runs every member scenario's `pre` check
against a fresh composition, so a world edit that invalidates an assumed fact
fails CI before it costs a run. Review world diffs as cross-cutting changes.

| World | The team | Used by |
|---|---|---|
| `file-board-team` | Runs its board as one markdown file per issue under `board/issues/`, with REQUIRED conventions for issue titles, labels and output discipline. | `workitem-write-board-gate`, `reflex-cold-start` |

The bespoke overlays (daily-digest's GitHub Projects sample, process-workitem's
file-backed variant, setup-awow's greenfield stub) are single-member worlds in
waiting. The canonical Fikkert & Zn. universe (seed material under
`tests/fixtures/fikkert/`) is the intended consolidation target.
