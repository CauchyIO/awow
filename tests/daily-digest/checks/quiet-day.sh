# Checks — quiet-day. One comment-only item; the digest must stay small and
# honest. Mechanical facts only; the no-padding judgement is the rubric's.

pre() {
  local d; d=$(date +%F)
  file-exists "activity/$d.json"
  file-contains "activity/$d.json" 'AWOW-201'
  file-exists context/team/members.md
  dir-absent digests
}

post() {
  local d; d=$(date +%F)
  file-exists "digests/$d.md"
  file-contains "digests/$d.md" 'AWOW-201'
  # No HTML, ever — the command forbids rendering it (Behavioral boundaries).
  file-absent "digests/$d.html"
  file-contains "digests/$d.md" 'tags:'
}
