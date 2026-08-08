# tests/harness/lib/fixture.sh — sourced. Builds scratch fixtures under $TMPDIR.
_fx_root() { printf '%s' "${AWOW_REPO_ROOT:-$(git -C "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" rev-parse --show-toplevel)}"; }

make_template_fixture() {  # <dir>
  local dir="$1" root; root="$(_fx_root)"; mkdir -p "$dir" || return 1
  local d; for d in .agents tools setup context .claude-plugin commands hooks; do
    [ -e "$root/$d" ] && cp -R "$root/$d" "$dir/" 2>/dev/null
  done
  # Mirror .agents/ into the harness surfaces; --surface both keeps it lean (no dist/ build).
  ( cd "$dir" && python3 tools/gather.py --surface both >/dev/null 2>&1 ) || return 1
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
