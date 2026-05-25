# Azure DevOps — duplicate avoidance reference

Azure Boards has **no automatic duplicate detection**. Prevention is search-before-create plus the built-in "Duplicate / Duplicate Of" work-item link.

## Native capabilities & limits

- **Search:** the Boards search box or WIQL (`[System.Title] CONTAINS "<terms>"`). Keyword/text; vary terms. (Work-item search requires the search extension to be enabled.)
- **Marking a duplicate:** the **"Duplicate / Duplicate Of"** link type. Link the newer work item as *Duplicate Of* the canonical one and close it with reason `Duplicate` (or set state *Removed*, per the process template). No automatic merge.

## Wizard responsibilities

**Mode A (from reference).** Confirm the search approach and that the process template exposes the Duplicate link type and a suitable close reason; otherwise add to the manual checklist.

**Mode B (assess current).** Check whether Duplicate links are in use and which close reason the team applies.

## What lands in `board.md`

```
## Avoiding duplicates

No auto-detection — **search before creating.**
Search: Boards search box, or WIQL `[System.Title] CONTAINS "<terms>"`.
Found one? Comment or advance it. Genuine duplicate: add a **"Duplicate Of"**
link to the canonical work item and close it with reason `Duplicate`.
```
