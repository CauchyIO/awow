# Word Export in `/artifact` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/artifact` can emit a `.docx` from the agreed markdown via pandoc, styled by a reference doc `/design-system` registers, verified structurally, with every render mechanic living in one new `artifact-render` skill.

**Architecture:** Prompt edits (two commands, one rule) delegate rendering to a new packaged skill whose only code is a stdlib `docx_outline.py`. Verification is a three-scenario eval suite (`tests/artifact/`, one scenario in a docker `env/`) plus one stdlib unit test for the script and one new check verb in the shared prelude. No new Python dependencies; pandoc is an external binary the skill probes for and degrades without.

**Tech Stack:** pandoc ≥ 2.6 (verified 3.8.2), Python 3.10+ stdlib (`zipfile`, `xml.etree`), bash eval suites under `tests/`, `tools/gather.py` payload build.

**Spec:** `proposals/word-export-design.md` — every verbatim prompt block below is quoted from it; when the two disagree, the spec wins and this plan gets fixed.

**Board item:** [CAU-1525](https://linear.app/cauchyio/issue/CAU-1525/add-a-word-export-target-to-artifact). Branch: `arie/cau-1525-add-a-word-export-target-to-artifact`.

## Global Constraints

- Word output is generated from the markdown with `--from gfm --to docx`; never from HTML. (spec D4, D6)
- `--reference-doc` is passed only when `word_reference` is non-empty; `--toc` only when the user asked. (spec §4.2)
- Heading detection resolves `styleId → w:name`; matching on the ID alone is a defect. (spec D8)
- Verification order: outline → round trip → visual-only-if-`soffice`. LibreOffice is never required. (spec D5)
- Tool-absent check is `pandoc --version` exit 0; anything else triggers the one-time install offer. (spec §3.2, §4.2)
- Skill scripts are stdlib only and invoked as `python3 <skill-dir>/scripts/docx_outline.py`. (spec D7)
- Prompt bodies under `.agents/` use `{ANCHOR}` / `{AWOW_ROOT}` tokens, never bare `context/` or `tools/` (`python tools/lint-paths.py` gates CI).
- Prompt voice: second person, imperative, two sentences per rule max (`.agents/skills/agent-directive-voice.md`).
- Eval-suite exec bits: `run-checks.sh` and `setup/*.sh` executable; `checks-prelude.sh` and `checks/*.sh` NOT executable. `python tools/validate-evals.py` enforces this.
- Test files are stdlib scripts (no pytest) wired into `.github/workflows/ci.yml` one `run:` line each.
- No CHANGELOG edit: the release PR drafts it from merged PR titles. This PR's title carries `CAU-1525:` and a one-line summary.
- Commit trailer on every commit:
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`
  `Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej`

---

## File structure

| Path | Responsibility | Task |
|---|---|---|
| `tests/checks-prelude.sh` | + `zip-member-contains` verb | 1 |
| `.agents/skills/artifact-render/scripts/docx_outline.py` | structural outline of a `.docx` as JSON | 2 |
| `tests/artifact-render/test_docx_outline.py`, `tests/artifact-render/fixtures/{make-fixtures.sh,sample.md,sample.docx,renamed.docx}` | unit test + frozen fixtures for the script | 2 |
| `.github/workflows/ci.yml` | + one `run:` line | 2 |
| `.agents/skills/artifact-render/SKILL.md` | render + verify recipes for HTML, PDF, Word; tool-absent rule | 3 |
| `.agents/skills/README.md` | list + example row for the new skill | 3 |
| `context/tooling/design-system.md`, `context/tooling/README.md` | `word_reference` key and its one-line description | 4 |
| `.agents/commands/design-system.md` | §3.2b register a Word template; Gate 3 line; §3.3 key | 5 |
| `.agents/commands/artifact.md` | target choice, Word constraints, delegation to the skill, boundaries | 6 |
| `.agents/AGENTS.md` | rule broadened to styled artifacts (HTML or Word) | 7 |
| `tests/artifact/**` | eval suite: `word-default`, `word-reference`, `pandoc-absent` | 8 |
| `proposals/design-system-capability.md`, `proposals/README.md`, `proposals/word-export-design.md` | status bookkeeping | 9 |

---

### Task 0: Branch and board

**Files:** none (git + board only)

- [ ] **Step 1: Confirm the board item.** CAU-1525 exists and is In Progress.
- [ ] **Step 2: Branch.** From `arie/word-export-office-ingest-specs` (which carries the spec and this plan): `git checkout -b arie/cau-1525-add-a-word-export-target-to-artifact`.
- [ ] **Step 3: Move the item to In Progress** with a one-line comment: "Implementation started; plan at proposals/plans/2026-09-04-word-export.md".

---

### Task 1: `zip-member-contains` check verb

**Files:**
- Modify: `tests/checks-prelude.sh` (append after `file-not-contains`)

**Interfaces:**
- Produces: bash function `zip-member-contains <zip> <member> <needle>` — records `CHECK pass|fail zip-member-contains …`; an unreadable zip or missing member records `fail … (unreadable)`; always returns 0, like every verb.

- [ ] **Step 1: Write the failing probe** — in a scratch dir, build a zip with one member and source the prelude:

```bash
cd "$(mktemp -d)" && printf 'hello world' > m.txt && python3 -c "import zipfile;zipfile.ZipFile('t.zip','w').write('m.txt')"
bash -c 'source /Users/arie/repos/cauchy/awow/tests/checks-prelude.sh; zip-member-contains t.zip m.txt world'
```

Expected: `bash: zip-member-contains: command not found`.

- [ ] **Step 2: Append the verb** to `tests/checks-prelude.sh`:

```bash

# zip-member-contains <zip> <member> <needle> — the zip member (e.g. a .docx's
# word/document.xml) must contain the literal needle. An unreadable zip or a
# missing member records fail with a reason, never a crash (verbs return 0).
zip-member-contains() {
  local rc
  python3 - "$1" "$2" "$3" <<'PY' 2>/dev/null
import sys, zipfile
z, m, needle = sys.argv[1:4]
try:
    data = zipfile.ZipFile(z).read(m).decode("utf-8", "replace")
except (FileNotFoundError, zipfile.BadZipFile, KeyError):
    sys.exit(127)
sys.exit(0 if needle in data else 1)
PY
  rc=$?
  if [ "$rc" -eq 0 ]; then _record pass "zip-member-contains $1 $2 $3"
  elif [ "$rc" -eq 127 ]; then _record fail "zip-member-contains $1 $2 $3 (unreadable)"
  else _record fail "zip-member-contains $1 $2 $3"; fi
}
```

- [ ] **Step 3: Re-run the probe** from Step 1 three ways: `… world` → `CHECK	pass`; `… nope` → `CHECK	fail`; `zip-member-contains m.txt m.txt x` → `CHECK	fail … (unreadable)`.
- [ ] **Step 4: Static gate.** `python tools/validate-evals.py` → exit 0 (prelude still not executable, passes `bash -n`).
- [ ] **Step 5: Commit.**

```bash
git add tests/checks-prelude.sh
git commit -m "CAU-1525: add the zip-member-contains check verb so post() can see inside a .docx" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 2: `docx_outline.py` with its unit test and frozen fixtures

**Files:**
- Create: `.agents/skills/artifact-render/scripts/docx_outline.py`
- Create: `tests/artifact-render/fixtures/make-fixtures.sh` (executable), `tests/artifact-render/fixtures/sample.md`, `tests/artifact-render/fixtures/sample.docx`, `tests/artifact-render/fixtures/renamed.docx`
- Create: `tests/artifact-render/test_docx_outline.py`
- Modify: `.github/workflows/ci.yml` (one line after the `tests/hooks/test_lifecycle_seam_check.py` step)

**Interfaces:**
- Produces: CLI `python3 docx_outline.py <file.docx>` → stdout JSON `{"headings":[{"level":int,"text":str},…],"tables":int,"images":int}`, exit 0; exit 2 + one stderr line on missing file, non-zip, or no `word/document.xml`. Title style is level 0.

- [ ] **Step 1: Write the fixture source** `tests/artifact-render/fixtures/sample.md`:

```markdown
# Probe brief

## Intent

A short paragraph with **bold** and a [link](https://example.com).

## Acceptance criteria

- [ ] First criterion
- [ ] Second criterion

| Column A | Column B |
|---|---|
| one | two |
| three | four |
```

- [ ] **Step 2: Write the fixture generator** `tests/artifact-render/fixtures/make-fixtures.sh` and `chmod +x` it. It needs pandoc locally; CI never runs it — the outputs are committed.

```bash
#!/usr/bin/env bash
# Regenerate the frozen .docx fixtures for tests/artifact-render. Needs pandoc.
# renamed.docx is sample.docx with Heading1's styleId renamed to "berschrift1"
# in both styles.xml and document.xml — the w:name stays "heading 1", which is
# exactly the case docx_outline.py must still classify as level 1.
set -euo pipefail
cd "$(dirname "$0")"
pandoc sample.md --from gfm --to docx -o sample.docx
python3 - <<'PY'
import zipfile
with zipfile.ZipFile("sample.docx") as zin, zipfile.ZipFile("renamed.docx", "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in ("word/styles.xml", "word/document.xml"):
            data = data.replace(b'w:styleId="Heading1"', b'w:styleId="berschrift1"').replace(b'w:val="Heading1"', b'w:val="berschrift1"')
        zout.writestr(item, data)
PY
echo "fixtures regenerated: sample.docx renamed.docx"
```

Run it: `tests/artifact-render/fixtures/make-fixtures.sh`. Confirm `git check-ignore tests/artifact-render/fixtures/sample.docx` prints nothing (fixtures must not be swallowed by `.gitignore`).

- [ ] **Step 3: Write the failing test** `tests/artifact-render/test_docx_outline.py`:

```python
#!/usr/bin/env python3
"""Black-box test for the artifact-render skill's docx_outline.py.

Stdlib only, no pytest. Runs the script as a subprocess over frozen fixtures
(regenerate with fixtures/make-fixtures.sh — needs pandoc; CI does not).
    python3 tests/artifact-render/test_docx_outline.py
Exits 0 if all pass, 1 otherwise.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(ROOT, ".agents", "skills", "artifact-render", "scripts", "docx_outline.py")
FIX = os.path.join(os.path.dirname(__file__), "fixtures")

EXPECTED_HEADINGS = [
    {"level": 1, "text": "Probe brief"},
    {"level": 2, "text": "Intent"},
    {"level": 2, "text": "Acceptance criteria"},
]

failures = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        failures.append(name)


def run(path):
    return subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True)


r = run(os.path.join(FIX, "sample.docx"))
check("sample: exit 0", r.returncode == 0)
out = json.loads(r.stdout) if r.returncode == 0 else {}
check("sample: headings in order", out.get("headings") == EXPECTED_HEADINGS)
check("sample: one table", out.get("tables") == 1)
check("sample: no images", out.get("images") == 0)

r = run(os.path.join(FIX, "renamed.docx"))
out = json.loads(r.stdout) if r.returncode == 0 else {}
check("renamed styleId still resolves by name", out.get("headings") == EXPECTED_HEADINGS)

r = run(os.path.join(FIX, "sample.md"))
check("non-zip: exit 2", r.returncode == 2)
check("non-zip: one stderr line", r.stderr.count("\n") == 1)

r = run(os.path.join(FIX, "does-not-exist.docx"))
check("missing: exit 2", r.returncode == 2)

sys.exit(1 if failures else 0)
```

- [ ] **Step 4: Run it to see it fail.** `python3 tests/artifact-render/test_docx_outline.py` → every line `FAIL` (script missing), exit 1.

- [ ] **Step 5: Write the script** `.agents/skills/artifact-render/scripts/docx_outline.py`:

```python
#!/usr/bin/env python3
"""Print the structural outline of a .docx as JSON: headings (by resolved
style *name*, so renamed or localised style IDs still count), table count,
image count. Stdlib only. Used by the artifact-render skill to verify a
pandoc-generated Word document against its markdown source.

Usage: python3 docx_outline.py <file.docx>
Exit 0 with JSON on stdout; exit 2 with one line on stderr when the file is
missing, not a zip, or has no word/document.xml.
"""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
HEADING_NAME = re.compile(r"^(?:heading\s*(\d))$", re.IGNORECASE)
TITLE_NAME = re.compile(r"^title$", re.IGNORECASE)


def style_names(zf):
    """styleId -> canonical w:name from word/styles.xml (empty if absent)."""
    try:
        root = ET.fromstring(zf.read("word/styles.xml"))
    except KeyError:
        return {}
    names = {}
    for style in root.iter(f"{{{W}}}style"):
        sid = style.get(f"{{{W}}}styleId")
        name_el = style.find(f"{{{W}}}name")
        if sid and name_el is not None:
            names[sid] = name_el.get(f"{{{W}}}val", "")
    return names


def heading_level(style_id, names):
    name = names.get(style_id, style_id or "")
    if TITLE_NAME.match(name):
        return 0
    m = HEADING_NAME.match(name)
    return int(m.group(1)) if m else None


def outline(path):
    with zipfile.ZipFile(path) as zf:
        names = style_names(zf)
        root = ET.fromstring(zf.read("word/document.xml"))
    headings = []
    for p in root.iter(f"{{{W}}}p"):
        pstyle = p.find(f"{{{W}}}pPr/{{{W}}}pStyle")
        if pstyle is None:
            continue
        level = heading_level(pstyle.get(f"{{{W}}}val"), names)
        if level is None:
            continue
        text = "".join(t.text or "" for t in p.iter(f"{{{W}}}t"))
        headings.append({"level": level, "text": text})
    return {
        "headings": headings,
        "tables": sum(1 for _ in root.iter(f"{{{W}}}tbl")),
        "images": sum(1 for _ in root.iter(f"{{{A}}}blip")),
    }


def main(argv):
    if len(argv) != 2:
        print("usage: docx_outline.py <file.docx>", file=sys.stderr)
        return 2
    try:
        result = outline(argv[1])
    except (FileNotFoundError, zipfile.BadZipFile, KeyError) as exc:
        print(f"docx_outline: cannot read {argv[1]}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 6: Run the test.** `python3 tests/artifact-render/test_docx_outline.py` → all `PASS`, exit 0. (Verified against these exact fixtures on 2026-09-04.)

- [ ] **Step 7: Wire CI.** In `.github/workflows/ci.yml`, after the step that runs `python3 tests/hooks/test_lifecycle_seam_check.py`, add a step in the same shape:

```yaml
      - name: artifact-render docx_outline
        run: python3 tests/artifact-render/test_docx_outline.py
```

(Match the neighbouring steps' `name:` style exactly; open the file and copy the preceding step's indentation.)

- [ ] **Step 8: Commit.**

```bash
git add .agents/skills/artifact-render/scripts/docx_outline.py tests/artifact-render .github/workflows/ci.yml
git commit -m "CAU-1525: docx_outline.py — stdlib structural outline of a .docx, with frozen fixtures and CI test" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 3: `artifact-render/SKILL.md` and the skills README

**Files:**
- Create: `.agents/skills/artifact-render/SKILL.md`
- Modify: `.agents/skills/README.md` (line 39 sentence "The base plugin keeps the behavioural skills, including …"; the examples list under "Packaged skill")

**Interfaces:**
- Produces: skill name `artifact-render` that `artifact.md` (Task 6) names in Phases 2, 3 and 4.
- Consumes: `scripts/docx_outline.py` from Task 2.

- [ ] **Step 1: Write `SKILL.md`** — the Word section is spec §4.2 verbatim; the HTML and PDF sections lift the text of `artifact.md` Phase 4 steps 1–3 as they stand today:

````markdown
---
name: artifact-render
description: "Use when an /artifact run reaches rendering or verification — check HTML layout with Playwright, export PDF via Chrome headless, emit Word via pandoc with the team's reference doc — or when one of those tools is missing."
---

# artifact-render — render and verify every `/artifact` target

You own the mechanics only. `/artifact` decides content, reads the design system and works the board; you turn the agreed markdown into each target and prove it before anyone calls it done. Read `{ANCHOR}/context/tooling/design-system.md` (falling back to `{AWOW_ROOT}/context/tooling/design-system.md`) for `templates_dir` and `word_reference`; never invent styling.

## HTML — verify layout

1. Open the artifact in a browser (`open <file>.html`).
2. Verify layout with Playwright: inspect computed layout and overflow. Do not eyeball.
3. Fix overflow by tightening padding, splitting dense slides, or reducing font at the source, then regenerate. This loop is expected; do not ship a clipped slide.

## PDF — export from HTML

Export via Chrome headless print-to-PDF. Modern CSS — grid, clamp, viewport units — survives; WeasyPrint does not handle flex or grid, so do not use it. Apply the template's print CSS (for decks, one slide per 1280×720 page). Open the PDF and check for overflow before reporting.

## Diagrams to PNG (for Word)

With Playwright, load the HTML fragment that carries the diagram, take an element screenshot at device scale factor 2, save it as PNG beside the markdown, and reference it from the markdown by relative path. One recipe; do not reach for Mermaid CLI or inline SVG export.

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

## Boundaries

- Word comes from the markdown, never from the HTML.
- Nothing is done until it has been opened, measured, or outlined. A target you have not verified is not finished.
- A missing tool is a stated fallback in the final report, never a silent omission.
````

- [ ] **Step 2: Skills README.** In `.agents/skills/README.md`: (a) in the sentence on line 39 add `artifact-render` to the base-plugin list, after `knowledge-source-routing`; (b) under "Packaged skill — a directory with `SKILL.md` and optional resources", add to the examples list:

```markdown
- [`artifact-render/`](./artifact-render/) — render and verify `/artifact` targets: Playwright layout check, Chrome headless PDF, pandoc Word with the team's reference doc. Ships `scripts/docx_outline.py` (stdlib) for the Word outline check.
```

- [ ] **Step 3: Gates.** `python tools/lint-paths.py` → 0 (no bare `context/`); `python tools/gather.py` then `python tools/gather.py --check` → 0; confirm `dist/skills/artifact-render/scripts/docx_outline.py` exists; `python3 tests/payload-tools/test_tool_references.py` → 0.
- [ ] **Step 4: Commit** (include `dist/` — the payload is tracked):

```bash
git add .agents/skills/artifact-render/SKILL.md .agents/skills/README.md dist
git commit -m "CAU-1525: artifact-render skill — HTML/PDF/Word render and verify recipes in one place" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 4: `word_reference` in the design-system pointer

**Files:**
- Modify: `context/tooling/design-system.md` (frontmatter after `templates_dir`; body mode list)
- Modify: `context/tooling/README.md` (the `design-system.md` bullet)

- [ ] **Step 1: Frontmatter.** After the `templates_dir:` lines add:

```yaml
word_reference: ""    # in-repo  → context/design-system/templates/word/reference.docx
                      # external → e.g. ~/repos/design/word/reference.docx (access: local-path applies)
                      # empty    → pandoc's stock styles; /artifact says so when it emits Word
```

- [ ] **Step 2: Body.** After the `mode: external` bullet add:

```markdown
- **`word_reference`** — optional, any mode but `absent`: the pandoc reference `.docx` that styles Word output. Registered by `/design-system` §3.2b; empty means pandoc's stock styles.
```

- [ ] **Step 3: Tooling README.** Change the `design-system.md` bullet's tail to end: `…Read by every command that produces a styled artifact, and names the Word reference doc when one is registered.`
- [ ] **Step 4: Gates.** `python tools/gather.py --check` (context files ship in the payload; if the check flags the stub, rebuild with `python tools/gather.py` first) and `python3 tests/payload-manifests/test_manifest_integrity.py`.
- [ ] **Step 5: Commit.**

```bash
git add context/tooling/design-system.md context/tooling/README.md dist
git commit -m "CAU-1525: design-system pointer gains word_reference" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 5: `/design-system` registers a Word template

**Files:**
- Modify: `.agents/commands/design-system.md` — insert §3.2b after §3.2 "Build per-artifact-type templates"; extend §3.3's key list; add one line to the Gate 3 block.

- [ ] **Step 1: Insert §3.2b** — the block in spec §2.3 verbatim, starting `### 3.2b Register a Word template` and ending `…will not appear in generated documents.`
- [ ] **Step 2: §3.3.** Change `set `mode`, `path`, `templates_dir`, `access`,` to `set `mode`, `path`, `templates_dir`, `word_reference`, `access`,`.
- [ ] **Step 3: Gate 3 block.** After the `Templates:` line add `Word template: [<path>  (probe: ok)  |  none — pandoc defaults]`.
- [ ] **Step 4: Gates.** `python tools/lint-paths.py`; `python3 tests/command-frontmatter/test_frontmatter.py`; `python tools/gather.py && python tools/gather.py --check`.
- [ ] **Step 5: Commit.**

```bash
git add .agents/commands/design-system.md dist
git commit -m "CAU-1525: /design-system registers the team's Word template as the pandoc reference doc" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 6: `/artifact` chooses targets and delegates rendering

**Files:**
- Modify: `.agents/commands/artifact.md` — frontmatter `description`, Phase 0, Phase 2, Phase 3, Phase 4, Phase 5, Behavioural boundaries.

- [ ] **Step 1: Description.** Replace the frontmatter `description:` with: `"Use when the user asks for a deck, slides, a blog post, one-pager, or report as HTML, PDF or Word — any styled document that should follow the team's house style instead of hand-written CSS."`
- [ ] **Step 2: Phase 0.** Append the paragraph: `Read `word_reference` as well. Empty or `mode: absent` means Word output uses pandoc's stock styles, and you say so in the run's final report.`
- [ ] **Step 3: Phase 2.** Before the paragraph beginning `**Gate:**`, insert the spec §3.2 block verbatim (from `**Target.** Before you draft…` through `…with the fact in hand.`). Change the gate question to *"content agreed — generate the <targets>?"*.
- [ ] **Step 4: Phase 3.** Retitle to `## Phase 3 — Generate the targets`. Prefix the existing body with `**HTML.**` and append:

```markdown
**Word.** Generate the Word document from the agreed markdown per the `artifact-render` skill §Word. Do not generate HTML first and convert it; the markdown is the source.
```

- [ ] **Step 5: Phase 4.** Replace the four numbered steps with:

```markdown
Verify and export every target per the `artifact-render` skill: HTML gets the Playwright layout check and the Chrome headless PDF; Word gets the outline check, the round trip, and the visual check when LibreOffice is present. Fix overflow or outline mismatches at the source (markdown or template), regenerate, re-verify. This loop is expected; do not ship a clipped slide or a document whose outline does not match its source.
```

- [ ] **Step 6: Phase 5.** Replace `Commit and push the markdown source, the HTML, and the PDF.` with `Commit and push the markdown source and every emitted target file (HTML, PDF, `.docx`).`
- [ ] **Step 7: Boundaries.** Append two bullets:

```markdown
- **Word comes from the markdown, never from the HTML.** If the HTML and the Word document disagree, the markdown was edited after one of them was generated — regenerate both.
- **A missing render tool is a stated fallback, never a silent one.** When pandoc is absent, the final report names the target that was not produced and why.
```

- [ ] **Step 8: Gates.** `python tools/lint-paths.py`; `python3 tests/command-frontmatter/test_frontmatter.py`; `python tools/gather.py && python tools/gather.py --check`; `python3 tests/payload-commands/test_command_surface.py`.
- [ ] **Step 9: Commit.**

```bash
git add .agents/commands/artifact.md dist
git commit -m "CAU-1525: /artifact asks for the target, holds Word content to its constraints, delegates rendering to artifact-render" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 7: AGENTS.md rule broadened

**Files:**
- Modify: `.agents/AGENTS.md` — replace the whole `## When you produce an HTML artifact` section.

- [ ] **Step 1: Replace the section** with spec §5.1 verbatim (heading `## When you produce a styled artifact (HTML or Word)` through `…`/design-system` stands the system up in the first place.`).
- [ ] **Step 2: Gates.** `python tools/gather.py --check`; `python3 tests/context-writes/test_context_writes.py`.
- [ ] **Step 3: Commit.**

```bash
git add .agents/AGENTS.md dist
git commit -m "CAU-1525: the styled-artifact rule covers Word and names word_reference" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 8: `tests/artifact/` eval suite

**Files:**
- Create: `tests/artifact/suite.md`, `tests/artifact/README.md`
- Create: `tests/artifact/fixtures/_base/…` (shared source, copied into each scenario by `make-fixtures.sh`), `tests/artifact/fixtures/{word-default,word-reference,pandoc-absent}/…`
- Create: `tests/artifact/fixtures/make-fixtures.sh` (executable)
- Create: `tests/artifact/scripts/{word-default,word-reference,pandoc-absent}.txt`
- Create: `tests/artifact/rubrics/{word-default,word-reference,pandoc-absent}.md`
- Create: `tests/artifact/checks/{word-default,word-reference,pandoc-absent}.sh` (NOT executable)
- Create: `tests/artifact/setup/{word-default,word-reference,pandoc-absent}.sh` (executable)
- Create: `tests/artifact/env/pandoc-absent/Dockerfile`

**Interfaces:**
- Consumes: `zip-member-contains` (Task 1); the prompts from Tasks 5–7.

- [ ] **Step 1: `suite.md`.**

```markdown
---
command: artifact
---

# Suite — artifact

Regression suite for the Word target (spec: `proposals/word-export-design.md`),
exercised through `/artifact`. Every fixture board is an inert file-based
sample: items live inline in `context/tooling/board.md`, so no live board,
network, or `gh` auth is ever touched. Scenarios: `word-default` (target asked,
docx from markdown, stock styles reported), `word-reference` (registered
reference doc applied), `pandoc-absent` (one install offer, honest report; runs
in an `env/` container without pandoc). Setup hooks `git init` the fixture
repos. Invariants, scenarios, and fixture conventions: [README.md](README.md).
```

- [ ] **Step 2: Shared fixture source** under `tests/artifact/fixtures/_base/` (the generator copies it into each scenario dir, so a fix lands once):

`_base/setup-progress.md` — copy `tests/process-transcript/fixtures/plan-gate/setup-progress.md` verbatim.

`_base/context/tooling/board.md`:

```markdown
# Board — sample (frozen test fixture)

- **Tool:** file-based sample board (frozen test fixture — the items ARE the list below; query no live surface; a write edits its row)
- **State machine:** Todo → In Progress → In Review → Done

## Items

| id | title | state | assignee |
|---|---|---|---|
| AR-1 | Write the Q3 stakeholder one-pager | Todo | dana |
```

`_base/context/tooling/design-system.md` — copy the repo's `context/tooling/design-system.md` as of Task 4 (mode `absent`, `word_reference: ""`).

`_base/brief.md`:

```markdown
# Q3 stakeholder one-pager

## Intent

The export job now retries on transient failures and caps payloads at 10 MB, so nightly runs stop paging the on-call.

![Retry flow](diagram.png)

## Acceptance criteria

| Criterion | Status |
|---|---|
| Retry budget wired into the export job | done |
| Payload cap at 10 MB enforced | in review |
```

- [ ] **Step 3: Fixture generator** `tests/artifact/fixtures/make-fixtures.sh` (`chmod +x`). Needs pandoc locally; outputs are committed.

```bash
#!/usr/bin/env bash
# Build the three scenario fixtures from _base/. Needs pandoc (for the
# word-reference reference doc). Re-run after editing anything in _base/.
set -euo pipefail
cd "$(dirname "$0")"
for s in word-default word-reference pandoc-absent; do
  rm -rf "$s"; mkdir -p "$s"; cp -R _base/. "$s/"
done
# A 4x4 opaque PNG, written with stdlib so the fixture is deterministic.
python3 - <<'PY'
import struct, zlib
def chunk(t, d): return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
raw = b"".join(b"\x00" + b"\x50\x6f\xa0" * 4 for _ in range(4))
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
for s in ("word-default", "word-reference", "pandoc-absent"):
    open(f"{s}/diagram.png", "wb").write(png)
PY
# word-reference: in-repo pointer + a reference doc whose Heading 1 colour is a sentinel.
mkdir -p word-reference/context/design-system/templates/word
pandoc -o word-reference/context/design-system/templates/word/reference.docx --print-default-data-file reference.docx
python3 - <<'PY'
import re, zipfile
p = "word-reference/context/design-system/templates/word/reference.docx"
tmp = p + ".tmp"
with zipfile.ZipFile(p) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/styles.xml":
            s = data.decode("utf-8")
            blk = re.search(r'(<w:style[^>]*w:styleId="Heading1".*?</w:style>)', s, re.S).group(1)
            new = re.sub(r'<w:color w:val="[0-9A-Fa-f]+"', '<w:color w:val="FF00AA"', blk) if "<w:color" in blk else blk.replace("<w:rPr>", '<w:rPr><w:color w:val="FF00AA"/>', 1)
            data = s.replace(blk, new).encode("utf-8")
        zout.writestr(item, data)
import os; os.replace(tmp, p)
PY
python3 - <<'PY'
p = "word-reference/context/tooling/design-system.md"
s = open(p).read()
s = s.replace("mode: absent ", "mode: in-repo", 1)
s = s.replace('path: ""  ', 'path: "context/design-system/style-guide.html"', 1)
s = s.replace('templates_dir: ""  ', 'templates_dir: "context/design-system/templates/"', 1)
s = s.replace('word_reference: ""  ', 'word_reference: "context/design-system/templates/word/reference.docx"', 1)
open(p, "w").write(s)
PY
echo "fixtures built"
```

Run it. Then open `word-reference/context/tooling/design-system.md` and confirm the four keys read `in-repo`, the style-guide path, the templates dir and the reference path (the replacements key on the stub's exact spacing; fix by hand if the stub's padding differs). Confirm `git check-ignore tests/artifact/fixtures/word-reference/context/design-system/templates/word/reference.docx` prints nothing.

- [ ] **Step 4: Scripts.**

`scripts/word-default.txt`:

```
# Target asked before drafting; Word chosen; docx generated from the markdown; report states stock styles.
Turn brief.md into a one-pager for the stakeholders. The content is final — use it as-is. Track it under AR-1 on context/tooling/board.md. Put outputs in out/.
Word
yes
```

`scripts/word-reference.txt`:

```
# Registered reference doc applied; report names it.
Turn brief.md into a one-pager for the stakeholders. The content is final — use it as-is. Track it under AR-1 on context/tooling/board.md. Put outputs in out/.
Word
yes
```

`scripts/pandoc-absent.txt`:

```
# No pandoc in the env container: one install offer (declined), HTML+PDF fallback offered (declined), honest final report, no docx claimed.
Turn brief.md into a one-pager for the stakeholders. The content is final — use it as-is. Track it under AR-1 on context/tooling/board.md. Put outputs in out/.
Word
no
no
```

- [ ] **Step 5: Rubrics.**

`rubrics/word-default.md`:

```markdown
# Rubric — word-default

1. [target-first] Did the run ask which output the user wanted (HTML + PDF / Word / both) before drafting or generating anything?
2. [word-constraints] After "Word" was chosen, did the run state the Word constraints (diagrams as PNG or table; one H1 or title line; relative image paths; no slide layouts)?
3. [content-gate] Did the run stop at "content agreed — generate the Word?" and generate only after the user's yes?
4. [from-markdown] Was `out/brief.docx` produced by a pandoc call reading `brief.md` (or a copy of it) with `--from gfm --to docx`, with no HTML generated at any point?
5. [outline] Does the evidence bundle show `docx_outline.py` run over the output, reporting headings `Q3 stakeholder one-pager` (1), `Intent` (2), `Acceptance criteria` (2) in that order, `tables: 1`, `images: 1`?
6. [style-report] Did the final report state that pandoc's stock styles were used (no reference doc)?
7. [board] Was AR-1 moved to In Review with a comment only after the docx existed?
```

`rubrics/word-reference.md`:

```markdown
# Rubric — word-reference

1. [target-first] Did the run ask which output the user wanted before drafting or generating anything?
2. [content-gate] Did the run generate only after the user's yes at the content gate?
3. [reference-applied] Did the pandoc call pass `--reference-doc=` naming `context/design-system/templates/word/reference.docx`?
4. [outline] Does the evidence bundle show `docx_outline.py` run over the output with the three headings in order, `tables: 1`, `images: 1`?
5. [style-report] Did the final report name the reference doc that was applied?
```

`rubrics/pandoc-absent.md`:

```markdown
# Rubric — pandoc-absent

1. [tool-absent] After "Word" was chosen, did the run detect that pandoc was unavailable (a failed `pandoc --version`) before drafting content?
2. [one-offer] Did the run make exactly one install offer, naming a platform command (`apt install pandoc` or equivalent), and not retry after "no"?
3. [fallback-offered] After the install was declined, did the run offer HTML + PDF as a fallback rather than assume it?
4. [honest-report] Did the final report state that the Word target was not produced and why, without claiming any `.docx` exists?
5. [board] Was AR-1 left out of In Review (nothing was delivered)?
```

- [ ] **Step 6: Checks** (all three files NOT executable — create with `cat >` and never `chmod +x`).

`checks/word-default.sh`:

```bash
# Checks — word-default. Mechanical facts: fixture intact before; docx from
# markdown, board moved, no HTML after. Gate conduct is the rubric's.

pre() {
  file-exists brief.md
  file-exists diagram.png
  file-exists context/tooling/board.md
  file-contains context/tooling/design-system.md "mode: absent"
  file-absent out/brief.docx
}

post() {
  file-exists out/brief.docx
  zip-member-contains out/brief.docx word/document.xml "Q3 stakeholder one-pager"
  zip-member-contains out/brief.docx word/document.xml "Acceptance criteria"
  file-absent out/brief.html
  file-contains context/tooling/board.md "AR-1 .* In Review"
}
```

`checks/word-reference.sh`:

```bash
# Checks — word-reference. The sentinel colour proves the reference doc was applied.

pre() {
  file-exists brief.md
  file-exists context/design-system/templates/word/reference.docx
  file-contains context/tooling/design-system.md "mode: in-repo"
  file-contains context/tooling/design-system.md "word_reference: \"context/design-system/templates/word/reference.docx\""
  zip-member-contains context/design-system/templates/word/reference.docx word/styles.xml FF00AA
  file-absent out/brief.docx
}

post() {
  file-exists out/brief.docx
  zip-member-contains out/brief.docx word/styles.xml FF00AA
  zip-member-contains out/brief.docx word/document.xml "Acceptance criteria"
  file-absent out/brief.html
}
```

`checks/pandoc-absent.sh`:

```bash
# Checks — pandoc-absent. Nothing was delivered, so nothing may claim it was.

pre() {
  file-exists brief.md
  file-contains context/tooling/design-system.md "mode: absent"
  file-absent out/brief.docx
}

post() {
  file-absent out/brief.docx
  file-not-contains context/tooling/board.md "AR-1 .* In Review"
  file-not-contains context/tooling/board.md "AR-1 .* Done"
}
```

- [ ] **Step 7: Setup hooks** — three identical executable files `setup/<scenario>.sh` (copy of the process-transcript hook):

```bash
#!/usr/bin/env bash
# Board writes in this suite edit the fixture board file; a real repo boundary
# keeps the resolution walk honest.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
```

`chmod +x tests/artifact/setup/*.sh`.

- [ ] **Step 8: Env container** `tests/artifact/env/pandoc-absent/Dockerfile`:

```dockerfile
# pandoc-absent: a Linux machine without pandoc on PATH. The RUN guard fails
# the build if the base image ever starts shipping pandoc, so the scenario
# can't silently rot into testing nothing.
FROM debian:bookworm-slim
RUN if command -v pandoc >/dev/null 2>&1; then echo "base image ships pandoc — pick a slimmer base" >&2; exit 1; fi
```

- [ ] **Step 9: Suite README** `tests/artifact/README.md` — mirror `tests/process-transcript/README.md`'s sections (Principle, Scenarios table, Invariants graded, Layout, Fixture conventions, Adding a scenario). Scenarios table rows: `word-default` — "target not asked; HTML generated then converted; stock-styles fact missing from the report"; `word-reference` — "reference doc ignored"; `pandoc-absent` — "silent drop of the Word target; repeated install nagging; a docx claimed that does not exist". Invariants: target-first, word-constraints, content-gate, from-markdown, outline, style-report, reference-applied, tool-absent, one-offer, fallback-offered, honest-report, board. State that fixtures are built by `fixtures/make-fixtures.sh` (needs pandoc) and that `pandoc-absent` needs docker (composes `indeterminate (stage: env)` otherwise).

- [ ] **Step 10: Static gate.** `python tools/validate-evals.py` → exit 0. Common failures: a checks file accidentally executable (`chmod -x`), a script without a rubric, a fixture swallowed by `.gitignore`.
- [ ] **Step 11: Run the suite.** `/test-awow artifact` (interactive, needs the plugin payload from this branch: `python tools/gather.py && claude --plugin-dir dist`). Expected: `word-default` PASS, `word-reference` PASS, `pandoc-absent` PASS (or `INDETERMINATE(env)` without docker). Fix prompt text, not checks, when a rubric question fails for a real reason; fix the check when the two witnesses disagree and the check is wrong. Paste the `OVERALL:` line into the board item as a comment.
- [ ] **Step 12: Commit.**

```bash
git add tests/artifact
git commit -m "CAU-1525: tests/artifact eval suite — word-default, word-reference, pandoc-absent" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
```

---

### Task 9: Bookkeeping and PR

**Files:**
- Modify: `proposals/design-system-capability.md` (Status line), `proposals/README.md` (two rows), `proposals/word-export-design.md` (Status line)

- [ ] **Step 1: Status lines.** In `design-system-capability.md` append to the Status line: ` §3.7 render skill landed as `artifact-render` via [word-export-design.md](word-export-design.md).` In `proposals/README.md` change the `word-export-design` row's status to `**Landed** (PR #<n>, <date>)` once the PR number exists, and the `design-system-capability` row's outcome to mention the render skill. In `word-export-design.md` set Status to `Implemented <date>; board item CAU-1525; PR #<n>.`
- [ ] **Step 2: Full local gate** — the CI list, in order: `python tools/gather.py --check`, `python tools/lint-paths.py`, `python3 tests/context-writes/test_context_writes.py`, `python3 tests/command-frontmatter/test_frontmatter.py`, `python3 tests/gather-tokens/test_tokens.py`, `python3 tests/payload-classification/test_classification.py`, `python3 tests/payload-manifests/test_manifest_integrity.py`, `python3 tests/payload-tools/test_tool_references.py`, `python3 tests/payload-manifests/test_build_stamp.py`, `python3 tests/payload-commands/test_command_surface.py`, `python3 tests/artifact-render/test_docx_outline.py`, `python tools/validate-evals.py`. All exit 0.
- [ ] **Step 3: Commit, push, open the PR.**

```bash
git add proposals
git commit -m "CAU-1525: mark word-export landed; design-system-capability §3.7 resolved" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -m "Claude-Session: https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej"
git push -u origin arie/cau-1525-add-a-word-export-target-to-artifact
gh pr create --title "CAU-1525: /artifact emits Word via pandoc; render mechanics move into artifact-render" --body-file <(printf '%s\n' "Spec: proposals/word-export-design.md — plan: proposals/plans/2026-09-04-word-export.md." "" "- /artifact asks for the target, holds Word content to its constraints, delegates rendering." "- /design-system registers the team's Word template as word_reference." "- artifact-render skill: HTML/PDF/Word recipes + stdlib docx_outline.py." "- tests/artifact suite (3 scenarios) + zip-member-contains verb + CI unit test." "" "🤖 Generated with [Claude Code](https://claude.com/claude-code)" "" "https://claude.ai/code/session_01KVcWcfTJADvj7555SXdNej")
```

- [ ] **Step 4: Board.** Move CAU-1525 to In Review with the PR link and the `OVERALL:` line from Task 8.

---

## Amendments at implementation (2026-09-04)

Recorded by the build; the steps above are the plan as written, the branch is the record of what actually happened.

- **Task 1 Step 1** hardcoded the main checkout's prelude path; probe against the worktree under test.
- **Task 2:** a third fixture `titled.docx` (`--metadata title="Probe brief"`) and one assertion pin the Title-as-level-0 rule; `docx_outline.py` also catches `OSError` and `ET.ParseError`. Step 4's "every line FAIL" is overstated: the three error-path assertions pass vacuously when the script is missing; the suite still fails overall.
- **Task 5** also updates `design-system.md` §3.3's quote of the AGENTS.md heading; **Task 7** also updates `guides/guide-design-system-and-artifacts.md`'s quote, and produces no `dist/` change.
- **Task 6** additionally generalises `/artifact`'s H1, intro, `when-to-use`, Phase 2 heading, the "until locked" line and two boundaries, and places the Target block at the top of Phase 2 (not before the gate paragraph).
- **Task 8:** `make-fixtures.sh` also writes a minimal `style-guide.html` for `word-reference`; scripts pre-empt the design-system offer and pin the basename; rubric outline questions are graded from the report, not from tool output; `pandoc-absent` `post()` asserts only `file-absent out/brief.docx` and the board row; the suite README's "Fixture conventions" and "Adding a scenario" sections follow `tests/daily-digest` and `tests/setup-awow` (process-transcript has none). The skill sentence from spec §10.2 and its `dist/` rebuild landed in Task 8's commit.
- **All gates:** run as `python3`; `python` is not on PATH here. Docker daemon was unreachable; the env image is unbuilt.
