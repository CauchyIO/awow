# Checks — install-walkthrough. End-to-end Step 0 → Step 3. Mirrors rubric
# Q15–Q19 (the full post-run state block).

pre() {
  dir-exists .venv
  file-exists .claude/commands/setup-awow.md
  file-exists .github/prompts/setup-awow.prompt.md
  file-absent setup-progress.md
  dir-exists context/tooling/boards/github-issues/reference
}

post() {
  file-exists context/tooling/board.md
  file-contains context/tooling/board.md 'CauchyIO'
  file-contains context/tooling/board.md 'gh-cli'
  file-contains context/tooling/board.md 'https://github\.com/orgs/CauchyIO/projects/3'
  file-contains context/tooling/board.md '## State machine'
  file-contains context/tooling/board.md '## Hierarchy'
  file-contains context/tooling/board.md '## Label taxonomy'
  file-contains context/tooling/board.md '## Required fields'
  file-contains context/tooling/board.md '## Team page conventions'
  file-exists context/team/mission.md
  file-contains context/team/mission.md 'Cauchy helps engineering teams'
  file-exists context/team/conventions/REQUIRED/issue-titles.md
  file-exists context/team/conventions/REQUIRED/labels.md
  file-exists context/team/conventions/REQUIRED/branches.md
  file-exists context/team/conventions/REQUIRED/output-discipline.md
  file-exists setup-progress.md
  file-contains setup-progress.md '\[x\].*Step 0'
  file-contains setup-progress.md '\[x\].*Step 1'
  file-contains setup-progress.md '\[x\].*Step 2'
  file-contains setup-progress.md '\[x\].*Step 3'
}
