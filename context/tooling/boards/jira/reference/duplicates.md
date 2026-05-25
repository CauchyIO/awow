# Jira — duplicate avoidance reference (skeleton)

Out of the box Jira has **no automatic duplicate detection** (some Marketplace apps add it). Prevention is search-before-create plus the built-in "Duplicate" issue link.

## Native capabilities & limits

- **Search:** JQL (`summary ~ "<terms>"`, `text ~ "<terms>"`) or quick search. Keyword/text; vary terms.
- **Marking a duplicate:** the standard **"duplicates / is duplicated by"** issue link type. Link the newer issue to the canonical one and resolve it as `Duplicate` (if that resolution exists in the workflow). No automatic merge.

## Wizard responsibilities

**Mode A (from reference).** Confirm the JQL search recipe and that the `Duplicate` resolution and link type exist in the project workflow; if not, add to the manual checklist.

**Mode B (assess current).** Check whether the `Duplicate` resolution and duplicate link type are present and used.

## What lands in `board.md`

```
## Avoiding duplicates

No auto-detection — **search before creating.**
Search: JQL `summary ~ "<terms>" OR text ~ "<terms>"` (keyword; try several).
Found one? Comment or advance it. Genuine duplicate: add a **"duplicates"**
link to the canonical issue and resolve as `Duplicate`.
```
