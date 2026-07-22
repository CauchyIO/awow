# Checks — no-board. The board pointer is absent and the workspace has no git
# remote: the run must ask once, record the answer, and still produce a digest.
# Mirrors rubric Q1-Q4.

pre() {
  local d; d=$(date +%F)
  file-exists "activity/$d.json"
  file-contains "activity/$d.json" 'AWOW-201'
  file-exists context/team/members.md
  file-absent context/tooling/board.md
  dir-absent digests
}

post() {
  local d; d=$(date +%F)
  file-exists "digests/$d.md"
  file-contains "digests/$d.md" 'AWOW-201'
  file-contains "digests/$d.md" 'tags:'
  file-exists .awow/board-session.md
  file-contains .awow/board-session.md 'GitHub Issues'
  # Still never HTML, and the board pointer was not invented on the user's behalf.
  file-absent "digests/$d.html"
  file-absent context/tooling/board.md
}
