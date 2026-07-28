# Checks — clean-clone. Empty workspace; script declines the installer, so
# nothing may be created. Mirrors rubric Q7–Q8 (belt-and-braces).

pre() {
  file-absent setup-progress.md
  dir-absent .venv
}

post() {
  file-absent setup-progress.md
  dir-absent .venv
}
