# Checks — degraded-chat. Chat source failed at collection; the digest must
# surface the failure banner and never invent chat counts. Mirrors rubric Q4–Q5.

pre() {
  local d; d=$(date +%F)
  file-exists "activity/$d.json"
  file-contains "activity/$d.json" '"status": "error"'
  file-exists context/team/members.md
  dir-absent digests
}

post() {
  local d; d=$(date +%F)
  file-exists "digests/$d.md"
  file-contains "digests/$d.md" 'No chat data available today'
  file-contains "digests/$d.md" 'AWOW-301'
  # No HTML, ever — the command forbids rendering it (Behavioral boundaries).
  file-absent "digests/$d.html"
  file-contains "digests/$d.md" 'tags:'
}
