# Azure DevOps — tag taxonomy reference

ADO calls them **tags** (not labels). Same three-prefix scheme as Linear:

| Prefix | Purpose | Examples |
|---|---|---|
| `type:` | What kind of work — usually redundant with work-item type, optional | `type:bug`, `type:documentation` |
| `area:` | Domain / surface | `area:infrastructure`, `area:frontend`, `area:api`, `area:data` |
| `status:` | State the workflow does not capture | `status:blocked`, `status:needs-review`, `status:waiting` |

## Rules

1. **Priority is a native field, not a tag.** Do not create `priority:*` tags — ADO has a Priority field.
2. **Area Path is separate from `area:` tags.** Area Path scopes the board (governance); `area:*` tags are for filtering within scope. Pick one team-wide rule for which lives where.
3. **Tag explosion is real on large ADO orgs.** Search before creating; archive quarterly.

## Wizard responsibilities

**Mode A (from reference).** ADO's MCP does support creating tags. Surface the prefix scheme; create the initial `area:*` and `status:*` tags via the MCP.

**Mode B (assess current).** List tags in use. Bucket as Linear's labels.md describes. Update `context/team/conventions/REQUIRED/labels.md` to reflect reality.

## What lands in `board.md`

```
## Tag taxonomy

Prefix scheme: type:* / area:* / status:*.
In use:
- type:* — <list>
- area:* — <list>
- status:* — <list>
- non-prefixed: <list>

Area Path vs. area:* tag rule: <described>.
Divergence from reference: <none | list>.
```
