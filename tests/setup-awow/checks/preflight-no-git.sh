# Checks — preflight-no-git. Containerised no-git environment; the wizard must
# stop at preflight check 1 and change nothing. Mirrors rubric Q6–Q7.
# (The scratch IS a git repo — the runner's default git init applies — but the
# container cannot see that: P1 fires before P2 is ever probed.)

pre() {
  file-absent setup-progress.md
  dir-absent proposals
}

post() {
  file-absent setup-progress.md
  dir-absent proposals
}
