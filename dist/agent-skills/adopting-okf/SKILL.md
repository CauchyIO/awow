---
name: adopting-okf
description: "Use when a user asks to make a repository or Markdown knowledge collection OKF-compatible, okify its documentation, add OKF frontmatter, or create progressive-disclosure indexes."
---

# Adopt OKF

Adopt the [Open Knowledge Format v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
as a navigation layer over documentation that already exists. Preserve authorship: add metadata
and indexes, not invented or rewritten knowledge.

## Boundaries

- Work only in the repository or collection the user explicitly authorized for modification.
- When reached through ANCHOR canonical-source routing, remain read-only; do not adopt OKF in
  the anchored repo as a side effect.
- Preserve every document body and every unknown frontmatter field.
- Do not create missing tutorials, explanations, or decisions. Report gaps separately.

## Adoption

1. Inventory the Markdown documents and agree the bundle boundary. Exclude generated, vendored,
   private, and archival material unless the user includes it.
2. Define a small type profile from the collection's existing concepts. OKF requires a non-empty
   `type` on each concept document; prefer stable domain nouns over folder names.
3. Add or merge frontmatter. Keep existing fields. Add `title`, `description`, `resource`, and
   `tags` only when the value is supported by the document or repository. Use OKF v0.2 freshness
   fields (`generated.at`, `verified`, `status`, `stale_after`) only when their evidence exists.
4. Create `index.md` files for progressive disclosure. Only the bundle-root index carries:

   ```yaml
   ---
   okf_version: "0.2"
   ---
   ```

   Link concepts and child indexes with ordinary Markdown links. Keep entries short enough that
   an agent can choose what to read next without loading the whole bundle.
5. Add `log.md` only when the collection needs a human-readable update log; use ISO date headings.
6. Show the metadata/index diff before landing it. Treat content enrichment as a separate,
   explicitly approved task.

## Verify

- Every in-scope concept has a non-empty `type`.
- Root `index.md` declares OKF v0.2; nested indexes have no frontmatter.
- Every concept is reachable from its nearest ancestor index.
- Local Markdown links resolve; remote resources remain canonical URIs.
- Document bodies and pre-existing frontmatter values are unchanged.

Broken links do not make a bundle unreadable under OKF, but report them and fix those introduced
by the adoption before calling the work complete.
