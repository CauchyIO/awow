# Checks — connect-repo. Committed pointer + local link land; no board spec, no
# profile, no roster, no progress file in the child; the anchor's record exists
# on one of its two allowed sides. Mirrors rubric Q9–Q12.

pre() {
  file-absent AGENTS.md
  dir-absent .awow
  file-exists anchor-checkout/context/tooling/board.md
  file-absent setup-progress.md
}

post() {
  file-contains AGENTS.md 'anchor: https://github\.com/example-team/anchor\.git'
  file-contains AGENTS.md 'awow: anchored'
  file-contains .awow/anchor.json 'https://github\.com/example-team/anchor\.git'
  file-contains .gitignore '\.awow/'
  file-absent context/tooling/board.md
  file-absent context/team/mission.md
  file-absent context/team/members.md
  file-absent setup-progress.md
  if ls anchor-checkout/context/knowledge-sources/*.md >/dev/null 2>&1 || ls proposals/*anchor* >/dev/null 2>&1; then
    _record pass "anchor record exists (checkout or proposals/)"
  else
    _record fail "anchor record exists (checkout or proposals/)"
  fi
}
