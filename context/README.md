# context/

Everything the agent needs to know about *this team* in *this place*. The agent reads from here at session start; the team writes to here through `/setup-awow` and ongoing maintenance.

## Layout

| Subfolder | Purpose |
|---|---|
| `team/` | The team's own surfaces — mission, members, style, conventions |
| `knowledge-base/` | Durable reference — patterns, decisions, runbooks, glossary. Mining is tuned by `mining-policy.md`; the inbox is drained into here by `synthesis.md`. Default location; relocatable via `tooling/knowledge-base.md` |
| `kb-inbox/` | Committed staging for durable-knowledge candidates awaiting promotion (the capture→synthesize spine). Default location; relocatable via `tooling/knowledge-base.md` |
| `company/` | Stakeholders, neighbouring teams, RACI |
| `quarterly/` | Quarterly-cycle inputs — slidedecks, OKRs, planning artefacts |
| `tooling/` | Board, harness, and MCP choices for this team |

## What lives here vs elsewhere

- **Story-specific content** lives on the board, never here. The story body holds intent + acceptance criteria; comments hold status; durable content gets promoted into `context/knowledge-base/` and linked back.
- **Generated artefacts** (proposals, traces) live at the repo root in their own folders, not under `context/`.
- **Code, scripts, schemas** live in the codebase (which may be this repo if the team has grown into a mono-repo, or sibling repos).

## How `/setup-awow` populates this folder

Step-by-step. `setup-progress.md` at the repo root tracks which sub-areas have been completed. The wizard is incremental and resumable; not all of `context/` needs to be filled in to be useful — only `context/tooling/board.md` (Step 0) is required.
