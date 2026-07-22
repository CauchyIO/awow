---
name: artifact
description: "Use when the user asks for a deck, slides, a blog post, one-pager, or report as HTML or PDF — any styled document that should follow the team's house style instead of hand-written CSS."
---

# /artifact — generate a styled HTML artifact from the design system

You produce an HTML artifact — presentation, blog post, one-pager, report — that **adopts the team's design system**. Content is drafted in markdown and agreed first; HTML is generated from a template, never hand-styled.

You run this often. It is lighter than `/design-system` (which you run once to build the system), but it still gates on content before generating, because regenerating HTML from changed markdown is cheap and rewriting hand-tuned HTML is not.

---

## Phase 0 — Resolve the design system

Read `{HUB}/context/tooling/design-system.md`, falling back to `${CLAUDE_PLUGIN_ROOT}/context/tooling/design-system.md` (a vendored copy wins over the shipped one).

- **`mode: absent`** — no design system. Offer to run `/design-system` first. If the user declines, proceed with plain, accessible defaults and say so — do not invent a house style and do not pretend one exists.
- **`mode: in-repo` / `external`** — read the source file at `path:` now (filesystem, not MCP, when `access: local-path`). Read the matching `templates_dir` template for the artifact type. Re-read the source even if the pointer has a token cache — the cache can drift.

Read `{HUB}/context/team/style/*.md` for the writing voice.

---

## Phase 1 — Board-first

Per the repo's "Before starting a new initiative" rule: find or create the tracking item, set it in progress. If the user named an item, skip the lookup and comment as you go.

---

## Phase 2 — Content in markdown (gate before HTML)

Draft the artifact's content as markdown — `slides.md` for a deck, `<artifact>.md` otherwise — under the working directory the user confirms. Iterate structure and tone with the user. Keep it light on text, heavy on intended visuals; note where diagrams go.

**Gate:** present the markdown outline and ask *"content agreed — generate the HTML?"* Do not generate HTML until the content is locked. Spin large sub-asks (a research appendix, an assessment tool) into their own side-doc and, if they warrant it, their own board item — do not cram them into this artifact.

---

## Phase 3 — Generate HTML from the template

Generate the artifact HTML from the template, **preserving its `<style>` block, nav JS, and print CSS verbatim**. Map content to the template's component/slide types (cover / content / accent / emphasis, per the `TEMPLATE.md` catalog).

- Prefer **HTML/CSS diagrams** over raw inline SVG or Mermaid.
- Drive any repeating layout from a **data object**, not hand-placed elements.
- Keep the logo and accent rules exactly as the design system specifies (accent reserved, wordmark caps, fill-by-context).

A background agent may do the bulk HTML generation, but it must preserve the template's style block — review its output, do not trust it blind.

---

## Phase 4 — Verify and export

1. Open the artifact in a browser (`open`).
2. **Verify layout with Playwright** — inspect computed layout and overflow, do not just eyeball it.
3. Export PDF via **Chrome headless print-to-PDF** (modern CSS — grid, clamp, viewport units — survives; WeasyPrint does not handle flex/grid). Use the template's print CSS (e.g. one slide per 1280×720 page for decks).
4. Fix overflow by tightening padding / splitting dense slides / reducing font, then regenerate. This loop is expected; do not ship a deck with clipped slides.

---

## Phase 5 — Land and update the board

Commit and push the markdown source, the HTML, and the PDF. Update the board item (in review, reviewer, link to the markdown source on the remote). Drafts land under the confirmed working directory; do not write outside it without confirming.

---

## Behavioral boundaries

- **Content before HTML, always.** Never hand-author styled HTML when a template exists. Agree the markdown, then generate.
- **The design system is not optional when present.** If the pointer is not `absent`, the artifact adopts it. Do not override the house style because a different look "would pop" — raise it with the user instead.
- **Re-read the source each run.** The pointer's token cache is a convenience, not the source of truth.
- **Render before you claim done.** An artifact you have not opened and exported is not finished. Verify layout with Playwright and check the PDF for overflow.
- **No false confidence on identifiers.** Any board ID, file path, or template name in your output must have been read this session.
