# Team workitem archetypes

This folder is where the team extends the archetype registry. awow ships a small set of generic handlers covering the universal work shapes (`feature`, `bugfix`, `refactor`, `spike`, `incident`); `/process-workitem` reads this folder **over** that shipped set — a file named after a shipped handler replaces it, a new name registers a new archetype.

Keep it sparse. The shipped handlers already carry the universal discipline; add a file only when a kind of work recurs here with rules of its own, or when a shipped handler's rules need adjusting for this team.

Use plain Markdown. No identifiers, inheritance declarations, or configuration syntax — `/process-workitem` matches the incoming story against the prose and needs no router edit when a file is added.

## Registering a new archetype

Name the file after the kind of work, for example `infra-change.md`, with sections for:

```markdown
# Infra change

## When this archetype applies

[Describe the work items that should route here.]

## Validation requirements

[State checks to run *before* planning, and what counts as a stop condition.]

## Planning rules

[Describe ordering, safety, and scoping rules specific to this kind of work.]

## Common pitfalls

[Describe the failure modes this discipline exists to prevent.]

## Verification checklist additions

[List checks beyond the generic tests/build/lint gate.]
```

## Overriding a shipped handler

Copy the shipped handler's filename (for example `bugfix.md`) and write the team's version; it wins wholesale — there is no merging within a file, so carry over whatever shipped rules still apply.

Write or edit these files directly when the team already knows its discipline, or let `/process-workitem` propose one: when no archetype matches, it drafts a stub under `proposals/archetypes/` for approval into this folder. Use `/update-context` to amend an existing handler when the team later states a durable correction.
