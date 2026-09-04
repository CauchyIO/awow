# tests/artifact — regression suite for the Word target

Maintainer-only. Adopters who templated this repo can delete this directory.

**Principle.** The promise this suite freezes is that `/artifact` asks which
target the user wants *before* it drafts, generates Word from the agreed
markdown rather than from the HTML, proves the result structurally before
calling it done, and never drops a target silently when the tool is missing
(spec: [`proposals/word-export-design.md`](../../proposals/word-export-design.md)).
Fixture boards are file-based samples — the items are markdown table rows, a
write edits the row — so the whole flow runs real prompts against real files
with no live board, network, or `gh` auth. Suite-wide conventions:
[`../README.md`](../README.md); execution mechanics:
[`.claude/commands/test-awow.md`](../../.claude/commands/test-awow.md).

## Scenarios

| scenario | break it witnesses |
|---|---|
| `word-default` | target not asked; HTML generated then converted; stock-styles fact missing from the report |
| `word-reference` | reference doc ignored |
| `pandoc-absent` | silent drop of the Word target; repeated install nagging; a docx claimed that does not exist |

## Invariants graded

- **target-first** — the target question precedes drafting and generation.
- **word-constraints** — the four Word content constraints are stated before drafting.
- **content-gate** — nothing is generated before the user's yes.
- **from-markdown** — the docx comes from the markdown via `--from gfm --to docx`; no HTML intermediate.
- **outline** — `docx_outline.py` is run over the output and its outline matches the source.
- **round-trip** — the pandoc round trip is run and its result reported.
- **style-report** — the report names the reference doc applied, or says stock styles were used.
- **reference-applied** — `--reference-doc=` names the registered template.
- **tool-absent** — `pandoc --version` is probed the moment Word is chosen, before content work.
- **one-offer** — exactly one platform install offer, no retry after "no".
- **fallback-offered** — HTML + PDF is offered, not assumed.
- **honest-report** — an unproduced target is named in the report; no `.docx` is claimed.
- **board** — the item advances only when something was delivered.

## Layout

```
tests/artifact/
├── suite.md                # command: artifact
├── fixtures/_base/         # shared source; make-fixtures.sh copies it per scenario
├── fixtures/<scenario>/    # file-based sample board + brief.md + diagram.png + pointer
├── fixtures/make-fixtures.sh
├── scripts/<scenario>.txt  # scripted user replies
├── rubrics/<scenario>.md   # yes/no questions tagged with the invariant graded
├── checks/<scenario>.sh    # pre() fixture gate + post() mechanical assertions
├── setup/<scenario>.sh     # git-inits the fixture repo at run start
├── env/pandoc-absent/      # a machine without pandoc
└── README.md
```

## Fixture conventions

- `fixtures/_base/` is the single source for what every scenario shares — the
  board, `setup-progress.md`, the pointer, `brief.md`. Edit it, then re-run
  `fixtures/make-fixtures.sh` (needs pandoc); the per-scenario directories are
  generated and committed, never hand-edited.
- `brief.md` is deliberately Word-shaped: one H1, two H2s, one table, one PNG
  referenced by a relative path. Its outline — three headings in order,
  `tables: 1`, `images: 1` — is what the `outline` invariant checks against.
- `diagram.png` is a 4×4 opaque PNG written from stdlib, so the fixture is
  byte-deterministic and tiny.
- `word-reference/` ships pandoc's own default reference doc with `Heading1`'s
  colour set to the sentinel `FF00AA`. The sentinel is a *mechanical* marker:
  finding it in the output's `word/styles.xml` proves the reference doc was
  applied. Its pointer also ships a minimal `style-guide.html` so Phase 0's
  `path:` read resolves.
- `word-default/` and `pandoc-absent/` keep `mode: absent` and an empty
  `word_reference`, which is what makes the stock-styles report assertable.
- `pandoc-absent` needs docker; without it the scenario composes
  `indeterminate (stage: env)`, as `setup-awow`'s `preflight-no-git` does.

## Adding a scenario

Same four-file unit as every suite (fixture, script, rubric, checks) plus the
executable `setup/<scenario>.sh`, and `env/<scenario>/Dockerfile` when the
scenario needs a machine the host cannot impersonate. Add the scenario name to
the loop in `fixtures/make-fixtures.sh` so its fixture is generated from
`_base/`. Run `python tools/validate-evals.py` to confirm the wiring.
