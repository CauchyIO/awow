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
#       awowify.sh --source "$CLAUDE_PLUGIN_ROOT" --target "$PWD"
#   Copilot / no-plugin users (clone awow first, then point at your repo):
#       awowify.sh --target /path/to/your/repo        # --source defaults to this clone
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

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="$(cd "$2" && pwd)"; shift 2 ;;
    --target) mkdir -p "$2"; TARGET="$(cd "$2" && pwd)"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "awowify.sh: unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ "$SOURCE" == "$TARGET" ]]; then
  echo "awowify.sh: --source and --target are the same directory ($TARGET)." >&2
  echo "Run this from inside the repo you want to awowify, or pass --target." >&2
  exit 2
fi

# Starter-owned paths only (see the owner table in README.md). README.md,
# guides/, meta/, input/, tests/, and the wizard's own state are intentionally
# left out: they are either the adopter's own, awow-internal, or generated.
STARTER_PATHS=(.agents tools setup context mcps pyproject.toml SETUP.md REFERENCES.md)

copied=0
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
      vendor_file "$f" "$TARGET/${f#"$SOURCE"/}"
    done < <(find "$src" -type f -print0)
  else
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

echo
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "awowify (dry run) — nothing was written. Re-run without --dry-run to apply."
else
  echo "awowify — starter tree vendored into $TARGET"
fi
echo "  files copied:   $copied"
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
