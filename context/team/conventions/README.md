# context/team/conventions/

Naming, tagging, and structural conventions. *How* the team names things, *which* labels apply, *what* branches look like.

## Two tiers

### REQUIRED/

The minimum set the agent needs to operate. Four files:

- `issue-titles.md` — verb-first patterns
- `labels.md` — label taxonomy with prefixes (`type:`, `area:`, `status:`)
- `branches.md` — branch naming rules
- `output-discipline.md` — board-output brevity and placement rules

`/setup-awow` proposes these from the board's observed patterns; each is a proposal the team can strike or edit.

### OPTIONAL/

Conventions that are *deferrable*. They appear in the tree as `# OPTIONAL — defer` stubs and are not asked about during initial setup. Fill them in when the team encounters a problem they would solve. Examples:

- `infra-naming.md` — cloud resource naming
- `data-objects.md` — table, schema, catalogue naming
- `code-style.md` — language-specific style beyond what the linter enforces

## How the agent uses this

The agent reads `REQUIRED/` at session start and applies the rules without being asked. When generating any artefact — a story title, a label suggestion, a branch name — the agent matches the team's pattern.

## Repo-level conventions

This folder holds the team's conventions, kept in the anchor and shared by every repo. A repo that needs a convention of its own — or a different one — keeps it at `{PROJECT}/context/team/conventions/`, in the same `REQUIRED/` and `OPTIONAL/` layout. Where the repo *is* the anchor (a standalone repo), the two are one folder and there is nothing to layer.

**Per rule, repo wins.** The agent reads the anchor's file, then the repo's file at the same path, and applies both. Where a repo rule conflicts with an anchor rule, the repo's applies; every anchor rule the repo file does not touch still applies. No repo file means the anchor's file alone.

Example — the anchor's `REQUIRED/branches.md` has three rules: the `{user}/{TEAM}-{number}-{slug}` pattern, a 60-character limit, and `feature/{slug}` for long-lived branches. A repo that wants a different pattern writes only that:

```markdown
# Branches — this repo

Name branches `issue/{TEAM}-{number}`. Replaces the anchor's branch pattern rule; the length limit and `feature/` rule still apply.
```

Writing repo rules:

- **Name the anchor rule you change.** "Replaces the anchor's branch pattern rule" leaves the agent nothing to guess.
- **Drop a rule explicitly.** "The anchor's `feature/{slug}` rule does not apply in this repo." Silence keeps it.
- **Replace the whole file only on purpose.** Frontmatter `replaces: true` makes the repo file stand alone; the anchor's file is not read. The repo then stops receiving the team's later changes to that file.
- **`REQUIRED/board-linkage.md` is add-only.** A repo may add rules to it, never change or drop the anchor's — those rules are how awow keeps the board true, and overriding them switches awow off for the repo. `replaces: true` does not apply to it.
- **Overriding the rest of `REQUIRED/` affects the shared board.** Labels and issue titles are seen by every repo on the team. It is allowed; `/setup-awow --check` names each `REQUIRED/` override so it is never a surprise.

`/update-context` lands a rule here when the user scopes it to the repo ("in this repo we…"), and in the anchor otherwise.

## Why split REQUIRED / OPTIONAL

The most common reason teams stall before they start is feeling they need to define every standard before turning the agent on. Splitting the set means the team can ship after defining four files. Everything else can be `# OPTIONAL — defer` for weeks without breaking the model.
