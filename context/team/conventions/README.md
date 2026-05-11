# context/team/conventions/

Naming, tagging, and structural conventions. *How* the team names things, *which* labels apply, *what* branches look like.

## Two tiers

### REQUIRED/

The minimum set the agent needs to operate. Four files:

- `issue-titles.md` — verb-first patterns
- `labels.md` — label taxonomy with prefixes (`type:`, `area:`, `status:`)
- `branches.md` — branch naming rules
- `output-discipline.md` — board-output brevity and placement rules

`/setup-awow` Step 2 populates these. The wizard refuses to consider the team bootstrapped without them.

### OPTIONAL/

Conventions that are *deferrable*. They appear in the tree as `# OPTIONAL — defer` stubs and are not asked about during initial setup. Fill them in when the team encounters a problem they would solve. Examples:

- `infra-naming.md` — cloud resource naming
- `data-objects.md` — table, schema, catalogue naming
- `code-style.md` — language-specific style beyond what the linter enforces

## How the agent uses this

The agent reads `REQUIRED/` at session start and applies the rules without being asked. When generating any artefact — a story title, a label suggestion, a branch name — the agent matches the team's pattern.

## Why split REQUIRED / OPTIONAL

The most common reason teams stall before they start is feeling they need to define every standard before turning the agent on. Splitting the set means the team can ship after defining four files. Everything else can be `# OPTIONAL — defer` for weeks without breaking the model.
