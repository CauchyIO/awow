---
description: "stand up or adopt a design system"
phase: spread
prerequisites:
  - "Step 1 of /setup-awow complete (the agent can read and write the board)"
  - "Team produces styled HTML artifacts (decks, blogs, solution designs)"
removes_pain: "the every-artifact-reinvents-its-own-styling problem"
consumes: "a reference site, brand, or existing style guide"
when-to-use: "The team produces styled HTML artifacts and has no design system yet, or has one in another repo that awow doesn't know about. First time standing up a house style, or pointing awow at an existing one."
when-not-to-use: "A design system is already configured ({HUB}/context/tooling/design-system.md, else ${CLAUDE_PLUGIN_ROOT}/context/tooling/design-system.md, mode is not absent) and you only want to produce an artifact — use /artifact. The team ships only board items and no styled HTML."
---

# /design-system — stand up or adopt a design system

You turn a reference, a brand, or an existing style guide into a **durable, reusable design system** awow can drive every HTML artifact from: a self-contained style-guide page, per-artifact-type templates, and a pointer (`{HUB}/context/tooling/design-system.md`) that every artifact-producing command reads.

You establish the system **once**; the team produces artifacts from it many times via `/artifact`. Do not generate decks or blogs here — that is `/artifact`'s job. Here you build the thing they are generated from.

This is rare, high-leverage work. Run it as a pipeline with **three gates**. Stop at each gate, present your work, and wait for explicit confirmation. Never skip a gate.

---

## Mode detection

Read `{HUB}/context/tooling/design-system.md` first, falling back to `${CLAUDE_PLUGIN_ROOT}/context/tooling/design-system.md` (a vendored copy wins over the shipped one).

- If `mode:` is not `absent`, a system is already configured. Name its `path:` and ask whether the user wants to **revise** it (proceed) or **point at a different one** (start over). Do not silently overwrite.
- If `mode: absent`, this is a fresh establish. Read `$ARGUMENTS` — a reference URL, a path to an existing style guide, or empty (ask for the source at Gate 1).

---

## Pipeline overview

```
Phase 0 ─ Load team context
Phase 1 ─ Source & method teardown        ──→ GATE 1 (confirm source + extracted method)
Phase 2 ─ Token set & principles          ──→ GATE 2 (approve tokens, fonts, rules)
Phase 3 ─ Write system + templates + wire ──→ GATE 3 (approve writes)
```

---

## Phase 0 — Load team context

Read `{HUB}/context/team/mission.md`, `{HUB}/context/team/members.md`, and `{HUB}/context/team/style/*.md` (the team's writing voice is part of the design system). Read `{HUB}/context/tooling/design-system.md`, falling back to `${CLAUDE_PLUGIN_ROOT}/context/tooling/design-system.md`, for current state.

Decide **in-repo vs external** with the user:

- **in-repo** — the system lives under `{HUB}/context/design-system/` in this repo. Default for teams without a separate design repo. Self-contained, no cross-repo fragility.
- **external** — the system lives in another repo (e.g. a dedicated `design` repo), referenced by absolute path. Choose this when the team already maintains design assets elsewhere. Note whether that repo is private — if so, the agent reads it by filesystem path, not MCP (`access: local-path`).

---

## Phase 1 — Source & method teardown

### 1.1 Identify the source

One of:

- **A reference site you admire** — tear it down empirically. Use Playwright/Chrome headless to capture screenshots *and computed styles* (colors as RGB, font families, sizes, line-heights, letter-spacing) into a results file under `/tmp/`. WebFetch is not enough for client-rendered sites; render the page.
- **An existing brand** (logo, colors, fonts the team already uses) — gather the assets and read them.
- **An existing style guide** in another repo — read it directly; you are adopting, not deriving.

### 1.2 Extract the method, not the pixels

From the teardown, name the *method* the reference uses — restraint, semantic color, type pairing, per-page or per-section motif, borders-vs-shadows — and propose re-expressing it in the team's own tokens. Do not clone the reference; extract what makes it work and adapt.

---

### >>> GATE 1: Confirm source + method

Stop here. Present:

```
GATE 1 — DESIGN SOURCE

Location:   [in-repo: {HUB}/context/design-system/  |  external: <path>  (private: <yes/no>)]
Source:     [reference URL / brand / existing guide]
Teardown:   [results file path, or "adopting existing guide as-is"]

Method extracted:
- [one line per design move — e.g. "one accent, reserved for the logo only"]
- [e.g. "hierarchy by weight, not color"]
- [e.g. "borders over shadows"]

Re-expressed in our tokens? [yes — proceed to define / no — adopting verbatim]

Anything wrong before I define tokens?
```

Wait for response. Apply corrections, then proceed.

---

## Phase 2 — Token set & principles

### 2.1 Define a small token set

Propose CSS custom properties — keep it small and load-bearing:

- One off-white background surface, white for inner surfaces
- **One brand accent, reserved for the logo / single emphasis — never a fill**
- A 3-step text-color ramp (dark / medium / tertiary)
- A named set of **semantic** tint families (each tint means something — e.g. plan, action, reference — not decoration)
- A spacing scale (`--sp-*`) and a `--page-width`
- Body and display font families; a **weight cap** (e.g. 600 — retire 700/800)

### 2.2 Codify the principles

State the load-bearing rules the system enforces — typically: accent is the logo only; hierarchy by weight not color; generous white space; the fixed text-color set plus semantic tints; borders over shadows. Add logo rules (caps, inline SVG, fill-by-context) if there is a wordmark. Fold in the team's writing voice from `{HUB}/context/team/style/`.

---

### >>> GATE 2: Approve tokens, fonts, rules

Stop here. Present the token table (name → value → role), the fonts + weight cap, and the numbered principles. Ask: *"Approve these tokens and rules, or adjust?"* Wait for response. Do not proceed to write until the token set is locked.

---

## Phase 3 — Write system + templates + wire

### 3.1 Write the style guide

Generate one **self-contained HTML style-guide page** with the tokens as CSS variables and **live component demos** (type scale, color swatches, buttons, cards, callouts, a sample diagram). This page *is* the source of truth.

- in-repo → `{HUB}/context/design-system/style-guide.html`
- external → write into the external repo at the agreed path

Version it; if superseding an older guide, mark the old one deprecated explicitly.

### 3.2 Build per-artifact-type templates

For each artifact type the team produces (presentation, blog, one-pager), write `templates/<type>/template.html` plus a `templates/<type>/TEMPLATE.md` generation guide. `template.html` carries the full token block, nav/print CSS, and one example of each component/slide type. `TEMPLATE.md` carries the token values, the component catalog, and a **content → component** map so `/artifact` can generate without re-deriving. Drive visuals from a **data object**, not hand-placed elements, wherever a layout repeats.

### 3.3 Wire the pointer and CLAUDE.md

Update `{HUB}/context/tooling/design-system.md`: set `mode`, `path`, `templates_dir`, `access`, and fill the token summary cache (short — accent, background, text ramp, fonts, spacing, principles). The `rule:` line stays: re-read the source before generating. Confirm the CLAUDE.md "When you produce an HTML artifact" rule is present (it ships in the stub); if the team has a generated CLAUDE.md, ensure the rule survived bootstrap.

---

### >>> GATE 3: Approve writes

Stop here. Present:

```
GATE 3 — PROPOSED WRITES

Style guide:   [path]  ([N] components demonstrated)
Templates:     templates/<type>/{template.html, TEMPLATE.md}  [list per type]
Pointer:       {HUB}/context/tooling/design-system.md  (mode: <in-repo|external>, path: <path>)
CLAUDE.md:     rule present? [yes / needs adding]

Options:
  "go"      — execute all
  "review"  — walk through each file
  "cancel"  — no changes
```

Wait for response. Only write what is approved. Draft to `{PROJECT}/proposals/design-system/` first if the user wants a review pass before files land in their final location.

After execution, tell the user: *"Design system established. Produce artifacts from it with `/artifact`."*

---

## Behavioral boundaries

- **Establish once, generate many.** Do not produce a deck or blog here; that is `/artifact`. If the user asks for an artifact mid-flow, finish establishing, then hand off.
- **Extract the method, do not clone.** Re-express the reference's principles in the team's tokens; do not copy a competitor's exact palette and call it a system.
- **Small token set.** Resist a sprawling palette. One accent, three text colors, named semantic tints. If you reach for a fourth neutral, justify it.
- **The source file is authoritative.** The pointer's token summary is a cache. Never let the cache become the thing artifacts are generated from.
- **No false confidence on computed styles.** Any color, font, or measurement you report must come from a teardown you ran this session — not from memory of what a site "probably" uses.
- **Render to verify.** Open the style guide in a browser before Gate 3; do not ship a guide you have not seen rendered.
