# Proposal — Design-system capability for awow

**Status:** approved; Phases 1–3 implemented (render skill, §3.7, deferred). See "Built" below.
**Trigger:** the design-system + artifact-generation workflow that ran across the `design` and `linear` repos (reconstructed from MLflow session traces) is a load-bearing way of working that currently lives only in one person's head. Capture it so adopters get it without it being re-explained. Secondary: HTML artifacts (solution designs, presentations, blogs) should follow a design system when one is present.

---

## 1. The workflow we are capturing

Reconstructed from 86 `design` sessions and 38 `linear` sessions. Two halves.

### Establishing a design system (rare — once per brand)
1. **Tear down a reference you admire, empirically.** Use Playwright/Chrome headless to capture screenshots *and computed styles* (colors as RGB, font families, sizes, tracking) into a results file. Extract the *method* (restraint, semantic color, type pairing, per-page motif), not the pixels.
2. **Define a small token set** as CSS custom properties: one off-white background, white, one brand accent reserved for the logo only, a 3-step text-color ramp, a named set of semantic tint families, a spacing scale (`--sp-*`), a `--page-width`. Cap font weight (e.g. 600). Choose body vs. display faces.
3. **Write the system as one self-contained HTML style guide** with live component demos. This *is* the source of truth, versioned; old versions are deprecated explicitly.
4. **Codify the rules as enforced agent instructions** (CLAUDE.md): the principles, logo rules (caps, inline SVG, fill-by-context), "borders over shadows," semantic tints, writing style. Add a coherence audit checklist.
5. **Build reusable per-artifact-type templates** (`templates/<type>/template.html` + a `TEMPLATE.md` generation guide carrying the token block, the component catalog, and a content→component map). Build visuals from a **data object**, not hand-placed elements.

### Producing an artifact from it (frequent)
1. Board-first: locate/create the tracking item, set in-progress.
2. **Draft and iterate content in markdown** (`slides.md` / `<artifact>.md`) with the user — agree structure and tone *before* generating any HTML.
3. **Generate HTML from the template**, preserving its `<style>` block and nav JS verbatim. Choose component/slide types from the catalog.
4. Prefer **HTML/CSS diagrams** over raw SVG or Mermaid; keep artifacts light on text, heavy on visual.
5. **Verify layout with Playwright** (computed layout, not just eyeballing), then **export PDF via Chrome headless** (not WeasyPrint — modern CSS grid/clamp/viewport units survive). Fix overflow, regenerate.
6. Commit, push, update the board (in review, reviewer, link to the markdown source).

### Cross-repo reuse mechanism (the friction point)
No package, symlink, or build import. The `linear` repo consumed the `design` repo by: a **sibling-repo absolute path** named as the "authoritative style source" in an instruction file, a rule to *"always re-read the source file to pick up updates,"* and a locally-cached template as the practical source of truth. Manual, agent-mediated, drift-prone. **awow should make this mechanism explicit and first-class** rather than leaving it as a convention buried in one command file.

---

## 2. Decisions (confirmed with the user)

1. **Setup role — opt-in extra + setup probe.** Design-system support is not a core step for every team (board-only teams never make HTML). It lives as a Spread command discoverable via `/awow-add`, and `/setup-awow` Step 8 asks one yes/no — *"does your team produce styled HTML artifacts?"* — and only then points at it.
2. **Reference mechanism — support both via a pointer file.** `context/tooling/design-system.md` is the single source of truth for *whether* a design system exists and *where*. It supports `mode: in-repo` (system lives under `context/design-system/`) or `mode: external` (a sibling/other repo path, the Cauchy reality), plus the always-re-read rule.
3. **What to capture — two flows + wire existing.** A rare **establish** command and a frequent **apply/generate** command, *plus* "adopt the design system if present" wired into `/solution-design-flow`'s Presentation track and into CLAUDE.md so even ad-hoc HTML obeys it.

---

## 3. Deliverables

### 3.1 `context/tooling/design-system.md` — the pointer (new)
Single source of truth for design-system presence and location. Shipped as a stub with `mode: absent` so commands can cheaply detect "no design system → don't enforce." Shape:

```yaml
---
mode: absent | in-repo | external
path: ""            # e.g. context/design-system/style-guide.html  OR  ~/repos/design/cauchy-style-guide-v2.html
templates_dir: ""   # e.g. context/design-system/templates/  OR  ~/repos/design/templates/
rule: "Always re-read the source file before generating; it is authoritative over any cached token summary below."
---
```
Body: a cached token summary (accent, background, text ramp, fonts, spacing scale, principles) for quick reference, explicitly subordinate to the source file. Indexed from `context/tooling/README.md`.

### 3.2 `.agents/commands/design-system.md` — establish flow (new, `phase: spread`)
Gated pipeline (mirrors `/solution-design-flow`'s gate discipline):
- **Gate 1 — source & method.** In-repo or external? Reference site/brand to tear down? Run the Playwright computed-style teardown; present extracted method + proposed tokens.
- **Gate 2 — token set & principles.** Confirm the small token set, fonts, weight cap, semantic tints, the principles, logo rules.
- **Gate 3 — write.** Generate the self-contained style-guide HTML + the per-artifact-type template(s) + `TEMPLATE.md`; write `context/tooling/design-system.md`; append the CLAUDE.md rule. Auto-discovered by `/awow-add` via its `phase: spread` frontmatter — no `/awow-add` code change needed.

### 3.3 `.agents/commands/artifact.md` — apply/generate flow (new, `phase: spread`)
Working name `/artifact` (final name open — could also be `/design-artifact`). Drives the frequent pipeline: read the pointer → board-first → markdown content with gates → generate HTML from the template preserving `<style>`/JS → HTML/CSS diagrams over SVG/Mermaid → Playwright verify → Chrome-headless PDF → board update. If the pointer is `mode: absent`, it offers `/design-system` first or proceeds with sane defaults on the user's say-so.

### 3.4 Wire into `/solution-design-flow` (edit)
- **Phase 0** — add `context/tooling/design-system.md` to the context read list.
- **Phase 3.1 Presentation track** — when the pointer is not `absent`, require the deck to adopt the design system (read the source, use the template); when absent, behave as today.

### 3.5 CLAUDE.md rule (edit `.agents/CLAUDE.md` stub + `bootstrap-claude-md.py` template)
New rule: *"When you produce an HTML artifact and `context/tooling/design-system.md` is not `mode: absent`, read the named source file and adopt its tokens/templates; never invent styling. Re-read the source each time — the cached summary can drift."* Flows into the generated CLAUDE.md at Step 5.

### 3.6 `/setup-awow` Step 8 probe (edit)
After surfacing the spread/standardise extras, ask: *"Does your team produce styled HTML artifacts (decks, blogs, solution designs)?"* If yes, point at `/awow-add design-system`. Record the answer in `setup-progress.md`. No new required step; board-only teams answer no and move on.

### 3.7 Optional — a render skill
The Playwright-verify + Chrome-headless-PDF mechanics are reusable across `/artifact`, `/solution-design-flow`, and digests. Candidate for a small `.agents/skills/html-artifact-render` skill so the rendering recipe isn't duplicated. Flagged as optional; can fold into the commands first and extract later.

---

## 4. Phasing

1. Pointer file + CLAUDE.md rule + setup probe (cheapest, makes "if present" meaningful everywhere).
2. `/design-system` establish command.
3. `/artifact` apply command + `/solution-design-flow` wiring.
4. Optional render skill extraction.

After approval, each artifact lands via the normal proposal-first loop. This file is the umbrella proposal; individual command drafts go to `proposals/awow-add/<name>.md` / `proposals/setup/...` as the existing flow dictates.

---

## 5. Open questions

- **Apply-command name:** `/artifact` vs `/design-artifact` vs folding entirely into `/solution-design-flow`. Leaning `/artifact` (general — slides, blogs, one-pagers all flow through it).
- **External-mode access:** when `mode: external` and the repo is private (Cauchy's was — MCP 404, `gh`-only), the rule must tell the agent to read via local path, not MCP. Worth a one-line note in the pointer.
- **Render skill now or later:** extract 3.7 up front, or after the two commands prove the recipe? (Deferred — recipe currently lives inline in `/artifact` Phase 4 and `/design-system`; extract once it proves out.)

---

## Built

- `context/tooling/design-system.md` — pointer, ships `mode: absent`. Indexed in `context/tooling/README.md`.
- `.agents/CLAUDE.md` — "When you produce an HTML artifact" rule (reads the pointer, adopts the system when present, re-reads the source).
- `.agents/commands/design-system.md` — establish flow, `phase: spread`, 3 gates.
- `.agents/commands/artifact.md` — apply/generate flow, `phase: spread` (`/artifact` name chosen over `/design-artifact`).
- `.agents/commands/solution-design-flow.md` — Phase 0 reads the pointer; Phase 3.1 presentation track adopts the system when present and hands rendering to `/artifact`.
- `.agents/commands/setup-awow.md` — Step 8 detects an existing system, otherwise asks the styled-artifacts question and suggests `/awow-add design-system` (implicit, opt-in — per user steer).
- `.agents/commands/README.md` table + `tools/gather.py` mirroring (`.claude/`, `.github/`).

**Note:** `tools/bootstrap-claude-md.py` is still a v0.1 skeleton (`NotImplementedError`). The CLAUDE.md rule currently lives in the stub, which is the live file. When the bootstrap is implemented, it must carry the "When you produce an HTML artifact" rule forward into the generated CLAUDE.md.
