# Linear — label taxonomy reference

Three label prefixes carry semantics. Everything else is optional decoration the agent ignores.

| Prefix | Purpose | Examples |
|---|---|---|
| `type:` | What kind of work | `type:feature`, `type:bug`, `type:task`, `type:documentation` |
| `area:` | Domain / component / surface | `area:infrastructure`, `area:frontend`, `area:api`, `area:data` |
| `status:` | Additional state the workflow does not capture | `status:blocked`, `status:needs-review`, `status:waiting` |

## Rules

1. **Search before creating.** Linear lets anyone create labels; the agent must check the existing taxonomy first and propose, never create autonomously.
2. **One or two labels per category per issue.** A `type:` and an `area:` cover almost every Issue. `status:` is only added when the workflow state does not capture the situation (e.g. `Blocked` modelled as a label).
3. **Workspace vs. team labels.** Linear's workspace labels span teams; team labels are scoped. Use workspace labels **only** for genuinely cross-team concerns (e.g. `area:platform` shared by every product team).
4. **Priority is a native field, not a label.** Do not create `priority:*` labels — Linear has a Priority field; see `fields.md`.
5. **Archive quarterly.** Unused labels are pruned by a human; the agent only proposes archive candidates.

## Wizard responsibilities

**Mode A (from reference).** Apply the three-prefix scheme to the team's Linear workspace.

1. Surface the table above. Ask which `area:*` labels the team needs day one (it depends on the codebase — `area:api`, `area:frontend`, `area:data`, etc.).
2. **Create labels via the MCP** (`mcp__linear-server__create_issue_label`) once the user approves the list. Workspace-scoped or team-scoped per the user's call.
3. If the team already has labels without the prefix scheme (e.g. `bug` without `type:`), propose a migration plan — rename or duplicate-and-archive — but do not execute it without the user's explicit go-ahead.

**Mode B (assess current).** Use the MCP to list existing labels (`mcp__linear-server__list_issue_labels`).

1. Bucket the labels into: matches-prefix-scheme / informal / orphaned-priority / other.
2. Surface the buckets and propose normalisations (rename `bug` → `type:bug`, etc.). For each: accept / override / skip.
3. Update `context/team/conventions/REQUIRED/labels.md` to reflect the **actual** taxonomy on the board so future agent proposals match the team's reality.

## What lands in `board.md`

```
## Label taxonomy

Prefix scheme: type:* / area:* / status:* (per `context/team/conventions/REQUIRED/labels.md`).

In use today:
- type:* — <list>
- area:* — <list>
- status:* — <list>
- non-prefixed (kept for legacy): <list, if any>

Workspace-scoped vs. team-scoped: <e.g. area:* is workspace; type:* and status:* are team>.
Divergence from reference: <none | list>.
```
