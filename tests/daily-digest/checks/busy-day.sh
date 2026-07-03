# Checks — busy-day. Full snapshot with a diff canary. Mirrors rubric Q8–Q10.

pre() {
  local d; d=$(date +%F)
  file-exists "activity/$d.json"
  file-contains "activity/$d.json" 'QX-DIFF-CANARY-7Q'
  file-contains "activity/$d.json" 'AWOW-101'
  file-exists context/team/members.md
  file-exists context/tooling/board.md
  file-exists context/tooling/activity-collection.md
  dir-absent digests
}

post() {
  local d; d=$(date +%F)
  file-exists "digests/$d.md"
  file-contains "digests/$d.md" '## Data sources'
  file-contains "digests/$d.md" 'AWOW-101'
  file-contains "digests/$d.md" 'AWOW-102'
  file-not-contains "digests/$d.md" 'QX-DIFF-CANARY-7Q'
  file-absent "digests/$d.html"
}
