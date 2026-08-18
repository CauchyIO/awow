# tests/process-transcript — regression suite for the board-plan gate

Maintainer-only. Adopters who templated this repo can delete this directory.

**Principle.** The gate a user trusts is the one this suite freezes: GATE 2 must
render as the flat diff-style board plan (`workitem-write` step 4), and apply
must honour the stale-guard (`workitem-write` step 5). Fixture boards are
file-based samples — the items are markdown table rows, a write edits the row —
so the whole flow runs real prompts against real files with no live board.
Suite-wide conventions: [`../README.md`](../README.md); execution mechanics:
[`.agents/commands/test-awow.md`](../../.agents/commands/test-awow.md).

## Scenarios

| scenario | break it witnesses |
|---|---|
| `plan-gate` | GATE 2 drifting off the board-plan grammar; `details N` executing or omitting `because:`; writes before `go` |
| `stale-move` | apply forcing a state move whose pre-image the board has outrun |

## Invariants graded

- **plan-grammar** — one fenced `diff` block titled `BOARD PLAN`, numbered `+` / `~` / `-` lines, counts footer.
- **plan-verbs** — `details N` prints the draft plus `because:` and executes nothing.
- **gate-discipline** — no board write before explicit approval.
- **stale-guard / apply-independence / no-force** — a stale line reports and skips; the rest still executes; nothing is overwritten.
- **apply-report** — the DONE shape (Executed / Skipped / Failed / Manual follow-up).

## Layout

```
tests/process-transcript/
├── suite.md               # command: process-transcript
├── fixtures/<scenario>/   # file-based sample board + standup notes + setup-progress
├── scripts/<scenario>.txt # scripted user replies
├── rubrics/<scenario>.md  # yes/no questions tagged with the invariant graded
├── checks/<scenario>.sh   # pre() fixture gate + post() mechanical assertions
├── setup/<scenario>.sh    # git-inits the fixture repo at run start
└── README.md
```
