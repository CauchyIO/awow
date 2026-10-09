# Linear — duplicate avoidance reference

Linear is the most dedup-friendly of the supported tools, but its help is **advisory, not enforcing** — it surfaces possible duplicates and offers a relation, yet nothing stops two issues for the same work. Search-before-create still applies.

## Native capabilities & limits

- **Similar-issue surfacing:** on the create screen Linear suggests existing issues with similar titles. Read these before saving — the cheapest dedup signal you'll get.
- **Search:** full-text search across the workspace (and via the MCP). Decent recall, still keyword-driven, so vary terms.
- **Marking a duplicate:** a first-class **"Mark as duplicate"** relation that links the duplicate to the canonical issue and cancels it. Prefer this over a bare cancel — it preserves the link.

## Wizard responsibilities

**Mode A (from reference).** Confirm the team relies on similar-issue surfacing + search before creating, and resolves duplicates with the native relation (not a bare cancel). Record in `board.md`.

**Mode B (assess current).** Note whether duplicate relations are actually in use (a sign the discipline already exists) or whether duplicates tend to be cancelled without linking.

## What lands in `board.md`

```
## Avoiding duplicates

Search before creating, and **read Linear's similar-issue suggestions** on the
create screen before saving. Found an existing issue? Comment or advance it —
do not open a second. Genuine duplicate: use **Mark as duplicate** (not a bare
cancel) so the link to the canonical issue is preserved.
```
