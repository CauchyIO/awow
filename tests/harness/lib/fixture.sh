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
  local dir="$1" hub="$1.hub"
  mkdir -p "$dir/context" "$hub/context/tooling" || return 1
  cat > "$dir/AGENTS.md" <<EOF
---
hub: $hub
project: fixture
---
This repo follows awow; hub is named above.
EOF
  printf 'fixture project\n' > "$dir/context/mission.md"
  printf 'team: fixture\nproject: fixture\n' > "$dir/context/board-scope.md"
  printf 'board: none (fixture)\n' > "$hub/context/tooling/board.md"
  ( cd "$dir" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm spoke ) || return 1
  ( cd "$hub" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm hub ) || return 1
  printf '%s' "$dir"
}
