# tests/harness/lib/fixture.sh — sourced. Builds scratch fixtures under $TMPDIR.
_fx_root() { printf '%s' "${AWOW_REPO_ROOT:-$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)}"; }

make_template_fixture() {  # <dir>
  local dir="$1" root; root="$(_fx_root)"; mkdir -p "$dir" || return 1
  local d; for d in .agents tools setup context .claude-plugin hooks; do
    [ -e "$root/$d" ] && cp -R "$root/$d" "$dir/" 2>/dev/null
  done
  # The root instruction files are hand-authored pointers to .agents/AGENTS.md
  # (AWO-257) — Codex and Pi read AGENTS.md natively, so the fixture needs them
  # and nothing generated: no gather run, no dist/ build.
  local f; for f in AGENTS.md .claude/CLAUDE.md .github/AGENTS.md .github/copilot-instructions.md; do
    mkdir -p "$dir/$(dirname "$f")" && cp "$root/$f" "$dir/$f" || return 1
  done
  ( cd "$dir" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm fixture ) || return 1
}

make_spoke_fixture() {  # <dir> ; echoes <dir>
  # The shipped connector shape (AWO-133): committed files carry the hub's
  # IDENTITY (remote URL), never a path; the machine-local clone path lives in
  # the gitignored .awow/hub.json, and the hub clone's origin must match.
  local dir="$1" hub="$1.hub" remote="https://github.com/example/fixture-hub"
  mkdir -p "$dir/context" "$hub/context/tooling" || return 1
  cat > "$dir/AGENTS.md" <<EOF
---
awow: spoke
hub: $remote
project: fixture
---
This repo follows awow; its hub is named by remote identity above.
EOF
  printf 'fixture project\n' > "$dir/context/mission.md"
  printf 'team: fixture\nproject: fixture\n' > "$dir/context/board-scope.md"
  printf '.awow/\n' > "$dir/.gitignore"
  printf 'board: none (fixture)\n' > "$hub/context/tooling/board.md"
  ( cd "$dir" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm spoke ) || return 1
  ( cd "$hub" && git init -q && git remote add origin "$remote" \
      && git add -A && git -c user.email=t@t -c user.name=t commit -qm hub ) || return 1
  mkdir -p "$dir/.awow" || return 1
  printf '{"remote": "%s", "path": "%s"}\n' "$remote" "$hub" > "$dir/.awow/hub.json"
  printf '%s' "$dir"
}
