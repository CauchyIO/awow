# Labels

Prefix-scoped taxonomy. Every label on an issue comes from this file — no free-form
labels, no urgency shouting (priority lives in `state:` and ordering, not labels).

- `type:` — `type:feature`, `type:bug`, `type:chore` (exactly one per issue)
- `area:` — `area:api`, `area:web`, `area:ops` (at most one per issue)
- `status:` — `status:blocked` (only while a `Blocked by:` line exists)
