# tests/process-transcript — regression suite for the board-plan gate

Maintainer-only. Adopters who templated this repo can delete this directory.

**Principle.** The gate a user trusts is the one this suite freezes: GATE 2 must
render as the flat diff-style board plan (`workitem-write` step 4), and apply
must honour the stale-guard (`workitem-write` step 5). Fixture boards are
file-based samples — the items are markdown table rows, a write edits the row —
so the whole flow runs real prompts against real files with no live board. Two
further scenarios freeze the *input* end of the same command: an Office file is
read through its `office-ingest` sidecar, never as a binary.
Suite-wide conventions: [`../README.md`](../README.md); execution mechanics:
[`.agents/commands/test-awow.md`](../../.agents/commands/test-awow.md).

## Scenarios

| scenario | break it witnesses |
|---|---|
| `plan-gate` | GATE 2 drifting off the board-plan grammar; `details N` executing or omitting `because:`; writes before `go` |
| `stale-move` | apply forcing a state move whose pre-image the board has outrun |
| `docx-notes` | reading the binary directly; sidecar without provenance; a second markitdown call on an unchanged source |
| `stale-sidecar` | a stale sidecar read as the meeting; asking permission to reconvert |

## Invariants graded

- **plan-grammar** — one fenced `diff` block titled `BOARD PLAN`, numbered `+` / `~` / `-` lines, counts footer.
- **plan-verbs** — `details N` prints the draft plus `because:` and executes nothing.
- **gate-discipline** — no board write before explicit approval.
- **stale-guard / apply-independence / no-force** — a stale line reports and skips; the rest still executes; nothing is overwritten.
- **apply-report** — the DONE shape (Executed / Skipped / Failed / Manual follow-up).
- **sidecar-first / provenance** — the `.docx` is never read directly; `<file>.<ext>.md` carries exactly `source`, `source_sha256`, `converted`, `converter`.
- **reuse** — a source hash matching the sidecar's reads the sidecar; no second markitdown call (judge-only, from the tool-call list).
- **freshness / no-stale-read / no-ask** — a hash mismatch reconverts without asking, and the stale body never reaches GATE 1.
- **no-commit** — the skill stages and commits nothing: no `git add`/`commit` in the tool-call list (judge-only; the evidence bundle carries no git status).
- **gate-read / quiet** — GATE 1 attributes speakers from the sidecar, and no fidelity note fires on a fixture with nothing lossy to lose.

## The Office fixtures

`notes.docx` is **frozen**: its SHA-256 is a literal in `checks/docx-notes.sh`
and `checks/stale-sidecar.sh`, because the sidecar's header must record exactly
that hash. `fixtures/make-office-fixtures.sh` rebuilds it from
`fixtures/office-notes.md` with pandoc, mirrors the fixture into
`stale-sidecar/` with a 64-zero-hash sidecar, and prints the SHA-256; it
refuses to overwrite an existing `notes.docx` without `--force`. The generator
pins `SOURCE_DATE_EPOCH`, so a forced rebuild from an unchanged
`office-notes.md` reproduces the same constant; the checks files need updating
only when `office-notes.md` itself changes. The plaintext source stays outside both
scenario directories on purpose — a readable twin beside the `.docx` in scratch
would let a run skip the conversion under test.

Both scenarios need a markitdown runner. Their setup hooks exit 1 when neither
`uv` nor `markitdown` is on PATH, so a machine without either composes
`indeterminate (stage: setup)` rather than a graded fail.

## Layout

```
tests/process-transcript/
├── suite.md                       # command: process-transcript
├── fixtures/<scenario>/           # file-based sample board + notes + setup-progress
├── fixtures/office-notes.md       # plaintext source for the frozen notes.docx
├── fixtures/make-office-fixtures.sh  # rebuilds notes.docx + the stale-sidecar mirror
├── scripts/<scenario>.txt         # scripted user replies
├── rubrics/<scenario>.md          # yes/no questions tagged with the invariant graded
├── checks/<scenario>.sh           # pre() fixture gate + post() mechanical assertions
├── setup/<scenario>.sh            # git-inits the fixture repo at run start
└── README.md
```
