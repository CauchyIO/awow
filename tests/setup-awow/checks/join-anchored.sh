# Checks — join-anchored. Only the local link appears; the committed pointer
# and the absence of context/ survive. Mirrors rubric Q8–Q9.

pre() {
  file-contains AGENTS.md 'anchor: https://github\.com/example-team/anchor\.git'
  file-contains AGENTS.md 'FIXTURE-MARKER'
  dir-absent .awow
  dir-absent context
}

post() {
  file-contains .awow/anchor.json 'https://github\.com/example-team/anchor\.git'
  file-contains AGENTS.md 'FIXTURE-MARKER'
  file-contains AGENTS.md 'project: billing-service'
  dir-absent context
  dir-absent proposals
  file-absent setup-progress.md
}
