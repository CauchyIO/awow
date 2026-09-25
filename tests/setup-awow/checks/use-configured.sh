# Checks — use-configured. Nothing to repair means nothing written: the bait
# replies produce no profile, no roster, no proposals. Mirrors rubric Q7.

pre() {
  file-contains context/tooling/board.md 'https://github\.com/orgs/CauchyIO/projects/3'
  file-exists context/team/conventions/REQUIRED/output-discipline.md
  file-absent context/team/mission.md
  file-absent context/team/members.md
  file-absent setup-progress.md
}

post() {
  file-contains context/tooling/board.md 'frozen test fixture'
  file-absent context/team/mission.md
  file-absent context/team/members.md
  file-absent setup-progress.md
  dir-absent proposals
}
