# Checks — preflight-not-a-repo. Non-repo scratch; the wizard must stop at
# preflight and change nothing. Mirrors rubric Q7–Q8.

pre() {
  dir-absent .git
  file-absent setup-progress.md
}

post() {
  dir-absent .git
  file-absent setup-progress.md
  dir-absent proposals
}
