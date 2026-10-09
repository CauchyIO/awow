# Checks — anchored-repo. The project gains no context tree, the link and the anchor are
# untouched, nothing is drafted. Mirrors Q5.

pre() {
  file-contains AGENTS.md 'anchor: https://github\.com/example-team/anchor\.git'
  file-contains AGENTS.md 'FIXTURE-MARKER'
  file-contains .awow/anchor.json 'anchor-checkout'
  file-contains .awow/profile.json '"sample": "sam"'
  file-exists anchor-checkout/context/tooling/board.md
  file-contains anchor-checkout/context/tooling/board.md 'EX-202'
  dir-absent context
  dir-absent proposals
}

post() {
  file-contains AGENTS.md 'FIXTURE-MARKER'
  file-contains .awow/anchor.json 'anchor-checkout'
  file-contains anchor-checkout/context/tooling/board.md '\| EX-202 \| Add invoice PDF export \| in-progress \| sam \| EX-205 \|'
  file-contains anchor-checkout/context/team/mission.md 'Keep billing boring'
  dir-absent context
  dir-absent proposals
  file-absent setup-progress.md
}
