# Labels

Labels use a prefix to declare their category. Each issue gets at most one or two labels per category. Priority is set via the board tool's native priority field, not via labels.

## Prefixes

| Prefix | Purpose | awow examples |
|---|---|---|
| `type:` | What kind of work | `type:feature`, `type:bug`, `type:task`, `type:documentation`, `type:prompt-iteration` |
| `area:` | Which awow surface is touched | `area:setup`, `area:skills`, `area:commands`, `area:gather`, `area:context`, `area:tooling`, `area:docs` |
| `status:` | Context beyond the workflow state | `status:blocked`, `status:needs-review`, `status:waiting` |

## Special labels

| Label | Purpose | Lifecycle |
|---|---|---|
| `awow-test` | Marks an issue generated during a test walkthrough (dogfooding awow against itself for prompt iteration). | Bulk-closed by `tools/reset-adopter-state.py` (and therefore by `/awow-reset`). Every test-walkthrough issue MUST carry it. |
| `good-first-issue` | Standard GitHub label; signals a low-context entry point for new contributors. | Survives resets. |

## Three rules

1. **Search before creating.** Run `gh label list -R CauchyIO/awow` before defining a new label.
2. **Labels are repo-scoped** on GitHub (unlike Linear's workspace labels). Issues opened against `CauchyIO/awow` see only the labels defined on this repo.
3. **Archive unused labels quarterly.** Stale labels make `gh label list` noisy and obscure the active taxonomy.

## Mapping to wizard outputs

`/refinement-prep`, `/process-workitem`, and any command that creates an issue MUST apply: exactly one `type:`, exactly one `area:`, zero or more `status:`, and `awow-test` if invoked during a test walkthrough.
