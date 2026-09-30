# Pull requests

How `/process-workitem` opens the PR for a board work item.

Draft PRs: yes

- `yes` (the default, also when this file is absent) — the PR opens as a draft. The agent comments on the work item and reminds you to review the PR, mark it ready for review, and add a reviewer. You move the item to In Review when you mark the PR ready.
- `no` — the PR opens ready for review; the reminder and the human In Review move stay the same.

A host that refuses drafts gets a normal PR, and the agent says so.
