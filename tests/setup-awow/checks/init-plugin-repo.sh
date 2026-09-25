# Checks — init-plugin-repo. Three context artefacts land, the existing
# AGENTS.md text survives with the pointer appended, and no wizard state is
# left behind. Mirrors rubric Q8–Q11.

pre() {
  file-contains AGENTS.md 'make test'
  file-absent context/tooling/board.md
  dir-absent context/team
  file-absent setup-progress.md
}

post() {
  file-exists context/tooling/board.md
  file-contains context/tooling/board.md 'https://github\.com/orgs/CauchyIO/projects/3'
  file-contains context/tooling/board.md 'gh-cli'
  file-exists context/team/conventions/REQUIRED/issue-titles.md
  file-exists context/team/conventions/REQUIRED/labels.md
  file-exists context/team/conventions/REQUIRED/branches.md
  file-exists context/team/conventions/REQUIRED/output-discipline.md
  file-contains AGENTS.md 'make test'
  file-contains AGENTS.md 'context/tooling/board\.md'
  file-absent setup-progress.md
  dir-absent proposals/setup
}
