# Pull requests

How `/process-workitem` opens the PR for a board work item.

Draft PRs: yes

- `yes` (the default, also when this file is absent) — the PR opens as a draft. The agent comments on the work item and reminds you to review the PR, mark it ready for review, and add a reviewer. The item moves to In Review per `context/tooling/board.md`: by you once the PR is ready, or automatically on the trigger it names (e.g. a review request).
- `no` — the PR opens ready for review; the reminder and the In Review move stay the same.

A host that refuses drafts gets a normal PR, and the agent says so.

## Merging

The reviewer who approves the PR also merges it. Approval and merge are one act: the author does not merge after an approval, and the agent never merges on the author's behalf. When several reviewers approve, the last one to approve merges.
