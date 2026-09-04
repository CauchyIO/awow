# Office Ingestion via markitdown — Design Spec

**Status:** Draft by Arie, 2026-09-04. Approved in conversation at the design gate; awaiting written review.
Board item: [CAU-1526](https://linear.app/cauchyio/issue/CAU-1526/implement-office-file-ingestion-through-markitdown-sidecars) (created 2026-09-04 from the §9 draft).
Companion: [word-export-design.md](word-export-design.md) (the outbound direction: markdown → Word). The two specs are independent; that one is sequenced first.

**Goal:** Commands that read team inputs can open Word, PowerPoint and Excel files. Today `context/quarterly/` invites `.pptx` and `.docx` drops and three commands claim to read that folder, but nothing says how the agent opens one, and Claude Code reads PDFs natively but not Office files. This spec makes a dropped `.docx`, `.pptx` or `.xlsx` readable by converting it once with [markitdown](https://github.com/microsoft/markitdown) into a provenance-stamped markdown sidecar beside it, re-converted only when the source changes, tracked exactly as the source is tracked. Every harness that reads context as text — the M365 declarative agent included — then sees the content. Nothing is left open.

## 1. Scope and non-goals

In scope:

- One new packaged skill `.agents/skills/office-ingest/SKILL.md`. No bundled script: the markitdown CLI is the deterministic helper.
- One-line routes in `.agents/skills/using-awow/SKILL.md` §Route to the moment and in `.agents/AGENTS.md` §Where to read context.
- One-line delegations in `.agents/commands/refinement-prep.md` (Inputs), `.agents/commands/process-transcript.md` (§1.1), `.agents/commands/strategy-flow.md` (Phase 0). In passing, refinement-prep's `input/quarterly/` is corrected to `{ANCHOR}/context/quarterly/` — `input/README.md` itself says quarterly material does not live under `input/`.
- Convention text in `context/quarterly/README.md` and `context/quarterly/INPUT.md`.
- Two scenarios added to `tests/process-transcript/`.
- A row in `.agents/skills/README.md`.
- No CHANGELOG edit: release sections are drafted from merged PR titles at version bump, so the PR title carries the board id and a one-line summary.
- Implementation sequencing: [plans/2026-09-04-office-ingest.md](plans/2026-09-04-office-ingest.md).

Non-goals:

- **The markitdown MCP server.** `markitdown-mcp` is 0.0.1a4, a pre-release alpha with a single `convert_to_markdown(uri)` tool. Revisit when it reaches a stable line; the CLI contract here does not change if it does.
- **LLM image captions** (`markitdown`'s `llm_client` option) and the **Azure Document Intelligence / Content Understanding** extras. Local, deterministic conversion only.
- **PDF through markitdown.** The harness reads PDF natively; routing it through a converter would lose the native reader's layout handling for no gain. Noted as a possible extension for scanned PDFs, which need OCR and are out of scope.
- **Outlook `.msg`, EPUB, audio, YouTube.** markitdown supports them; awow has no reader for them.
- **Editing a sidecar.** Corrections go to the source, or to the command's own working notes, never to the generated file.

## 2. The sidecar contract

### 2.1 Naming

`<file>.<ext>.md` beside the source: `2026-Q3-leadership-OKRs.pptx` → `2026-Q3-leadership-OKRs.pptx.md`. Keeping the original extension in the name means `deck.pptx` and `deck.docx` in one folder cannot collide, the provenance is visible in a directory listing, and the pair sorts together.

### 2.2 Provenance header (normative, verbatim shape)

```yaml
---
source: 2026-Q3-leadership-OKRs.pptx     # path relative to the sidecar's own directory
source_sha256: <64 lowercase hex>
converted: 2026-09-04                    # ISO date, local
converter: markitdown 0.1.7              # from `markitdown --version`
---
```

Four keys, nothing else. The body below the header is markitdown's output, untouched.

### 2.3 Freshness rule

Before reading a sidecar, hash the source:

```
python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <source>
```

(python3 is already a hard dependency of the plugin hooks, so this is portable where awow runs at all.) Hash equals `source_sha256` → read the sidecar, do not invoke markitdown. Hash differs, or no sidecar → convert, overwrite the sidecar, write a fresh header. SHA-256 rather than mtime because mtime changes on checkout and copy; the hash does not.

### 2.4 Tracking rule

The sidecar inherits the source's tracking. Inside a git repo, run `git check-ignore -q <source>`:

- **Source ignored** → run `git check-ignore -q <sidecar>`. Also ignored: done. Not ignored: propose one `.gitignore` line for the sidecar path, one confirmation, then write it.
- **Source tracked or untracked-but-not-ignored** → write the sidecar and leave it for whoever commits the source. The skill never stages or commits.
- **Not a git repo** → write the sidecar; nothing else.

### 2.5 Privacy

A sidecar carries its source's sensitivity. The public-repo rule in `.agents/AGENTS.md` applies as written: a converted copy of anything the user called sensitive never lands in a tracked path, and the `pre-push` leak scan is a backstop, not the line of defence.

## 3. Conversion

### 3.1 Formats

`.docx`, `.pptx`, `.xlsx`, `.xls` — matched on extension, case-insensitively. Anything else is not this skill's business; PDF in particular stays with the harness's native reader.

### 3.2 Command ladder (normative)

1. `uv` on PATH → `uvx --from "markitdown[docx,pptx,xlsx,xls]" markitdown <source> -o <sidecar>`. No install step, isolated environment, nothing pinned in the adopter's repo. Verified 2026-09-04: resolves 0.1.7 and converts in one call.
2. Else `markitdown` on PATH → `markitdown <source> -o <sidecar>`.
3. Else offer, once: `uv tool install "markitdown[docx,pptx,xlsx,xls]"` — or `pipx install "markitdown[docx,pptx,xlsx,xls]"`, or `python3 -m pip install --user "markitdown[docx,pptx,xlsx,xls]"` — and run only on an explicit yes. On no, or on a failed install, ask the user for a PDF export or pasted text and proceed on that. Never claim the file was read when it was not.

Record the version from `markitdown --version` (or `uvx --from … markitdown --version`) for the header. Version floor 0.1.x (verified 0.1.7); Python ≥ 3.10, which matches `pyproject.toml`.

### 3.3 Fidelity facts

Verified 2026-09-04 against markitdown 0.1.7 on pandoc-generated files. `.docx`: headings, bold, links and tables survive; **task-list checkboxes flatten to plain bullets**; **fenced code blocks become plain paragraphs**; images are referenced, not extracted. `.pptx`: slides arrive under `<!-- Slide number: N -->` markers with speaker notes appended per slide under a `### Notes:` heading, and PowerPoint loses more than Word — bold, links and bullet markers are dropped, non-title headings flatten to plain text, checkboxes render as a literal `☐`, and shapes arrive in placement order rather than reading order. `.xlsx`: one `## <sheet>` heading and table per sheet. Tracked changes and comments are not guaranteed in any format. Two mechanical facts the freshness rule relies on: `markitdown -o` overwrites an existing sidecar cleanly, and pandoc 3.8.2 `.docx` output is byte-deterministic for identical input, so a same-version fixture rebuild reproduces a frozen hash.

When a fact bears on the task at hand — a brief with checklists, a deck whose notes matter — say it in one line at conversion time. Otherwise stay quiet.

### 3.4 Post-conversion sanity

A sidecar body that is whitespace only, or implausibly short for the source's size, is a signal, not a result: the file may be image-only (scanned, needs OCR — out of scope), encrypted, or empty. Say which is likely and ask for a different export rather than proceeding on nothing. No byte floor: a correct three-line brief converts to under 200 bytes.

## 4. `SKILL.md` (verbatim draft)

```markdown
---
name: office-ingest
description: "Use when you are handed or encounter a .docx, .pptx, .xlsx or .xls — a quarterly deck, a stakeholder brief, Word meeting notes — before any command reads it; converts it once into a provenance-stamped markdown sidecar and reuses that sidecar until the source changes."
---

# office-ingest — read Office files through a markdown sidecar

You read Office files through their markdown sidecar, never directly. The sidecar is `<file>.<ext>.md` beside the source, written by markitdown, headed by four provenance keys. PDF is not yours: the harness reads it natively.

## 1. Check for a current sidecar

Hash the source with `python3 -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <source>`. If `<file>.<ext>.md` exists and its `source_sha256` equals the hash, read it and stop here. Otherwise convert.

## 2. Convert

Use the first rung that applies, and no other:

1. `uv` on PATH: `uvx --from "markitdown[docx,pptx,xlsx,xls]" markitdown <source> -o <sidecar>`
2. `markitdown` on PATH: `markitdown <source> -o <sidecar>`
3. Neither: offer once — `uv tool install "markitdown[docx,pptx,xlsx,xls]"` (or `pipx install …`, or `python3 -m pip install --user …`) — and run it only on an explicit yes. On no or on failure, ask for a PDF export or pasted text and proceed on that. Do not claim the file was read.

`markitdown -o` writes the body only. Convert first, then rewrite the sidecar with this header on top of the body it just wrote — exactly these four keys:

    ---
    source: <source filename, relative to the sidecar's directory>
    source_sha256: <hash from step 1>
    converted: <today, ISO date>
    converter: markitdown <version from --version>
    ---

Leave the body as markitdown wrote it. Never edit a sidecar by hand; fix the source or note the correction in your own working notes.

## 3. Match the source's tracking

In a git repo, run `git check-ignore -q <source>`. If the source is ignored and the sidecar is not, propose one `.gitignore` line for the sidecar and write it on confirmation. If the source is tracked, leave the sidecar for the same commit. Never stage or commit. Outside git, do nothing here.

A sidecar carries its source's sensitivity: a converted copy of anything the user called sensitive never lands in a tracked path.

## 4. Say what may have been lost, when it matters

Checkboxes flatten to bullets, fenced code becomes plain text, images are referenced not extracted, tracked changes and comments are not guaranteed. State the fact that bears on the task in one line; otherwise say nothing. A body that is whitespace only, or implausibly short for the source's size, means the file is likely image-only, encrypted or empty — ask for a different export instead of proceeding on nothing.

## Boundaries

- Convert `.docx`, `.pptx`, `.xlsx`, `.xls` only. Hand PDF to the harness's native reader.
- One conversion per source version. A matching hash means no markitdown call.
- The sidecar's name keeps the source extension: `deck.pptx.md`, never `deck.md`.
- No MCP server, no LLM captioning, no cloud extraction. Local CLI only.
```

## 5. Wiring edits (verbatim)

### 5.1 `.agents/skills/using-awow/SKILL.md` §Route to the moment

Append to the paragraph: *"A `.docx`, `.pptx` or `.xlsx` in hand → the `office-ingest` skill first, then the command the content calls for."*

### 5.2 `.agents/AGENTS.md` §Where to read context

`.agents/AGENTS.md` is not part of the plugin payload (no `AGENTS.md` under `dist/`), so this bullet binds this repo's own sessions and templated adopters; plugin adopters get the route from the `using-awow` reflex in §5.1, which does ship.

New bullet after **Tooling reference**: *"**Office inputs:** a `.docx`, `.pptx`, `.xlsx` or `.xls` anywhere in the context tree is read through its markdown sidecar (`<file>.<ext>.md`) — the `office-ingest` skill creates and refreshes it; never read the binary directly."*

### 5.3 `.agents/commands/refinement-prep.md` §Inputs

Replace *"A slidedeck or document in `input/quarterly/` to extract from"* with *"A slidedeck or document in `{ANCHOR}/context/quarterly/` to extract from — Office files through the `office-ingest` skill; read the sidecar it produces"*.

### 5.4 `.agents/commands/process-transcript.md` §1.1

New bullet after **SRT**: *"**Word notes** (`.docx`) — convert through the `office-ingest` skill, then treat the sidecar as Plain text / Markdown."* The `$ARGUMENTS` sentence gains: *"An Office extension routes through `office-ingest` before parsing."*

### 5.5 `.agents/commands/strategy-flow.md` Phase 0

*"…and everything under `{ANCHOR}/context/quarterly/`"* becomes *"…and everything under `{ANCHOR}/context/quarterly/`, Office files through their `office-ingest` sidecars."*

### 5.6 `context/quarterly/README.md` and `INPUT.md`

New section in both, after **Naming**:

```markdown
## Office files

Drop the `.pptx`, `.docx` or `.xlsx` as-is. On first read the agent writes `<file>.<ext>.md` beside it — markitdown's conversion under a four-key provenance header — and reads that. Commit the pair together; the sidecar is regenerated whenever the source changes, and is never edited by hand. If the source is gitignored, the sidecar is too.
```

### 5.7 `.agents/skills/README.md`

Add `office-ingest` to the base-plugin list, and one example row: *"`office-ingest/` — read `.docx`/`.pptx`/`.xlsx` through a provenance-stamped markdown sidecar written once by markitdown. No script; the CLI is the helper."*

### 5.8 Release notes

No CHANGELOG edit in the feature PR. `tools/release-notes.py` drafts the next version's section from merged PR titles, so the PR title reads `CAU-<id>: Office inputs read through markitdown sidecars (office-ingest skill)`.

## 6. Tests

### 6.1 Scenarios added to `tests/process-transcript/`

Both fixtures follow the suite's convention: an inert file-based board (items inline in `context/tooling/board.md`) plus `setup-progress.md`. `notes.docx` is generated once from `fixtures/office-notes.md` — kept *outside* both scenario directories, because a plaintext twin inside the fixture would let the run read it instead of converting — and committed; because it is frozen, its SHA-256 is a constant recorded in the checks files, and the generator refuses to overwrite it without `--force`.

| Scenario | Fixture | Script (user turns) | `post()` asserts | Rubric asks |
|---|---|---|---|---|
| `docx-notes` | `notes/notes.docx` (a short speaker-attributed meeting); no sidecar | Turn 1: `/process-transcript notes/notes.docx`, walk to Gate 1, stop. Turn 2: run it again on the same file. | `file-exists notes/notes.docx.md`; `file-contains` for each of `source: notes.docx`, `source_sha256: <constant>`, `converted: `, `converter: markitdown ` | Gate 1 reached with speakers attributed from the sidecar; the binary was never read directly; the tool-call list shows exactly one markitdown invocation across both turns (turn 2 reused the sidecar); no fidelity note (nothing lossy in the fixture); the sidecar is left untracked and no `git add`/`commit` appears in the tool-call list |
| `stale-sidecar` | As above plus a pre-written `notes/notes.docx.md` whose `source_sha256` is 64 zeros and whose body is the single line `STALE` | `/process-transcript notes/notes.docx` | `file-contains notes/notes.docx.md "source_sha256: <constant>"`; `file-not-contains notes/notes.docx.md 0000000000000000`; `file-not-contains notes/notes.docx.md STALE` | Re-converted without asking; the stale body was never treated as the meeting |

Each scenario ships an executable `setup/<scenario>.sh` that `git init -q`s the scratch (its existence suppresses the runner's default, so it owns git-ness) and then exits 1 unless `uv` or `markitdown` is on PATH — so a machine without either composes `indeterminate (stage: setup)`, never `fail`.

### 6.2 Static

`python tools/gather.py --check` (new skill in payload); `python tools/validate-evals.py` (new scenarios wired). No pytest: there is no script.

## 7. Acceptance criteria, restated testable

1. Handing a command a `.docx`, `.pptx` or `.xlsx` produces `<file>.<ext>.md` beside it with the four-key provenance header, and the command proceeds from the sidecar. (`docx-notes`)
2. A source whose hash matches its sidecar is not reconverted; markitdown is not invoked. (`docx-notes` turn 2: rubric over the tool-call list — deliberately one witness; `post()` cannot see tool calls, so this criterion is judge-only and the suite README says so)
3. A source whose hash differs from its sidecar is reconverted and the header refreshed. (`stale-sidecar`)
4. Sidecar tracking follows the source: ignored source → one proposed `.gitignore` line; tracked source → sidecar left for the same commit; nothing staged or committed by the skill. (the "nothing staged or committed" clause: `docx-notes` rubric `[no-commit]` — the setup hook commits the fixture, so the sidecar must end up untracked; the ignored-source branch: manual walk)
5. With neither `uv` nor `markitdown` available, the agent offers exactly one install path and, on decline, asks for a PDF export or pasted text instead of failing or pretending. (manual walk)
6. refinement-prep, process-transcript and strategy-flow name the skill at their input step; refinement-prep points at `{ANCHOR}/context/quarterly/`; the quarterly README and INPUT guide document the sidecar. (diff review)

## 8. Decisions closed

- **D1 — Sidecar beside the source, same tracking.** Cross-harness readability (the M365 agent reads context as text from git) outweighs the repo footprint; privacy rides on the source's own tracking decision. (User, 2026-09-04.)
- **D2 — CLI, not MCP.** `markitdown-mcp` is alpha; the CLI is already the deterministic helper, so the skill ships no wrapper script.
- **D3 — `uvx` first.** Zero-install and isolated; `uv` is already this repo's Python tool. PATH install second; an install offer third; a human fallback last.
- **D4 — Extension-preserving sidecar name.** Prevents collisions and shows provenance in a listing.
- **D5 — SHA-256, not mtime.** Checkout and copy change mtime; only content changes the hash.
- **D6 — PDF stays native.** The harness reads it already; scanned PDFs are an OCR problem outside this spec.
- **D7 — The skill never stages or commits.** It writes files; the human, or the flow that owns the commit, lands them.
- **D8 — Two skills, not one.** Ingestion and rendering have different audiences and dependency profiles; every skill description loads into every session. (User approved packaging option 2, 2026-09-04.)

## 9. Board item draft

Per `workitem-write`: title pattern `Implement {thing}` (new capability); labels `type:feature`, `area:process`; team Cauchyio; no project; priority, estimate and cycle left to humans.

**Title:** Implement Office-file ingestion through markitdown sidecars

**Body:**

Commands that read team inputs can open `.docx`, `.pptx` and `.xlsx` files: markitdown converts each once into a provenance-stamped markdown sidecar beside the source, so quarterly decks and Word briefs stop being invisible to the agent.

Acceptance criteria

- [ ] An Office file handed to a command gets `<file>.<ext>.md` beside it with `source`, `source_sha256`, `converted`, `converter` in its header, and the command reads the sidecar.
- [ ] An unchanged source is not reconverted; a changed source is, with the header refreshed.
- [ ] The sidecar's git tracking follows the source; the skill stages and commits nothing.
- [ ] With no `uv` and no `markitdown`, the agent offers one install path and otherwise asks for a PDF or pasted text.
- [ ] refinement-prep, process-transcript and strategy-flow route Office inputs through the skill; the quarterly README documents the sidecar.

Spec: `proposals/office-ingest-design.md`.

## 10. Amendments at implementation (2026-09-04)

Found by the build on branch `arie/cau-1526-implement-office-file-ingestion-through-markitdown-sidecars`; folded into the sections above and into the built files.

1. **§3.3 verified for `.pptx` and `.xlsx`.** The upstream claim held and was understated: PowerPoint loses inline formatting, bullet markers and reading order. Text replaced with the observed behaviour.
2. **§3.4 byte floor dropped.** A correct three-line brief converts to 175 bytes; "~200 bytes" was a false-positive rule. Spec and `SKILL.md` now say "whitespace only, or implausibly short for the source's size".
3. **§4 two-step write made explicit.** `markitdown -o` writes the body only; the header is prepended afterwards. Spec and `SKILL.md` say so.
4. **§5.2 reach corrected.** `.agents/AGENTS.md` does not ship in the payload; plugin adopters get the route from the `using-awow` reflex.
5. **§5.6 "four-line" → "four-key".** Four keys over six lines including the fences.
6. **§6.1 fixture placement.** The plaintext source of `notes.docx` lives at `tests/process-transcript/fixtures/office-notes.md`, outside both scenario directories: the runner copies a whole scenario directory, and a `.md` twin beside the `.docx` would let the run skip the conversion under test. Turns are separated by blank lines so pandoc emits one paragraph per speaker.
7. **§6.1 freeze guard.** `make-office-fixtures.sh` refuses to overwrite `notes.docx` without `--force`, so the constant hash in the checks files cannot silently desynchronise.
8. **§7.2 is judge-only by design**, stated explicitly. **§7.4's "nothing staged or committed"** gained a rubric question (`[no-commit]`) in `docx-notes`; the ignored-source branch stays a manual walk.
9. **`context/quarterly/` is team data, not payload** (`tools/gather.py` classifies it under `TEAM_DATA_CONTEXT_PATHS`), so §5.6's text reaches templated adopters only. Accepted: the convention is documented where the files are dropped.
10. **Accepted as written:** §5.4's process-transcript bullet names `.docx` only — the `$ARGUMENTS` sentence already routes every Office extension; a `.pptx` meeting note is not a real case.
11. **Tooling note:** this machine has `python3` only, no `python`; the gate list in the plan and in `.claude/CLAUDE.md` is written as `python …` and runs as `python3`.
