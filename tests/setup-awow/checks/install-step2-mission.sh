# Checks — install-step2-mission. Step 2 lands the mission proposal-first.
# Mirrors rubric Q5–Q6.

pre() {
  file-exists setup-progress.md
  file-contains setup-progress.md '\[x\].*Step 1'
  file-exists context/tooling/board.md
}

post() {
  file-exists context/team/mission.md
  file-contains context/team/mission.md 'Cauchy helps engineering teams'
  file-exists proposals/setup/step-2/mission.md
}
