# Checks — orientation-multi-board. Mechanical facts: orientation answers recorded
# in setup-progress.md. The index-form announcement and split-rule conduct are the
# rubric's.

pre() {
  file-exists setup-progress.md
  file-not-contains setup-progress.md 'track:'
}

post() {
  file-contains setup-progress.md 'track: team'
  file-contains setup-progress.md 'hat: product'
  file-contains setup-progress.md 'boards: product, infra'
}
