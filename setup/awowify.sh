#!/usr/bin/env bash
#
# awowify.sh — vendor the awow starter tree into an existing repository.
#
# awow normally ships via "Use this template", which only works for a brand-new
# repo. This is the other door: it copies awow's starter-owned files into a repo
# that already has code, without overwriting anything that is already there.
#
# Two callers:
#   /awowify plugin command (Claude Code) — passes the plugin clone as source:
#       awowify.sh --source "$CLAUDE_PLUGIN_ROOT" --target "$PWD" --solo --board linear
#   Copilot / no-plugin users (clone awow first, then point at your repo):
#       awowify.sh --target /path/to/your/repo        # --source defaults to this clone
#
# Tailoring (copy only what the team will use):
#   --board <linear|jira|azure-devops|github-issues|all>
#       Copy references for one board tool only. Default: all.
#   --layer <team|department>
#       Install profile (default: team). Commands/skills tagged `layer:
#       team` or `layer: department` in frontmatter ship only in the
#       matching profile; untagged files ship in both.
#   --solo
#       Skip team-coordination files (neighbouring teams, members roster, the
#       team-digest / cross-team / coaching / transcript commands).
#   awow-maintainer tooling (the regression suite, reset/distribute scripts,
#   awowify.sh itself) is never copied — adopters never run it.
#
# Non-destructive contract: an existing target file is never overwritten. The
# awow version is written next to it as <file>.awow and reported; your file is
# left untouched. README.md is never copied. .gitignore gets an appended,
# clearly-marked awow block (additive only).
#
# This script only moves files. Wiring Python (uv) and generating the harness
# stubs (tools/gather.py) is the caller's next step — run setup/install.sh.

set -euo pipefail

SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="$PWD"
DRY_RUN=0
BOARD="all"
LAYER="team"
SOLO=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="$(cd "$2" && pwd)"; shift 2 ;;
    --target) mkdir -p "$2"; TARGET="$(cd "$2" && pwd)"; shift 2 ;;
    --board)  BOARD="$2"; shift 2 ;;
    --layer)  LAYER="$2"; shift 2 ;;
    --solo)   SOLO=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,37p' "$0"; exit 0 ;;
    *) echo "awowify.sh: unknown argument: $1" >&2; exit 2 ;;
  esac
done

case "$BOARD" in
  linear|jira|azure-devops|github-issues|all) ;;
  *) echo "awowify.sh: --board must be one of linear, jira, azure-devops, github-issues, all (got '$BOARD')." >&2; exit 2 ;;
esac

case "$LAYER" in
  team|department) ;;
  *) echo "awowify.sh: --layer must be one of team, department (got '$LAYER')." >&2; exit 2 ;;
esac

if [[ "$SOURCE" == "$TARGET" ]]; then
  echo "awowify.sh: --source and --target are the same directory ($TARGET)." >&2
  echo "Run this from inside the repo you want to awowify, or pass --target." >&2
  exit 2
fi

# Starter-owned paths only (see the owner table in README.md). README.md,
# guides/, proposals/, input/, tests/, and the wizard's own state are intentionally
# left out: they are either the adopter's own, awow-internal, or generated.
STARTER_PATHS=(.agents tools setup context mcps pyproject.toml SETUP.md REFERENCES.md)

# Always excluded — awow-maintainer tooling adopters never run.
EXCLUDES=(
  setup/awowify.sh
  tools/distribute.py
  tools/reset-adopter-state.py
  tools/sync-dist.sh
  .agents/commands/awow-reset.md
)
# Solo mode also drops team-coordination context and commands.
if [[ "$SOLO" -eq 1 ]]; then
  EXCLUDES+=(
    context/company
    context/team/members.md
    .agents/commands/daily-digest.md
    .agents/commands/weekly-digest.md
    .agents/commands/coaching-review.md
    .agents/commands/process-transcript.md
  )
fi
# Board mode drops the reference dirs for every tool except the chosen one.
if [[ "$BOARD" != "all" ]]; then
  for tool in linear jira azure-devops github-issues; do
    [[ "$tool" != "$BOARD" ]] && EXCLUDES+=("context/tooling/boards/$tool")
  done
fi

# layer_of <file> — the frontmatter `layer:` value ("team" or "department"),
# or empty when the file carries none.
layer_of() {
  awk '
    /^---$/ { n++; if (n == 2) exit; next }
    n == 1 && /^layer:/ {
      sub(/^layer:[[:space:]]*"?/, ""); sub(/"?[[:space:]]*$/, ""); print; exit
    }
  ' "$1" 2>/dev/null
}

# layer_excluded <relpath> — true when relpath is tagged for the layer this
# install is not using. Only .agents/commands/*.md (direct children) and
# .agents/skills/* carry the tag; a directory skill's tag lives on its
# SKILL.md, not on every file inside it. Untagged files pass for both layers.
layer_excluded() {
  local rel="$1" tagfile="" sub rest
  case "$rel" in
    .agents/commands/*.md)
      sub="${rel#.agents/commands/}"
      [[ "$sub" == */* ]] && return 1   # nested (e.g. _workitem-archetypes/)
      tagfile="$SOURCE/$rel" ;;
    .agents/skills/*)
      rest="${rel#.agents/skills/}"
      if [[ "$rest" == */* ]]; then
        tagfile="$SOURCE/.agents/skills/${rest%%/*}/SKILL.md"
      else
        tagfile="$SOURCE/$rel"
      fi ;;
    *) return 1 ;;
  esac
  [[ -f "$tagfile" ]] || return 1
  local tag
  tag="$(layer_of "$tagfile")"
  if [[ -n "$tag" && "$tag" != "team" && "$tag" != "department" ]]; then
    echo "awowify.sh: ${tagfile#"$SOURCE"/} has unrecognized layer: '$tag' (must be team, department, or absent)." >&2
    exit 1
  fi
  [[ -z "$tag" || "$tag" == "$LAYER" ]] && return 1
  return 0
}

is_excluded() {
  local rel="$1" ex
  for ex in "${EXCLUDES[@]}"; do
    [[ "$rel" == "$ex" || "$rel" == "$ex"/* ]] && return 0
  done
  layer_excluded "$rel" && return 0
  return 1
}

copied=0
excluded=0
conflicts=()

vendor_file() {
  local src="$1" dst="$2"
  if [[ -e "$dst" ]]; then
    if cmp -s "$src" "$dst"; then
      return 0   # identical — already in place
    fi
    conflicts+=("${dst#"$TARGET"/}")
    [[ "$DRY_RUN" -eq 0 ]] && cp "$src" "$dst.awow"
    return 0
  fi
  if [[ "$DRY_RUN" -eq 0 ]]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
  fi
  copied=$((copied + 1))
}

for rel in "${STARTER_PATHS[@]}"; do
  src="$SOURCE/$rel"
  [[ -e "$src" ]] || continue
  if [[ -d "$src" ]]; then
    while IFS= read -r -d '' f; do
      relpath="${f#"$SOURCE"/}"
      if is_excluded "$relpath"; then excluded=$((excluded + 1)); continue; fi
      vendor_file "$f" "$TARGET/$relpath"
    done < <(find "$src" -type f -print0)
  else
    if is_excluded "$rel"; then excluded=$((excluded + 1)); continue; fi
    vendor_file "$src" "$TARGET/$rel"
  fi
done

# .gitignore — keep venv and generated-but-local artefacts out of git. Additive:
# append a marked block if one isn't already there; never rewrite the file.
GITIGNORE_MARKER="# >>> awow >>>"
read -r -d '' AWOW_IGNORES <<'EOF' || true
# >>> awow >>>
# Added by awowify.sh — keep venv and per-machine harness state out of git.
.venv/
__pycache__/
*.py[cod]
.claude/settings.local.json
.claude/mlflow/
mlruns/
tools/.awow-vendor-stamp
# <<< awow <<<
EOF

gi="$TARGET/.gitignore"
if [[ -f "$gi" ]]; then
  if grep -qF "$GITIGNORE_MARKER" "$gi"; then
    gitignore_action="already present"
  else
    gitignore_action="appended awow block"
    [[ "$DRY_RUN" -eq 0 ]] && printf '\n%s\n' "$AWOW_IGNORES" >> "$gi"
  fi
else
  gitignore_action="created"
  [[ "$DRY_RUN" -eq 0 ]] && printf '%s\n' "$AWOW_IGNORES" > "$gi"
fi

# Vendor stamp — awowify'd repos carry no plugin.json, so record the awow
# version, source commit, and mode here. tools/awow_lock.py backfill (run by
# setup/install.sh next) reads this to seed tools/awow.lock.json, then deletes
# it. Template adopters skip this: they read the version from their plugin.json.
if [[ "$DRY_RUN" -eq 0 ]]; then
  awow_version="$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$SOURCE/.claude-plugin/plugin.json" 2>/dev/null | head -1)"
  source_commit="$(git -C "$SOURCE" rev-parse --short HEAD 2>/dev/null || true)"
  mkdir -p "$TARGET/tools"
  {
    echo "# awow vendor stamp — consumed by tools/awow_lock.py backfill at install."
    echo "awow_version=${awow_version}"
    echo "source_commit=${source_commit}"
    echo "board=${BOARD}"
    echo "solo=${SOLO}"
  } > "$TARGET/tools/.awow-vendor-stamp"
fi

echo
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "awowify (dry run) — nothing was written. Re-run without --dry-run to apply."
else
  echo "awowify — starter tree vendored into $TARGET"
fi
echo "  mode:           board=$BOARD, $([[ "$SOLO" -eq 1 ]] && echo solo || echo team)"
echo "  files copied:   $copied"
echo "  files skipped:  $excluded (board/solo/maintainer trims)"
echo "  .gitignore:     $gitignore_action"
if [[ ${#conflicts[@]} -gt 0 ]]; then
  echo "  conflicts:      ${#conflicts[@]} (awow version saved as <file>.awow; your file untouched)"
  for c in "${conflicts[@]}"; do
    echo "    - $c"
  done
  echo
  echo "Merge each .awow into your file, then delete the .awow."
fi
echo
echo "Next — wire Python and generate the harness stubs so /setup-awow appears:"
echo "  $TARGET/setup/install.sh        # macOS / Linux"
echo "  $TARGET/setup/install.ps1       # Windows / PowerShell"
echo "then open an agent session in $TARGET and run /setup-awow."
