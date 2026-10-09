# Board — file-based (test fixture)

The team's board is this repository: one markdown file per issue under
`board/issues/`, named `<ID>.md` where IDs run `T-101`, `T-102`, … Create an issue
by writing the next free `T-<n>.md`.

## Issue file shape

```markdown
---
id: T-101
title: <verb-first title per conventions/REQUIRED/issue-titles.md>
state: todo | in-progress | in-review | done
labels: [<from conventions/REQUIRED/labels.md>]
---

<body — intent + acceptance criteria, per conventions/REQUIRED/output-discipline.md>
```

## Mechanics and limitations

- **Search** = read the files under `board/issues/`.
- **Comment** = append to the issue file under a `## Comments` heading with a dated
  entry; the body above the heading is never rewritten for status.
- **No native blocked-by relation.** Record dependencies as a `Blocked by: <ID>`
  line in the body.
- **States move by editing the `state:` frontmatter line.** The agent owns the moves
  todo → in-progress → in-review; done is a human's move.
- **No pull requests.** This repository has no remote. Delivering code means a commit on a
  branch named per `conventions/REQUIRED/branches.md`, and a comment on the item naming the
  branch and the commit.
