# tests/harness/pi/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"

  # Pi discovers root AGENTS.md/CLAUDE.md natively (spec §7) — same keystone as Codex.
  file-contains "$r/AGENTS.md" '\.agents/AGENTS\.md'

  # Pi package manifest — the whole integration is package.json pi.skills. WI-5 S3
  # dropped the .ts extension: Pi discovers .agents/skills + AGENTS.md natively, so
  # the package (pointing pi.skills at the commands-as-skills surface) is all it needs.
  local p="$r/dist/package.json"
  cmd-succeeds "pi package.json is valid JSON" -- python3 -c "import json; json.load(open('$p'))"
  cmd-succeeds "pi.skills registers ./agent-skills" -- python3 -c "
import json
skills = json.load(open('$p')).get('pi', {}).get('skills', [])
raise SystemExit(0 if './agent-skills' in skills else 1)"

  # The commands-as-skills surface pi.skills points at.
  file-exists "$r/dist/agent-skills/setup-awow/SKILL.md"

  # No .pi extension ships — package-only is the WI-5 decision. Guard against a
  # regression that re-introduces the dropped .ts extension.
  dir-absent "$r/.pi"
  file-absent "$r/dist/.pi"

  # Version lockstep: the pi package cannot ship a stale version.
  cmd-succeeds "pi package version == canonical plugin version" -- python3 -c "
import json
a = json.load(open('$r/.claude-plugin/plugin.json'))['version']
b = json.load(open('$p'))['version']
raise SystemExit(0 if a == b else 1)"
}
