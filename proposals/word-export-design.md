# Word Export in `/artifact` — Design Spec

**Status:** Draft by Arie, 2026-09-04. Approved in conversation at the design gate; awaiting written review.
Board item: [CAU-1525](https://linear.app/cauchyio/issue/CAU-1525/add-a-word-export-target-to-artifact) (created 2026-09-04 from the §9 draft).
Companion: [office-ingest-design.md](office-ingest-design.md) (the inbound direction: Office → markdown). The two specs are independent; this one is sequenced first.
Closes the deferred §3.7 "render skill" of [design-system-capability.md](design-system-capability.md).

**Goal:** `/artifact` can emit a Word document (`.docx`) from the agreed markdown, styled by the team's own Word template when one is registered, verified structurally before it is called done, and never silently dropped when the tool is missing. Three things drive everything here: (1) the output is generated from the markdown, never from the HTML; (2) house style comes from a *registered* reference docx, not a generated one; (3) the render mechanics for every target — Playwright layout check, Chrome PDF, pandoc Word — move into one skill that `/artifact` delegates to. Nothing is left open.

## 1. Scope and non-goals

In scope:

- One new frontmatter key in `context/tooling/design-system.md`: `word_reference`.
- One new sub-step in `.agents/commands/design-system.md` Phase 3 (§3.2b, register a Word template) and one line in its Gate 3 block.
- Edits to `.agents/commands/artifact.md`: Phase 0 reads the new key; Phase 2 asks for the target(s) and states the Word constraints; Phase 3 and Phase 4 delegate rendering and verification per target to the new skill; Phase 5 commits every emitted target; two new behavioural boundaries.
- One new packaged skill `.agents/skills/artifact-render/` — `SKILL.md` plus `scripts/docx_outline.py` (stdlib only).
- One rule broadened in `.agents/AGENTS.md` ("When you produce an HTML artifact" → styled artifacts, HTML or Word). `tools/bootstrap-claude-md.py` does not carry this rule (verified 2026-09-04), so nothing changes there.
- One-line mentions in `context/tooling/README.md`, the body of `context/tooling/design-system.md`, and `.agents/skills/README.md`.
- A new eval suite `tests/artifact/` (three scenarios, one in an `env/` container), one stdlib test script for `docx_outline.py` wired into CI, and one new check verb in `tests/checks-prelude.sh`.
- No CHANGELOG edit: release sections are drafted from merged PR titles at version bump, so this PR's title carries the board id and a one-line summary.
- Implementation sequencing: [plans/2026-09-04-word-export.md](plans/2026-09-04-word-export.md).

Non-goals, stated so nobody re-opens them:

- **PowerPoint output.** pandoc drives `.pptx` through the same reference-doc mechanism, so this is the named follow-on once Word has shipped. Decks keep going out as HTML + PDF.
- **Generating a reference docx from the design tokens.** Teams register the branded template they already have. Token-derived Word styling is a separate item if anyone ever wants it.
- **Word → markdown.** That is [office-ingest-design.md](office-ingest-design.md).
- **Tracked changes, comments, footnote styling, citations.** Plain document body only.
- **LibreOffice as a dependency.** It is used for an optional visual check when present, never required.
- **Converting HTML to Word.** pandoc's HTML reader drops semantics the markdown already has; the markdown is the agreed source anyway.

## 2. The reference docx

### 2.1 Pointer key

`context/tooling/design-system.md` frontmatter gains one key, after `templates_dir`:

```yaml
word_reference: ""    # in-repo  → context/design-system/templates/word/reference.docx
                      # external → e.g. ~/repos/design/word/reference.docx (access: local-path applies)
                      # empty    → pandoc's stock styles; /artifact says so when it emits Word
```

Resolution follows `path:` exactly: in-repo paths are relative to the repo root; external paths are absolute and read from the filesystem when `access: local-path`. The shipped stub carries the key empty. `mode: absent` implies the key is ignored.

### 2.2 What pandoc takes from it (normative, verified 2026-09-04 on pandoc 3.8.2)

pandoc reads the reference docx for its **styles** (paragraph, character and table styles matched by name: Title, Heading 1–6, Body Text, First Paragraph, Block Text, Source Code, Table, Compact, Hyperlink, Caption, …), its **page setup** (size, margins), its **headers and footers**, its **theme and fonts**, and its **numbering definitions**. It **ignores the body**. Consequence: a cover page, boilerplate paragraph or table of contents that lives in the template's body does not appear in generated documents. pandoc's own default reference doc (`pandoc -o ref.docx --print-default-data-file reference.docx`) carries `styles.xml` and no header or footer parts, which is why a team template is what brings letterhead.

### 2.3 Registration step in `/design-system` (verbatim, inserted after §3.2)

```markdown
### 3.2b Register a Word template

Ask whether the team has a branded Word template. If not, leave `word_reference` empty and move on; pandoc's stock styles apply and `/artifact` says so whenever it emits Word.

If yes, take the file the user names. Require `.docx`. When handed a `.dotx`, ask the user to open it in Word and save it as `.docx` first — do not rename or convert it yourself. In-repo: copy it to `{ANCHOR}/context/design-system/templates/word/reference.docx`. External: record its absolute path and rely on `access: local-path`.

Probe it once before Gate 3: write a three-line markdown sample (a heading, a paragraph, a two-row table) to scratch and run `pandoc <sample>.md --from gfm --to docx --reference-doc=<path> -o <scratch>/probe.docx`. Exit 0 means usable. Any other exit means the file is not a usable reference doc: report pandoc's message verbatim and leave `word_reference` empty.

Tell the user what carries over and what does not: pandoc takes the template's styles, page setup, headers and footers and ignores its body, so a cover page or boilerplate text in the template will not appear in generated documents.
```

Gate 3 block gains one line after `Templates:`:

```
Word template: [<path>  (probe: ok)  |  none — pandoc defaults]
```

§3.3 ("Wire the pointer") gains `word_reference` in its list of keys to set.

## 3. `/artifact` changes

### 3.1 Phase 0 — resolve the design system

Add: *"Read `word_reference` as well. Empty or `mode: absent` means Word output uses pandoc's stock styles, and you say so in the run's final report."*

### 3.2 Phase 2 — target choice and Word constraints (verbatim, inserted before the content gate)

```markdown
**Target.** Before you draft, ask which outputs the user wants: HTML + PDF (the default), Word (`.docx`), or both. Record the answer; it shapes the content.

When Word is among the targets, state these constraints before drafting and hold the content to them:

- Every diagram is a PNG or a table. HTML/CSS diagrams do not survive into Word; render them to PNG per the `artifact-render` skill or replace them with a table.
- One H1 or a `title:` metadata line, never both — pandoc emits a Title *and* a Heading 1 otherwise.
- Images are referenced by a path relative to the markdown file's directory.
- No slide-style layouts, columns, or positioned elements. Headings, paragraphs, lists, tables, images, code.

Run `pandoc --version` the moment Word is chosen. Anything but exit 0 — absent or broken — means you follow the `artifact-render` skill's tool-absent rule now, before content work, so the user can decide the target with the fact in hand.
```

The gate question becomes *"content agreed — generate the <targets>?"*.

### 3.3 Phase 3 — generate the targets

Retitle to **"Phase 3 — Generate the targets"**. The existing HTML text stays as the HTML sub-section. Add:

```markdown
**Word.** Generate the Word document from the agreed markdown per the `artifact-render` skill §Word. Do not generate HTML first and convert it; the markdown is the source.
```

### 3.4 Phase 4 — verify and export

Replace the four numbered steps with a delegation, keeping the fix loop:

```markdown
Verify and export every target per the `artifact-render` skill: HTML gets the Playwright layout check and the Chrome headless PDF; Word gets the outline check, the round trip, and the visual check when LibreOffice is present. Fix overflow or outline mismatches at the source (markdown or template), regenerate, re-verify. This loop is expected; do not ship a clipped slide or a document whose outline does not match its source.
```

### 3.5 Phase 5 — land

"Commit and push the markdown source, the HTML, and the PDF" becomes "Commit and push the markdown source and every emitted target file (HTML, PDF, `.docx`)". The working-directory confirmation rule is unchanged.

### 3.6 Behavioural boundaries (two added)

- **Word comes from the markdown, never from the HTML.** If the HTML and the Word document disagree, the markdown was edited after one of them was generated — regenerate both.
- **A missing render tool is a stated fallback, never a silent one.** When pandoc is absent, the final report names the target that was not produced and why.

## 4. The `artifact-render` skill

### 4.1 Shape

```
.agents/skills/artifact-render/
├── SKILL.md
└── scripts/
    └── docx_outline.py     # stdlib only
```

Frontmatter:

```yaml
---
name: artifact-render
description: "Use when an /artifact run reaches rendering or verification — check HTML layout with Playwright, export PDF via Chrome headless, emit Word via pandoc with the team's reference doc — or when one of those tools is missing."
---
```

The skill is mechanics only. Content decisions, the design-system read and the board steps stay in `/artifact`. `channel:` is unset (ships in the base plugin on every harness).

### 4.2 Sections

**§HTML layout verification** — moved verbatim from `artifact.md` Phase 4 step 2: open in a browser, inspect computed layout and overflow with Playwright, do not eyeball.

**§PDF export** — moved verbatim from Phase 4 step 3: Chrome headless print-to-PDF; modern CSS survives, WeasyPrint does not; use the template's print CSS.

**§Diagrams to PNG** — one recipe: with Playwright, load the HTML fragment that carries the diagram, take an element screenshot at device scale factor 2, save as PNG beside the markdown, reference it from the markdown by relative path.

**§Word** (new, normative):

```markdown
## Word

Generate from the agreed markdown:

    pandoc <artifact>.md --from gfm --to docx \
      [--reference-doc=<word_reference>] \
      --resource-path=<directory of the markdown> \
      -o <artifact>.docx

Pass `--reference-doc` only when `word_reference` is set; add `--toc` only when the user asked for a table of contents. Do not add filters or Lua scripts.

Verify in this order; stop at the first failure, fix at the source, regenerate:

1. **Outline.** Run `python3 <skill-dir>/scripts/docx_outline.py <artifact>.docx`. Compare its JSON to the markdown: every markdown heading appears at the same level in the same order; table count and image count match. A mismatch is a generation defect — fix the markdown or the command, never the `.docx`.
2. **Round trip.** Run `pandoc <artifact>.docx --from docx --to gfm` and diff against the source, ignoring whitespace, front matter, task-list markers (`- [ ]` returns as a plain bullet) and code-fence form. Report a missing paragraph, list item or table row to the user; ignore formatting-only noise.
3. **Visual, only when present.** If `soffice` is on PATH, run `soffice --headless --convert-to pdf <artifact>.docx --outdir <dir>` and open the PDF to check page breaks, header and footer. Absent: say the visual check was skipped and why. Never ask the user to install LibreOffice for this.

State in the final report which reference doc was applied, or that pandoc's stock styles were used.

### Tool absent

When `pandoc --version` does not exit 0 — not installed, or installed and broken — say so and offer the install for the platform, once:

- macOS: `brew install pandoc`
- Debian/Ubuntu: `sudo apt install pandoc`
- Windows: `winget install --id JohnMacFarlane.Pandoc` (or `choco install pandoc`)
- Anything else: https://pandoc.org/installing.html

Run it only on an explicit yes. On no, or on a failed install, produce the other targets and state in the final report that the Word target was not produced and why. Never drop the target silently. Minimum version: pandoc 2.6 (task lists in `gfm`); verified on 3.8.2.
```

### 4.3 `scripts/docx_outline.py` contract

- **Input:** one path to a `.docx`. **Output:** one JSON object on stdout:
  `{"headings":[{"level":1,"text":"…"},…],"tables":N,"images":N}`. Title style is level 0.
- **Heading detection resolves style names, not IDs.** Parse `word/styles.xml` into a map `styleId → w:name`. A paragraph is a heading when its `w:pStyle` resolves to a name matching `^title$` or `^heading (\d)$` case-insensitively. Word stores built-in style names in English internally regardless of UI language, and a team template may carry localised or renamed style IDs, so keying on the ID is wrong.
- **Tables:** count of `w:tbl` in `word/document.xml`. **Images:** count of `a:blip`.
- **Dependencies:** `zipfile`, `xml.etree.ElementTree`, `json`, `sys`, `re`. Nothing else.
- **Exit codes:** 0 success; 2 file missing, not a zip, or no `word/document.xml`, with one line on stderr.
- Verified shape on the 2026-09-04 probe: `[('Title','Probe brief'),('Heading1','Probe brief'),('Heading2','Intent'),('Heading2','Acceptance criteria')]`, `tables: 1`, `images: 0` — the duplicated title is exactly the defect §3.2's "one H1 or a `title:` line" rule prevents.

## 5. Documentation edits

### 5.1 `.agents/AGENTS.md` — rule broadened (verbatim replacement of the section)

```markdown
## When you produce a styled artifact (HTML or Word)

Before generating any styled artifact — a presentation, a solution design, a blog post, a styled digest, a one-pager, a Word document — read `context/tooling/design-system.md`.

- If `mode:` is `absent`, proceed with plain defaults; do not invent or enforce a house style.
- If `mode:` is `in-repo` or `external`, **read the source file named in `path:` and adopt its tokens and templates. Do not invent styling.** Re-read the source each time — the token summary in the pointer is a convenience cache and can drift. When `mode: external` and `access: local-path`, read the file from the filesystem (a private design repo will 404 over MCP); do not guess its contents.
- For Word output, `word_reference` names the pandoc reference doc. Empty means pandoc's stock styles, and you say so in the run's report.

Drafting content first in markdown, then generating each target from it, is the expected order — never hand-author a styled artifact when a template exists, and never derive Word from the HTML. `/artifact` drives this end to end; the render mechanics live in the `artifact-render` skill; `/design-system` stands the system up in the first place.
```

### 5.2 `context/tooling/design-system.md` body

In the mode list, after the `mode: external` bullet: *"`word_reference` — optional, any mode but `absent`: the pandoc reference `.docx` that styles Word output. Registered by `/design-system` §3.2b; empty means stock styles."*

### 5.3 `context/tooling/README.md`

The `design-system.md` line gains: *"…and, when registered, the Word reference doc."*

### 5.4 `.agents/skills/README.md`

Add `artifact-render` to the base-plugin skill list in "Two plugins, one source tree", and one row in the examples: *"`artifact-render/` — render and verify `/artifact` targets: Playwright layout check, Chrome PDF, pandoc Word with the team's reference doc. Ships `scripts/docx_outline.py` (stdlib)."*

### 5.5 `proposals/design-system-capability.md`

Status line: *"§3.7 render skill landed as `artifact-render` via [word-export-design.md](word-export-design.md)."* Mirror in the README index row.

### 5.6 Release notes

No CHANGELOG edit in the feature PR. `tools/release-notes.py` drafts the next version's section from merged PR titles, so the PR title reads `CAU-<id>: /artifact emits Word via pandoc; render mechanics move into artifact-render`.

## 6. Tests

### 6.1 Eval suite `tests/artifact/` (`suite.md`: `command: artifact`)

| Scenario | Fixture | Script (user turns) | `post()` asserts | Rubric asks |
|---|---|---|---|---|
Every fixture follows the process-transcript convention: an inert file-based board — items inline in `context/tooling/board.md`, an approved write edits a row — plus `setup-progress.md`; no live board, network or `gh` is touched. `mode: absent` / `in-repo` is set in the fixture's `context/tooling/design-system.md`.

| Scenario | Fixture | Script (user turns) | `post()` asserts | Rubric asks |
|---|---|---|---|---|
| `word-default` | `design-system.md` with `mode: absent`; `brief.md` with three headings (H1, H2, H2), one table, one referenced PNG | Ask for a Word one-pager from `brief.md`; answer "Word"; agree content at the gate | `file-exists out/brief.docx`; `zip-member-contains out/brief.docx word/document.xml "Acceptance criteria"` (the H2 text); `file-absent out/brief.html` | Target asked before drafting; constraints stated; content gate honoured; the `docx_outline.py` output in the evidence bundle shows the three headings in order, `tables: 1`, `images: 1`; final report says stock styles were used |
| `word-reference` | As above but `mode: in-repo`, `word_reference: context/design-system/templates/word/reference.docx`; the fixture reference doc is pandoc's default with `Heading1`'s colour in `styles.xml` set to a sentinel (`FF00AA`) | Same | As above plus `zip-member-contains out/brief.docx word/styles.xml FF00AA` | Report names the reference doc applied |
| `pandoc-absent` | As `word-default`, run in `env/pandoc-absent/` — a `debian:bookworm-slim` container whose `RUN` guard fails the build if the base image ever ships pandoc (the `preflight-no-git` pattern) | Same; decline the install offer; decline the HTML + PDF fallback | `file-absent out/brief.docx`; `file-exists out/brief.md` (content was still agreed and written) | Exactly one install offer naming a platform command; final report states Word was not produced and why; no claim that a `.docx` exists; the fallback was offered, not assumed |

`pandoc-absent` composes `indeterminate (stage: env)` without docker, as `preflight-no-git` does. Fixture binaries (`reference.docx`, the PNG) are small (≈11 KB, ≈1 KB), generated once by a documented command in the suite README, then committed.

### 6.2 Script test — `tests/artifact-render/test_docx_outline.py`

A stdlib script in the shape of `tests/hooks/test_session_start.py` (no pytest; `check(name, cond)`, exit 1 on any failure), wired into `.github/workflows/ci.yml` as one `run:` line. Frozen fixtures under `tests/artifact-render/fixtures/`, generated once by `make-fixtures.sh` (needs pandoc; CI does not) and committed: (a) `sample.docx` yields headings `Probe brief` (1), `Intent` (2), `Acceptance criteria` (2), `tables: 1`, `images: 0`; (b) `renamed.docx` — `sample.docx` with `Heading1`'s styleId renamed to `berschrift1` in both `styles.xml` and `document.xml`, `w:name` untouched — yields the same outline, proving the name-resolution rule; (c) a non-zip path exits 2 with one stderr line; (d) a missing path exits 2. Verified against these fixtures on 2026-09-04.

### 6.3 One new check verb — `tests/checks-prelude.sh`

`zip-member-contains <zip> <member> <needle>` — records `pass` when `<member>` inside the zip contains the literal `<needle>`, `fail` when it does not, and `fail … (unreadable)` when the zip or member cannot be read — the prelude's rule is that a verb records and returns 0, never crashes; the driver owns exit codes. Implemented with an inline `python3` zipfile snippet. The existing six verbs are file-level only, and a `.docx` is a zip; this is the smallest addition that lets `post()` see inside one. Verified 2026-09-04.

### 6.4 Static

`python tools/gather.py --check` must pass with the new skill (its `scripts/` travel with `SKILL.md` per `skill_stubs`); `python tools/validate-evals.py` must pass; `tests/payload-tools` must not flag the `<skill-dir>` reference (it is skill-relative, not an `{AWOW_TOOLS}` reference).

## 7. Acceptance criteria, restated testable

1. With Word chosen at the content gate, `/artifact` emits `<artifact>.docx` from the agreed markdown with no HTML intermediate, and `docx_outline.py` reports the markdown's headings in order and matching table and image counts. (`word-default`)
2. With `word_reference` set, the emitted docx carries the reference doc's styles; with it empty, the final report says pandoc's stock styles were used. (`word-reference`, `word-default`)
3. `/design-system` registers an existing `.docx` as `word_reference`, probes it with pandoc before Gate 3, and sends a `.dotx` back for save-as instead of converting it. (manual walk at implementation; no eval suite exists for `/design-system` yet)
4. When pandoc is absent the agent offers the platform install once and, on decline, emits HTML + PDF and states that Word was not produced. (`pandoc-absent`)
5. The HTML verification and PDF export recipes move out of `artifact.md` into `artifact-render` with no behaviour change; `artifact.md` delegates. (diff review)
6. `gather.py --check`, `validate-evals.py` and `tests/artifact-render/test_docx_outline.py` pass; `/test-awow artifact` runs all three scenarios.

## 8. Decisions closed

- **D1 — Registered, not generated.** The reference docx is the team's existing template. (User, 2026-09-04.)
- **D2 — Word only.** PowerPoint is the named follow-on. (User, 2026-09-04.)
- **D3 — Two skills, commands delegate.** Render mechanics extract into `artifact-render`; this is the §3.7 skill the design-system proposal deferred. (User approved packaging option 2, 2026-09-04.)
- **D4 — Word from markdown, never from HTML.** pandoc's HTML reader loses structure the markdown carries, and the markdown is the agreed source.
- **D5 — Structural verification first.** Outline and round trip are mandatory; the visual check runs only when LibreOffice happens to be present and is never a requirement.
- **D6 — Input dialect `gfm`.** Tables, task lists and fenced code as authored; verified on the probe.
- **D7 — Script lives in the skill.** `.agents/skills/artifact-render/scripts/docx_outline.py`, stdlib only, invoked as `python3 <skill-dir>/scripts/…` per the operational-skill shape in the skills README.
- **D8 — Style names over style IDs.** Heading detection resolves `styleId → w:name` so localised or renamed templates still verify.
- **D9 — Commit the docx like the PDF.** Source plus every emitted target under the confirmed working directory; no new rule.

## 9. Board item draft

Per `workitem-write`: title pattern `Add {thing} to {surface}`; labels `type:feature`, `area:process` (awow way-of-working machinery, as CAU-1422); team Cauchyio; no project (awow items carry none); priority, estimate and cycle left to humans.

**Title:** Add a Word export target to /artifact

**Body:**

`/artifact` emits a Word document from the agreed markdown, styled by a registered reference docx when the team has one, so stakeholder-facing reports and one-pagers no longer need a manual HTML-to-Word step.

Acceptance criteria

- [ ] Choosing Word at the content gate produces `<artifact>.docx` from the markdown; its outline matches the source (headings in order, table and image counts).
- [ ] `/design-system` registers an existing `.docx` as the pandoc reference doc in `word_reference`; the emitted document carries its styles.
- [ ] With no reference doc, or with pandoc absent, the run states the fallback (stock styles / HTML + PDF only) instead of failing silently.
- [ ] Render mechanics — Playwright layout check, Chrome PDF, pandoc Word — live in one `artifact-render` skill that `/artifact` delegates to.
- [ ] `tests/artifact/` covers the default, reference-doc and pandoc-absent scenarios.

Spec: `proposals/word-export-design.md`. Follow-on, not in scope: PowerPoint via the same mechanism.
