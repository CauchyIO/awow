# context/team/

The team's identity, conventions, and writing style. This is the most-read part of the context layer. Keep it small, accurate, and current.

## Files in this folder

| File | What it is | Hard requirement? |
|---|---|---|
| `mission.md` | One-sentence team mission | Strongly recommended (gated by `/setup-awow` Step 1) |
| `vision.md` | Longer-form direction | Optional |
| `members.md` | Roles, responsibilities, focus areas | Recommended |
| `style/` | Writing-mode guidance (board / comments / prose) | Populated by Step 3 |
| `conventions/` | Naming and tagging rules (REQUIRED + OPTIONAL) | Populated by Step 2 |

## How the agent uses this

- Mission tells the agent what proposals should serve. Vague mission → vague behaviour.
- Members lets the agent attribute work, disambiguate transcripts, and respect reporting lines.
- Style governs what the agent writes — terse on the board, prose elsewhere.
- Conventions govern *how* the agent names everything — titles, labels, branches, infrastructure resources.

## Update cadence

Event-driven, not calendar-driven. When the mission changes, update. When a member joins or leaves, update. When a convention changes, update. If nothing has changed in a month, nothing needs to happen.

A stale team file does not produce broken agent behaviour — it produces *slightly-wrong* agent behaviour, which is harder to notice. Refresh at retrospectives.

## What does NOT live here

- Specific stakeholders or neighbouring teams → `context/company/`
- Durable architectural or pattern knowledge → `context/knowledge-base/`
- Which board / MCP / harness the team uses → `context/tooling/`
