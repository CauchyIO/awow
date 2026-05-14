# GitHub Issues — label taxonomy reference (skeleton)

GitHub's labels are flat and repo-scoped. Same three-prefix scheme:

| Prefix | Purpose | Examples |
|---|---|---|
| `type:` | What kind of work | `type:feature`, `type:bug`, `type:task`, `type:documentation` |
| `area:` | Domain / component | `area:infrastructure`, `area:frontend`, `area:api` |
| `status:` | State not captured by the Project Status field | `status:blocked`, `status:needs-review` |

The repo's existing labels often pre-date the operating model (`good first issue`, `help wanted`, etc.). Keep them; they have semantics outside the prefix scheme.

## Wizard responsibilities

**Mode A.** Create the prefix-scheme labels via the MCP or `gh label create`. Leave existing labels as-is.

**Mode B.** List labels; bucket as Linear's labels.md describes. Surface duplicates (`bug` and `type:bug` both present).

## What lands in `board.md`

```
## Label taxonomy

Prefix scheme: type:* / area:* / status:*.
In use:
- type:* — <list>
- area:* — <list>
- status:* — <list>
- legacy / GitHub default: <list — e.g. `good first issue`, `help wanted`>

Divergence from reference: <none | list>.
```
