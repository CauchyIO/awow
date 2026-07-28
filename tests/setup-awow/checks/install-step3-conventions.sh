# Checks — install-step3-conventions. Step 3 drafts the four REQUIRED
# conventions proposal-first and lands them. Mirrors rubric Q5–Q6.

pre() {
  file-exists setup-progress.md
  file-exists context/tooling/board.md
  file-exists context/team/mission.md
}

post() {
  file-exists context/team/conventions/REQUIRED/issue-titles.md
  file-exists context/team/conventions/REQUIRED/labels.md
  file-exists context/team/conventions/REQUIRED/branches.md
  file-exists context/team/conventions/REQUIRED/output-discipline.md
  file-exists proposals/setup/step-3/issue-titles.md
  file-exists proposals/setup/step-3/labels.md
  file-exists proposals/setup/step-3/branches.md
  file-exists proposals/setup/step-3/output-discipline.md
}
