---
name: artifact
description: "Use when the user asks for a deck, slides, a blog post, one-pager, or report as HTML, PDF or Word — any styled document that should follow the team's house style instead of hand-written CSS."
---

# /artifact — generate a styled artifact from the design system

You produce a styled artifact — presentation, blog post, one-pager, report — that **adopts the team's design system**. Content is drafted in markdown and agreed first; every target is generated from it, never hand-styled.

You run this often. It is lighter than `/design-system` (which you run once to build the system), but it still gates on content before generating, because regenerating a target from changed markdown is cheap and rewriting a hand-tuned one is not.

---

## Phase 0 — Resolve the design system

Read `{ANCHOR}/context/tooling/design-system.md`, falling back to `../../context/tooling/design-system.md` (a vendored copy wins over the shipped one).

- **`mode: absent`** — no design system. Offer to run `/design-system` first. If the user declines, proceed with plain, accessible defaults and say so — do not invent a house style and do not pretend one exists.
- **`mode: in-repo` / `external`** — read the source file at `path:` now (filesystem, not MCP, when `access: local-path`). Read the matching `templates_dir` template for the artifact type. Re-read the source even if the pointer has a token cache — the cache can drift.

Read `word_reference` as well. Empty or `mode: absent` means Word output uses pandoc's stock styles, and you say so in the run's final report.

Read `{ANCHOR}/context/team/style/*.md` for the writing voice.

---

## Phase 1 — Board-first

Per the repo's "Before starting a new initiative" rule: find or create the tracking item, set it in progress. If the user named an item, skip the lookup and comment as you go.

---

## Phase 2 — Content in markdown (gate before generating)

**Target.** Before you draft, ask which outputs the user wants: HTML + PDF (the default), Word (`.docx`), or both. Record the answer; it shapes the content.

When Word is among the targets, state these constraints before drafting and hold the content to them:

- Every diagram is a PNG or a table. HTML/CSS diagrams do not survive into Word; render them to PNG per the `artifact-render` skill or replace them with a table.
- One H1 or a `title:` metadata line, never both — pandoc emits a Title *and* a Heading 1 otherwise.
- Images are referenced by a path relative to the markdown file's directory.
- No slide-style layouts, columns, or positioned elements. Headings, paragraphs, lists, tables, images, code.

Run `pandoc --version` the moment Word is chosen. Anything but exit 0 — absent or broken — means you follow the `artifact-render` skill's tool-absent rule now, before content work, so the user can decide the target with the fact in hand.

Draft the artifact's content as markdown — `slides.md` for a deck, `<artifact>.md` otherwise — under the working directory the user confirms. Iterate structure and tone with the user. Keep it light on text, heavy on intended visuals; note where diagrams go.

**Gate:** present the markdown outline and ask *"content agreed — generate the <targets>?"* Do not generate any target until the content is locked. Spin large sub-asks (a research appendix, an assessment tool) into their own side-doc and, if they warrant it, their own board item — do not cram them into this artifact.

---

## Phase 3 — Generate the targets

**HTML.** Generate the artifact HTML from the template, **preserving its `<style>` block, nav JS, and print CSS verbatim**. Map content to the template's component/slide types (cover / content / accent / emphasis, per the `TEMPLATE.md` catalog).

- Prefer **HTML/CSS diagrams** over raw inline SVG or Mermaid.
- Drive any repeating layout from a **data object**, not hand-placed elements.
- Keep the logo and accent rules exactly as the design system specifies (accent reserved, wordmark caps, fill-by-context).

A background agent may do the bulk HTML generation, but it must preserve the template's style block — review its output, do not trust it blind.

**Word.** Generate the Word document from the agreed markdown per the `artifact-render` skill §Word. Do not generate HTML first and convert it; the markdown is the source.

---

## Phase 4 — Verify and export

Verify and export every target per the `artifact-render` skill: HTML gets the Playwright layout check and the Chrome headless PDF; Word gets the outline check, the round trip, and the visual check when LibreOffice is present. Fix overflow or outline mismatches at the source (markdown or template), regenerate, re-verify. This loop is expected; do not ship a clipped slide or a document whose outline does not match its source.

---

## Phase 5 — Land and update the board

Commit and push the markdown source and every emitted target file (HTML, PDF, `.docx`). Update the board item (in review, reviewer, link to the markdown source on the remote). Drafts land under the confirmed working directory; do not write outside it without confirming.

---

## Behavioral boundaries

- **Content before generation, always.** Never hand-author a styled target when a template exists. Agree the markdown, then generate every target from it.
- **The design system is not optional when present.** If the pointer is not `absent`, the artifact adopts it. Do not override the house style because a different look "would pop" — raise it with the user instead.
- **Re-read the source each run.** The pointer's token cache is a convenience, not the source of truth.
- **Render before you claim done.** A target you have not opened, measured, or outlined is not finished. Verify each one per the `artifact-render` skill.
- **No false confidence on identifiers.** Any board ID, file path, or template name in your output must have been read this session.
- **Word comes from the markdown, never from the HTML.** If the HTML and the Word document disagree, the markdown was edited after one of them was generated — regenerate both.
- **A missing render tool is a stated fallback, never a silent one.** When pandoc is absent, the final report names the target that was not produced and why.
