# Pull requests

How `/process-workitem` opens the PR for a board work item.

Draft PRs: yes

- `yes` (the default, also when this file is absent) — the PR opens as a draft. The agent comments on the work item and reminds you to review the PR, mark it ready for review, and add a reviewer. The item moves to In Review when you mark the PR ready — by you, or automatically when `context/tooling/board.md` names an integration as its owner.
- `no` — the PR opens ready for review; the reminder and the In Review move stay the same.

A host that refuses drafts gets a normal PR, and the agent says so.
