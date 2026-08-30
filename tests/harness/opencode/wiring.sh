# tests/harness/opencode/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"

  # opencode reads the repo-root AGENTS.md natively — the same keystone Codex and
  # Pi use. Nothing opencode-specific is needed for steering.
  file-contains "$r/AGENTS.md" '\.agents/AGENTS\.md'

  # No in-repo command stubs (AWO-257): opencode reaches awow's flows through
  # the plugin's commands-as-skills surface, the same way an adopter does. The
  # spoke registration flow must still be reachable from this harness.
  dir-absent "$r/.opencode/commands"
  file-contains "$r/dist/agent-skills/setup-awow/SKILL.md" 'Anchored track'

  # Payload half: the plugin module package.json `main` resolves to.
  local js="$r/dist/.opencode/plugins/awow.js"
  file-exists "$js"
  cmd-succeeds "plugin module is valid JS" -- node --check "$js"
  # opencode plugins cannot declare skills in a manifest — the config hook is the
  # only registration path, and the bootstrap is what makes a global install
  # non-dormant in a repo with no root AGENTS.md.
  file-contains "$js" 'config:'
  file-contains "$js" 'skills\.paths'
  file-contains "$js" 'experimental\.chat\.messages\.transform'
  file-contains "$js" 'using-awow'

  # The shared dist/ manifest serves Pi (pi.skills) and opencode (main) at once.
  local p="$r/dist/package.json"
  cmd-succeeds "dist package.json main points at the plugin module" -- python3 -c "
import json
m = json.load(open('$p')).get('main')
raise SystemExit(0 if m == './.opencode/plugins/awow.js' else 1)"
  # ESM: the module uses import; without type=module opencode's loader rejects it.
  cmd-succeeds "dist package.json declares type=module" -- python3 -c "
import json
raise SystemExit(0 if json.load(open('$p')).get('type') == 'module' else 1)"
  # Adding opencode must not have displaced Pi from the same manifest.
  cmd-succeeds "pi.skills still registers ./agent-skills" -- python3 -c "
import json
skills = json.load(open('$p')).get('pi', {}).get('skills', [])
raise SystemExit(0 if './agent-skills' in skills else 1)"

  # The directory the config hook registers has to exist in the payload.
  file-exists "$r/dist/agent-skills/using-awow/SKILL.md"

  # Emitting .opencode/skills/ would be a second copy of every skill: opencode
  # already discovers .agents/skills/ natively, and the plugin registers the rest.
  dir-absent "$r/.opencode/skills"
}
