# Labels

`/setup-awow` Step 2 populates this from your team's existing pattern, or guides you to one. Stub below until then.

## Pattern (TODO — fill via /setup-awow)

Labels use a prefix to declare their category. Each issue gets at most one or two labels per category.

| Prefix | Purpose | Examples |
|---|---|---|
| `type:` | What kind of work | `type:feature`, `type:bug`, `type:task`, `type:documentation` |
| `area:` | Domain or component | `area:infrastructure`, `area:frontend`, `area:api`, `area:data` |
| `status:` | Additional context beyond the workflow state | `status:blocked`, `status:needs-review`, `status:waiting` |

Three rules:
1. Search existing labels before creating new ones.
2. Workspace-level labels only for cross-team concerns; team-scoped otherwise.
3. Archive unused labels quarterly.

Priority is set via the board tool's native priority field, not via labels.
