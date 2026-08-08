# tests/harness/opencode/wiring.sh
wiring() {
  local r="$HARNESS_REPO_ROOT"

  # opencode reads the repo-root AGENTS.md natively — the same keystone Codex and
  # Pi use. Nothing opencode-specific is needed for steering.
  file-contains "$r/AGENTS.md" '\.agents/AGENTS\.md'

  # The in-repo command surface. opencode does NOT read .claude/commands/, so this
  # directory is the only way awow's flows become slash commands.
  file-exists "$r/.opencode/commands/setup-awow.md"
  file-exists "$r/.opencode/commands/process-workitem.md"

  # The spoke registration flow must be reachable from this harness. The
  # .opencode command is a pointer stub, so assert both ends of the chain:
  # the stub points at the source, and the source carries the flow.
  file-contains "$r/.opencode/commands/setup-awow.md" '\.agents/commands/setup-awow\.md'
  file-contains "$r/.agents/commands/setup-awow.md" 'Spoke track'

  # The load-bearing one. opencode builds a command's placeholder list from the
  # template body; a stub without a literal $ARGUMENTS silently receives no
  # arguments at all. This fails invisibly at runtime, so it is asserted per file
  # rather than on a sample.
  cmd-succeeds "every .opencode command carries \$ARGUMENTS" -- python3 -c "
import pathlib, sys
bad = [p.name for p in pathlib.Path('$r/.opencode/commands').glob('*.md')
       if '\$ARGUMENTS' not in p.read_text()]
sys.exit(1 if bad else 0)"

  # description is the only frontmatter key worth setting; template must never
  # appear (for a markdown command the body IS the template, and a frontmatter
  # template key conflicts with it).
  cmd-succeeds "every .opencode command declares a description" -- python3 -c "
import pathlib, sys
bad = [p.name for p in pathlib.Path('$r/.opencode/commands').glob('*.md')
       if not p.read_text().startswith('---\ndescription:')]
sys.exit(1 if bad else 0)"
  file-not-contains "$r/.opencode/commands/setup-awow.md" '^template:'

  # A README in a commands dir becomes a bogus /README command in every harness.
  # The Claude and Copilot surfaces still carry that leak; do not spread it here.
  file-absent "$r/.opencode/commands/README.md"

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

  # Emitting .opencode/skills/ would be a third in-repo copy of every skill.
  # opencode already discovers .agents/skills/ and .claude/skills/ natively.
  dir-absent "$r/.opencode/skills"
}
