# Issue titles

Verb-first. The title alone tells you what the issue delivers; the body adds acceptance criteria. Vague titles ("setup-awow improvements", "fix bug") fail this convention.

## Pattern

| Pattern | Example | When to use |
|---|---|---|
| `Implement {thing}` | Implement `/awow-status` command | Net-new capability |
| `Add {thing} to {surface}` | Add MCP-alternative section to `context/tooling/boards/github-issues/reference/mcp.md` | Extending an existing artefact |
| `Fix {symptom} in {area}` | Fix `gh project list` returning empty when all org projects are closed | Bug with a known symptom |
| `Update {thing}` | Update `/setup-awow` Step 1 to surface `gh` CLI as an MCP alternative | Modifying existing behaviour |
| `Remove {thing}` | Remove `voice-memo-capture` references from refinement-prep | Decommission / cleanup |
| `Draft {thing}` | Draft `dogfood/context/knowledge-base/decisions/0001-gh-cli-vs-mcp.md` | Content or documentation |
| `Define {thing}` | Define `dogfood`-label inflation-control pattern in github-issues reference | Convention, policy, or standard |

## Scope discipline

Awow issues that span more than one of `.agents/commands/`, `.agents/skills/`, `tools/`, and `context/tooling/boards/` are almost always too big. Split before opening. The dogfood `/refinement-prep` exists to make that split cheap.

## What fails

- **Topic titles**: "OAuth", "setup-awow", "the gh thing". A topic is not work.
- **Vague verbs**: "Improve...", "Refactor...", "Look into...". Replace with one of the patterns above or close the issue as not-yet-actionable.
- **Bundled scope**: "Fix X and also tighten Y and Z". Split into one issue per outcome.
