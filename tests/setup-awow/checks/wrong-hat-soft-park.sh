# Checks — wrong-hat-soft-park. Mechanical facts: the fixture starts hat-mismatched
# at Step 2, and afterwards the mission landed provisional with the hand-off and
# pending entry recorded. Conduct (never blocking) is the rubric's.

pre() {
  file-exists setup-progress.md
  file-contains setup-progress.md 'hat: engineering'
  file-absent context/team/mission.md
}

post() {
  file-exists context/team/mission.md
  file-contains context/team/mission.md 'provisional'
  file-contains setup-progress.md 'needs product'
}
