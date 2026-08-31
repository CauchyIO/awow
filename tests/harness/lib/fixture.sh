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

_make_connector_fixture() {  # <dir> <awow-value> <connector-key> <link-name> ; echoes <dir>
  # The shipped connector shape (AWO-133): committed files carry the anchor's
  # IDENTITY (remote URL), never a path; the machine-local clone path lives in
  # the gitignored .awow/ link file, and the anchor clone's origin must match.
  local dir="$1" awow="$2" key="$3" link_name="$4"
  local anchor="$1.anchor" remote="https://github.com/example/fixture-anchor"
  mkdir -p "$dir/context" "$anchor/context/tooling" || return 1
  cat > "$dir/AGENTS.md" <<EOF
---
awow: $awow
$key: $remote
project: fixture
---
This repo follows awow; its anchor is named by remote identity above.
EOF
  printf 'fixture project\n' > "$dir/context/mission.md"
  printf 'team: fixture\nproject: fixture\n' > "$dir/context/board-scope.md"
  printf '.awow/\n' > "$dir/.gitignore"
  printf 'board: none (fixture)\n' > "$anchor/context/tooling/board.md"
  ( cd "$dir" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -qm anchored ) || return 1
  ( cd "$anchor" && git init -q && git remote add origin "$remote" \
      && git add -A && git -c user.email=t@t -c user.name=t commit -qm anchor ) || return 1
  mkdir -p "$dir/.awow" || return 1
  printf '{"remote": "%s", "path": "%s"}\n' "$remote" "$anchor" > "$dir/.awow/$link_name"
  printf '%s' "$dir"
}

make_anchored_fixture() {  # <dir> ; echoes <dir>
  _make_connector_fixture "$1" anchored anchor anchor.json
}

make_legacy_spoke_fixture() {  # <dir> ; echoes <dir>
  # The pre-rename spoke forms — what an adopter registered before the anchor
  # rename still carries. The machinery dual-accepts them silently; this
  # builder is the harness-level legacy regression (CAU-1415).
  _make_connector_fixture "$1" spoke hub hub.json
}
