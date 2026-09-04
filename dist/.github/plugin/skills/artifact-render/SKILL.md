---
name: artifact-render
description: "Use when an /artifact run reaches rendering or verification — check HTML layout with Playwright, export PDF via Chrome headless, emit Word via pandoc with the team's reference doc — or when one of those tools is missing."
---

# artifact-render — render and verify every `/artifact` target

You own the mechanics only. `/artifact` decides content, reads the design system and works the board; you turn the agreed markdown into each target and prove it before anyone calls it done. Read `{ANCHOR}/context/tooling/design-system.md` (falling back to `${CLAUDE_PLUGIN_ROOT}/context/tooling/design-system.md`) for `templates_dir` and `word_reference`; never invent styling.

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

Run it only on an explicit yes. On no, or on a failed install, produce the other targets and state in the final report that the Word target was not produced and why. Never drop the target silently. When Word was the only target chosen, offer HTML + PDF instead and wait for the answer; do not substitute a target the user did not ask for. Minimum version: pandoc 2.6 (task lists in `gfm`); verified on 3.8.2.

## Boundaries

- Word comes from the markdown, never from the HTML.
- Nothing is done until it has been opened, measured, or outlined. A target you have not verified is not finished.
- A missing tool is a stated fallback in the final report, never a silent omission.
