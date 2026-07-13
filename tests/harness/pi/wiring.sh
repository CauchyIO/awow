# tests/harness/pi/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"
  # Pi discovers root AGENTS.md/CLAUDE.md by default (spec §7); same keystone as Codex.
  if [ -f "$r/AGENTS.md" ]; then
    file-contains "$r/AGENTS.md" '\.agents/AGENTS\.md'
  else
    skip "root AGENTS.md absent (pi-codex keystone not on this branch yet)"
  fi
  if [ -f "$r/.pi/extensions/awow.ts" ]; then
    file-contains "$r/.pi/extensions/awow.ts" 'skillPaths'
  else
    skip ".pi/extensions/awow.ts absent (hub-spoke WI-5 not landed)"
  fi
}
