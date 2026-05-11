# proposals/

The agent drafts every artefact here first. Humans review. Only after approval does the wizard move the artefact to its final location.

This is the **proposal-first principle** in physical form: iterate on the cheap-to-change artefact (a markdown file), not on the expensive one (the board, the codebase, the knowledge base).

## Structure

The agent organises proposals by command:

| Subfolder | Created by |
|---|---|
| `setup/<step>/` | `/setup-awow` — one folder per step it has reached |
| `refinement/` | `/refinement-prep` |
| `transcripts/` | `/process-transcript` |
| `<work-item-id>.md` | `/process-workitem` — one file per work item being planned |
| `awow-add/` | `/awow-add` — one file per command being promoted |

## Lifecycle

1. Agent produces an artefact under `proposals/<command>/<name>.md`.
2. User reviews.
3. If approved: wizard moves to final location (`context/`, the board, etc.).
4. If revised: agent updates the proposal; user re-reviews.
5. If rejected: proposal is deleted or marked superseded.

## Retention

Approved proposals can be deleted after they land — the version-controlled artefact lives in its final location. Rejected proposals are worth keeping briefly to understand what didn't work; clean them up at retrospectives.

The `proposals/` folder itself is tracked (via `.gitkeep`) but its contents are working artefacts. Be deliberate about which proposals you commit.
