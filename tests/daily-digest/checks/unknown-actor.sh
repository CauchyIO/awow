# Checks — unknown-actor. Zursk Vantell is not in members.md: their work may
# appear in the narrative, but no personalized-takeaways section may exist for
# them. Mirrors rubric Q5–Q6.

pre() {
  local d; d=$(date +%F)
  file-exists "activity/$d.json"
  file-contains "activity/$d.json" 'Zursk Vantell'
  file-exists context/team/members.md
  file-not-contains context/team/members.md 'Zursk'
  dir-absent digests
}

post() {
  local d; d=$(date +%F)
  file-exists "digests/$d.md"
  file-contains "digests/$d.md" 'AWOW-401'
  file-not-contains "digests/$d.md" '#+ For Zursk'
  file-absent "digests/$d.html"
}
