# Guide template contract

How every `guide-*.html` in this folder is built. The goal is one recognisable shape across the
gallery: a reader who has seen one guide knows where to look in the next. Guides are **self-contained
single HTML files** — no external fonts, stylesheets, scripts, or links by design (see the footer rule
below). That means the CSS is duplicated into each file on purpose; this document is the single written
source those copies come from.

`guide-board-and-mcp.html` is the **reference implementation** — when in doubt, match it.

---

## 1. The fixed skeleton

Every guide is, top to bottom:

```
<!DOCTYPE html><html lang="en">
<head>
  <meta charset> <meta viewport>
  <title>{Title} &mdash; {one-line what-it-is}</title>
  <!-- AWOW GUIDE — {slug}
       2–4 lines: what this guide covers and its place in the set.
       End with: Self-contained: no external fonts/links by design. -->
  <style> … the base block (§2) + any optional components (§3) … </style>
</head>
<body>
  <nav class="guide-toc" …>            ← left index, brand links to index.html (§4)
  <div class="wrap">
    <div class="pad" HEADER>           ← kicker, h1, subtitle, optional sub-note, badges (§5)
    <div class="pad-tight" TL;DR>      ← always present, directly under the header (§5)
    … content sections in .pad / .part-header …
    <div class="pad" FOOTER>           ← "Sources of truth: …" (§6)
  </div>
  <script> … the auto-TOC builder (§4) …
</body></html>
```

The `<head>` style block, the `nav.guide-toc`, the header/TL;DR/footer pattern, and the `<script>`
are **invariant** — copy them verbatim from the reference implementation. Only the content sections
differ between guides.

---

## 2. The base CSS block (copy verbatim)

Every guide includes exactly this `:root` and base component set. Do not change values; drift here is
what made the older guides feel "off". Notably: `--wrap` max-width is **1040px**, the mobile breakpoint
is **760px**, and the font stacks keep their full fallback chains.

```css
:root {
  --bg:#f6f5f3; --surface:#ffffff; --surface-alt:#f0efed;
  --text-1:#1a1a1a; --text-2:#6b6b6b; --text-3:#9a9a9a;
  --border:#e0dfdd; --border-subtle:#ebeae8;
  --accent:#f24b37; --link:#337FF9; --ok:#2e7d4f; --warn:#c97a1b; --risk:#b53a2a;
}
body { margin:0; padding:0; width:100%; font-family:'Nunito',system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text-1); line-height:1.6; }
.wrap { max-width:1040px; margin:0 auto; background:var(--surface); border:1px solid var(--border); border-radius:12px; overflow:hidden; }
.pad { padding:28px 40px; border-bottom:1px solid var(--border-subtle); }
.pad-tight { padding:20px 40px; border-bottom:1px solid var(--border-subtle); }
h1 { font-size:1.9rem; font-weight:700; margin:0; letter-spacing:-0.02em; }
h2 { font-size:1.35rem; font-weight:600; margin:0 0 16px; letter-spacing:-0.01em; }
h3 { font-size:1.05rem; font-weight:600; margin:24px 0 10px; letter-spacing:-0.01em; }
p  { font-size:0.92rem; color:var(--text-2); margin:0 0 12px; line-height:1.7; }
ul, ol { font-size:0.92rem; color:var(--text-2); line-height:1.7; padding-left:22px; margin:0 0 14px; }
li { margin:4px 0; }
strong { color:var(--text-1); font-weight:600; }
em { color:var(--text-1); font-style:italic; }
code { font-family:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,monospace; font-size:0.85em; background:var(--surface-alt); padding:1px 6px; border-radius:3px; border:1px solid var(--border-subtle); }
pre { font-family:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,monospace; font-size:0.82rem; background:var(--surface-alt); padding:14px 18px; border-radius:8px; border:1px solid var(--border-subtle); overflow-x:auto; line-height:1.55; color:var(--text-1); }
pre .c { color:var(--text-3); }
table.data { border-collapse:collapse; width:100%; font-size:0.85rem; margin:0 0 16px; }
table.data th { text-align:left; font-weight:600; padding:8px 10px; border-bottom:2px solid var(--border); background:var(--surface-alt); font-size:0.78rem; text-transform:uppercase; letter-spacing:0.04em; }
table.data td { padding:9px 10px; border-bottom:1px solid var(--border-subtle); color:var(--text-2); vertical-align:top; line-height:1.5; }
table.data tr:last-child td { border-bottom:none; }
table.data td strong { color:var(--text-1); }
.kicker { font-size:0.72rem; font-weight:600; color:var(--text-3); text-transform:uppercase; letter-spacing:0.08em; margin:0 0 8px; }
.badge { display:inline-block; font-size:0.7rem; font-weight:600; padding:3px 10px; border-radius:4px; border:1px solid var(--border); color:var(--text-1); background:var(--surface); }
.badge-accent { background:var(--accent); color:#fff; border-color:var(--accent); }
.badge-ok { background:rgba(46,125,79,0.08); color:var(--ok); border-color:rgba(46,125,79,0.25); }
.badge-warn { background:rgba(201,122,27,0.08); color:var(--warn); border-color:rgba(201,122,27,0.25); }
.badge-muted { background:var(--surface-alt); color:var(--text-3); border-color:var(--border-subtle); border-style:dashed; }
.badges { display:flex; gap:6px; flex-wrap:wrap; }
.callout { background:var(--surface-alt); border-left:3px solid var(--accent); border-radius:0 8px 8px 0; padding:14px 18px; margin:0 0 16px; font-size:0.88rem; color:var(--text-2); line-height:1.65; }
.callout strong { color:var(--text-1); }
.callout-warn { border-left-color:var(--warn); }
.callout-ok { border-left-color:var(--ok); }
.diagram { background:var(--surface-alt); border:1px solid var(--border-subtle); border-radius:10px; padding:18px 16px 12px; margin:0 0 18px; }
.diagram svg { display:block; max-width:100%; height:auto; margin:0 auto; }
.legend { display:flex; gap:16px; flex-wrap:wrap; font-size:0.78rem; color:var(--text-2); padding:8px 8px 0; }
.legend span { display:inline-flex; align-items:center; gap:6px; }
.legend i { display:inline-block; width:12px; height:12px; border-radius:2px; border:1px solid var(--border); }
.grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px; }
.grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px 18px; }
.card .card-label { font-size:0.7rem; font-weight:600; color:var(--text-3); text-transform:uppercase; letter-spacing:0.06em; margin:0 0 6px; }
.card h3 { margin-top:0; }
@media (max-width: 760px) {
  .pad, .pad-tight { padding-left:22px; padding-right:22px; }
  .grid-3 { grid-template-columns:1fr; }
  .grid-2 { grid-template-columns:1fr; }
}
@media print {
  body { background:#fff; }
  .wrap { border:none; border-radius:0; max-width:100%; }
}
/* ===== LEFT INDEX (auto-built from section headings) ===== */
.guide-toc { position:fixed; top:0; left:0; width:232px; height:100vh; background:var(--surface); border-right:1px solid var(--border); z-index:60; display:flex; flex-direction:column; overflow-y:auto; padding:20px 0; }
.guide-toc .toc-brand { display:flex; align-items:center; gap:8px; padding:0 20px 18px; border-bottom:1px solid var(--border-subtle); margin-bottom:10px; flex-shrink:0; }
.guide-toc .toc-brand svg { width:18px; height:18px; flex:none; }
.guide-toc .toc-brand span { font-size:12px; font-weight:700; letter-spacing:0.06em; color:var(--text-2); text-transform:uppercase; }
.guide-toc a.toc-item { display:flex; align-items:flex-start; gap:10px; padding:8px 20px; text-decoration:none; color:var(--text-2); font-size:12px; font-weight:500; line-height:1.45; border-left:3px solid transparent; transition:background 0.12s, color 0.12s; }
.guide-toc a.toc-item:hover { background:var(--surface-alt); color:var(--text-1); }
.guide-toc a.toc-item.active { background:var(--surface-alt); color:var(--text-1); font-weight:700; border-left-color:var(--accent); }
.guide-toc .toc-num { font-size:10px; font-weight:700; color:var(--accent); min-width:16px; opacity:0.5; padding-top:1px; flex:none; }
.guide-toc a.toc-item.active .toc-num { opacity:1; }
@media (min-width:1024px) { body { padding-left:232px; } }
@media (max-width:1023px) { .guide-toc { display:none; } }
@media print { .guide-toc { display:none !important; } body { padding-left:0 !important; } }
```

When the mobile breakpoint also needs to collapse an optional grid (`.scope-bar`, etc.), extend the
existing `@media (max-width: 760px)` rule — do **not** introduce a second breakpoint at 720px.

---

## 3. Optional component catalogue

Add a component's CSS **only if the guide uses it**, and when you do, copy it verbatim from here so it
is identical everywhere it appears. Reach for these before inventing a new one; if a guide genuinely
needs something new, add it to this catalogue in the same change.

```css
/* h4 — sub-subsection heading */
h4 { font-size:0.92rem; font-weight:600; margin:18px 0 8px; }

/* in-body links (most guides have none; add only if you link within the page) */
a { color:var(--link); text-decoration:none; }
a:hover { text-decoration:underline; }

/* meta-row — Stage / Commands / Audience strip under the header subtitle */
.meta-row { display:flex; flex-wrap:wrap; gap:14px 24px; margin:4px 0 0; font-size:0.78rem; color:var(--text-3); }
.meta-row span strong { color:var(--text-2); font-weight:600; }

/* risk variants of badge + callout */
.badge-risk { background:rgba(181,58,42,0.08); color:var(--risk); border-color:rgba(181,58,42,0.25); }
.callout-risk { border-left-color:var(--risk); }

/* part-header — dark full-width divider between major phases of a long guide */
.part-header { background:var(--text-1); color:#fff; padding:28px 40px; }
.part-header .part-num { font-size:0.72rem; font-weight:600; color:var(--accent); text-transform:uppercase; letter-spacing:0.16em; margin:0 0 8px; }
.part-header h2 { color:#fff; margin:0; font-size:1.45rem; font-weight:700; letter-spacing:-0.01em; }
.part-header p  { color:rgba(255,255,255,0.7); margin:6px 0 0; font-size:0.92rem; }

/* diagram-title — caption row above an SVG, optional C4-level marker on the right */
.diagram-title { font-size:0.72rem; font-weight:600; color:var(--text-3); text-transform:uppercase; letter-spacing:0.08em; margin:0 0 12px; padding:0 8px; display:flex; justify-content:space-between; }
.diagram-title .c4 { color:var(--accent); }

/* toc box — in-body 2-column contents list (for long guides with numbered sections) */
.toc { background:var(--surface-alt); border-radius:8px; padding:18px 22px; margin:0; }
.toc ol { padding-left:22px; margin:0; columns:2; column-gap:28px; }
.toc li { margin:5px 0; font-size:0.85rem; color:var(--text-2); }
.toc a { color:var(--text-1); font-weight:500; }

/* open-q — "open question a team must answer" highlight */
.open-q { background:rgba(242,75,55,0.06); border:1px solid rgba(242,75,55,0.25); border-radius:8px; padding:12px 16px; margin:0 0 12px; }
.open-q strong { color:var(--accent); }

/* pill — small inline token chip */
.pill { display:inline-block; font-family:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,monospace; font-size:0.72rem; padding:2px 8px; background:#fff; color:var(--text-1); border:1px solid var(--border); border-radius:10px; }

/* scope-bar — in/out-of-scope grid (4 cells) */
.scope-bar { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:14px 0 18px; }
.scope-cell { background:var(--surface-alt); border:1px solid var(--border-subtle); border-radius:8px; padding:10px 12px; font-size:0.78rem; }
.scope-cell.in { background:rgba(46,125,79,0.08); border-color:rgba(46,125,79,0.35); }
.scope-cell.out { background:#fff; border-style:dashed; color:var(--text-3); }
.scope-cell .lbl { font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-3); }
.scope-cell.in .lbl { color:var(--ok); }
.scope-cell .name { font-size:0.92rem; font-weight:600; color:var(--text-1); margin:2px 0 0; }
.scope-cell.out .name { color:var(--text-3); text-decoration:line-through; }

/* step — numbered "the flow in words" list with circled numbers */
.step { display:flex; gap:14px; margin:0 0 14px; align-items:flex-start; }
.step .n { flex:0 0 28px; width:28px; height:28px; border-radius:50%; background:var(--text-1); color:#fff; font-size:0.8rem; font-weight:700; display:flex; align-items:center; justify-content:center; }
.step .b { font-size:0.9rem; color:var(--text-2); line-height:1.6; }
.step .b strong { color:var(--text-1); }
```

If a guide uses `part-header`, `toc`, or `scope-bar`, add them to the mobile collapse rule:
`@media (max-width: 760px) { .pad, .pad-tight, .part-header { … } .toc ol { columns:1; } .grid-2, .grid-3, .scope-bar { grid-template-columns:1fr; } }`
and to print: `@media print { .part-header { page-break-before:always; } a { color:var(--text-1); } }`.

---

## 4. Navigation (invariant)

- The `nav.guide-toc` markup and the `<script>` at the end of `<body>` are copied verbatim from the
  reference implementation. The script auto-builds the left index from every `.wrap h2` (including the
  `h2` inside a `.part-header`), strips a leading `1. ` / `2) ` number from the label, and scroll-spies.
- The brand link in the nav always points to `index.html`.
- Because the TOC is generated from `h2`s, **every section that should appear in the index must be an
  `h2`** inside a `.pad`, `.pad-tight`, or `.part-header`. Use `h3`/`h4` for anything that should *not*
  get its own index entry.

---

## 5. Header & TL;DR conventions

Header block (`.pad`, `padding-top:36px;padding-bottom:24px;`):
1. **Kicker** — `Way of Working &middot; Guide` (the accent, letter-spaced micro-label). Always this text.
2. **`h1`** — the guide title, plain.
3. **Subtitle** — one sentence, `font-size:1rem; color:var(--text-2)`.
4. **Sub-note** *(optional)* — a smaller `text-3` line for a key clarification or companion-guide pointer.
5. **`meta-row`** *(optional)* — Stage / Commands / Audience, when those orient the reader.
6. **`.badges`** — 2–4 short badges; the last is usually `badge-accent` naming the load-bearing artefact.

**TL;DR** is mandatory and comes immediately after the header in a `.pad-tight` with a `kicker` reading
`TL;DR`, then one dense paragraph that lets a reader skip the rest and still be correct.

A guide may follow the TL;DR with one more `.pad-tight` callout for a single critical prerequisite or
shared dependency — keep it to one.

---

## 6. Section & content conventions

- **Numbering**: a guide either numbers all its `h2`s (`1.`, `2.`, …) or none of them — never mix.
  Number when the guide is a sequence to follow (a pipeline, a setup walk); leave unnumbered when the
  sections are a reference grouping.
- **`part-header`** divides a long guide into named phases ("Before you run it" / "The run" / "After").
  Use it only when there are clear phases; short guides skip it.
- **Diagrams**: an SVG lives in a `.diagram` with a `.legend` above it (colour swatch + label per node
  class). Keep node fills keyed to the tokens (`#1a1a1a` for inputs/actors, `rgba(--accent…)`,
  `rgba(--link…)`, etc.) and label the artefact the page is really about in the accent colour.
- **Footer** is the last `.pad` (`border-bottom:none`), a single `text-3` line beginning
  **`Sources of truth:`** that names the authoritative files/commands, then ends with
  *"This guide is self-contained — no external resources."*
- **No external resources, ever**: no web fonts, CDN links, external stylesheets/scripts, or outbound
  hyperlinks. Cross-reference other guides by filename and board vendors by name only. This is a
  security and portability rule, not a style preference.

---

## 7. Adding or refreshing a guide — checklist

1. Copy `guide-board-and-mcp.html` as the starting point; replace `<title>`, the head comment, the
   header, and the sections.
2. Keep the base CSS block (§2) byte-identical. Add optional components (§3) only as used.
3. First content block after the header is the TL;DR.
4. Every index-worthy section is an `h2`; numbering is all-or-nothing.
5. Footer names the real sources of truth and the self-contained disclaimer.
6. Add the guide to `index.html` under the correct flow grouping, with a card whose copy does not merely
   restate the phase-frame above it (see the index's own grouping comments).
7. New shared component? Add its canonical CSS to §3 in the same change.

---

## 8. Source of truth & knowledge extractability

The HTML file **is** the canonical source of a guide — there is no markdown twin to keep in sync.
Downstream consumers (the docs site and the knowledge-base agent) work from generated projections:
a deterministic strip step extracts headings, prose, list/table text, `figcaption`/`.legend` text,
and code blocks at publish time (see `linear/context/knowledge-base/patterns/guide-source-of-truth.md`).

That places one hard rule on authoring: **all knowledge in a guide must be extractable text in the
DOM.** Prose, tables, and code carry themselves. A diagram's *meaning* must live in its `.legend`
and caption text (§6 already requires these) — never only in SVG geometry, colour, or placement.
If removing every visual would lose a fact, that fact is missing from the text; add it.
