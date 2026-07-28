#!/usr/bin/env bash
#
# sync-dist.sh
#
# Publish this awow checkout's built `dist/` payload → CauchyIO/awow-dist.
#
# `dist/` published as a git repo IS the Codex marketplace (the plugin sits at
# the repo root with source "./") and the Pi git-install source (package.json
# pi.skills). This script mirrors the committed `dist/` into a fresh clone of
# awow-dist, commits, pushes a sync branch, and opens a PR. It never pushes to
# the base branch directly — branch-protection-safe.
#
# Deterministic: running twice against the same awow SHA (with dist/ in sync)
# produces PRs with identical diffs, so two back-to-back runs verify the tool.
#
# Usage:
#   ./tools/sync-dist.sh                # dry-run preview (default; nothing pushed)
#   ./tools/sync-dist.sh --apply        # apply: push a sync branch + open a PR
#   ./tools/sync-dist.sh --apply -y     # apply, skip the confirm prompt
#   ./tools/sync-dist.sh --local PATH   # use an existing awow-dist checkout
#   ./tools/sync-dist.sh --base BRANCH  # dest base branch (default: main)
#   ./tools/sync-dist.sh --bootstrap    # first publish into an empty awow-dist
#
# Requires: bash, rsync, git, gh (authenticated), python3.

set -euo pipefail

# =============================================================================
# Config — edit as the canonical marketplace repo evolves
# =============================================================================

DEST_REPO_SLUG="CauchyIO/awow-dist"
DEFAULT_BASE="main"

# =============================================================================
# Args
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UPSTREAM="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST="$UPSTREAM/dist"
BASE="$DEFAULT_BASE"
APPLY=0
YES=0
LOCAL_CHECKOUT=""
BOOTSTRAP=0

usage() { sed -n '/^# Usage:/,/^# Requires:/s/^# \{0,1\}//p' "$0"; exit "${1:-0}"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)      APPLY=1; shift ;;
    -n|--dry-run) APPLY=0; shift ;;
    -y|--yes)     YES=1; shift ;;
    --local)      LOCAL_CHECKOUT="$2"; shift 2 ;;
    --base)       BASE="$2"; shift 2 ;;
    --bootstrap)  BOOTSTRAP=1; shift ;;
    -h|--help)    usage 0 ;;
    *)            echo "Unknown arg: $1" >&2; usage 2 ;;
  esac
done

# =============================================================================
# Preflight
# =============================================================================

die() { echo "ERROR: $*" >&2; exit 1; }

command -v rsync >/dev/null   || die "rsync not found in PATH"
command -v git >/dev/null     || die "git not found in PATH"
command -v gh >/dev/null      || die "gh not found — install GitHub CLI"
command -v python3 >/dev/null || die "python3 not found in PATH"
gh auth status >/dev/null 2>&1 || die "gh not authenticated — run 'gh auth login'"

git -C "$UPSTREAM" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "upstream '$UPSTREAM' is not a git checkout"
[[ -d "$DIST" ]]          || die "no dist/ payload at $DIST — run 'python3 tools/gather.py' first"
[[ -f "$DIST/.codex-plugin/plugin.json" ]] || die "dist/ is missing the Codex manifest — run gather"

# The published dist/ must not be stale relative to .agents/. --check fails loud
# if a source edit hasn't been re-gathered, so we never publish a stale payload.
python3 "$UPSTREAM/tools/gather.py" --check >/dev/null \
  || die "dist/ is out of sync with .agents/ — run 'python3 tools/gather.py' and commit before publishing"

VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$DIST/.codex-plugin/plugin.json")"
[[ -n "$VERSION" ]] || die "could not read 'version' from dist/.codex-plugin/plugin.json"

UPSTREAM_BRANCH="$(cd "$UPSTREAM" && git branch --show-current)"
UPSTREAM_SHA="$(cd "$UPSTREAM" && git rev-parse HEAD)"
UPSTREAM_SHORT="$(cd "$UPSTREAM" && git rev-parse --short HEAD)"

confirm() { [[ $YES -eq 1 ]] && return 0; read -rp "$1 [y/N] " ans; [[ "$ans" == "y" || "$ans" == "Y" ]]; }

if [[ -n "$(cd "$UPSTREAM" && git status --porcelain -- dist)" ]]; then
  echo "WARNING: dist/ has uncommitted changes — the publish will use working-tree state, not HEAD ($UPSTREAM_SHORT)."
  confirm "Continue anyway?" || exit 1
fi

# =============================================================================
# Prepare destination (clone fresh, or use --local)
# =============================================================================

CLEANUP_DIR=""
cleanup() { [[ -n "$CLEANUP_DIR" ]] && rm -rf "$CLEANUP_DIR"; }
trap cleanup EXIT

if [[ -n "$LOCAL_CHECKOUT" ]]; then
  DEST_REPO="$(cd "$LOCAL_CHECKOUT" && pwd)"
  git -C "$DEST_REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "--local path '$DEST_REPO' is not a git checkout"
else
  echo "Cloning $DEST_REPO_SLUG..."
  CLEANUP_DIR="$(mktemp -d)"
  DEST_REPO="$CLEANUP_DIR/awow-dist"
  gh repo clone "$DEST_REPO_SLUG" "$DEST_REPO" >/dev/null
fi

git -C "$DEST_REPO" checkout -q "$BASE" 2>/dev/null || {
  [[ $BOOTSTRAP -eq 1 ]] || die "base branch '$BASE' doesn't exist in $DEST_REPO_SLUG — use --bootstrap for an empty repo"
  git -C "$DEST_REPO" checkout -q --orphan "$BASE"
  git -C "$DEST_REPO" rm -rq --cached . 2>/dev/null || true
}

# =============================================================================
# rsync args — mirror dist/ over the dest root, but never touch dest .git.
# =============================================================================

RSYNC_ARGS=(-a --delete --exclude="/.git/" --exclude=".DS_Store")

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
SYNC_BRANCH="sync/awow-${VERSION}-${UPSTREAM_SHORT}-${TIMESTAMP}"
[[ $BOOTSTRAP -eq 1 ]] && SYNC_BRANCH="bootstrap/awow-${VERSION}-${UPSTREAM_SHORT}-${TIMESTAMP}"

echo ""
echo "Upstream: $UPSTREAM ($UPSTREAM_BRANCH @ $UPSTREAM_SHORT)"
echo "Version:  $VERSION"
echo "Dest:     $DEST_REPO_SLUG"
echo "Base:     $BASE"
echo "Branch:   $SYNC_BRANCH"
[[ $BOOTSTRAP -eq 1 ]] && echo "Mode:     BOOTSTRAP (first publish into an empty repo)"
echo ""
echo "=== Preview (rsync --dry-run) ==="
rsync "${RSYNC_ARGS[@]}" --dry-run --itemize-changes "$DIST/" "$DEST_REPO/"
echo "=== End preview ==="
echo ""

if [[ $APPLY -eq 0 ]]; then
  echo "Dry run only. Nothing was changed or pushed. Re-run with --apply to publish."
  exit 0
fi

# =============================================================================
# Apply — mirror, commit, push branch, open PR
# =============================================================================

confirm "Apply changes, push $SYNC_BRANCH, and open a PR against $BASE?" || { echo "Aborted."; exit 1; }

git -C "$DEST_REPO" checkout -q -b "$SYNC_BRANCH"
rsync "${RSYNC_ARGS[@]}" "$DIST/" "$DEST_REPO/"

if [[ -z "$(git -C "$DEST_REPO" status --porcelain)" ]]; then
  echo "No changes — $DEST_REPO_SLUG is already in sync with awow $UPSTREAM_SHORT (v$VERSION)."
  exit 0
fi

git -C "$DEST_REPO" add -A
COMMIT_TITLE="publish awow v$VERSION from $UPSTREAM_SHORT"
PR_BODY="Automated publish of the awow \`dist/\` payload from awow @ \`$UPSTREAM_SHORT\` (v$VERSION).

The published tree is the Codex marketplace (plugin at root, \`source: \"./\"\`) and the Pi git-install source (\`package.json\` \`pi.skills\`).

Run via: \`tools/sync-dist.sh --apply\`
awow commit: https://github.com/CauchyIO/awow/commit/$UPSTREAM_SHA

Re-running against the same awow SHA should produce an identical diff — use that to verify the tool."

git -C "$DEST_REPO" commit --quiet -m "$COMMIT_TITLE

Automated publish via tools/sync-dist.sh
awow: https://github.com/CauchyIO/awow/commit/$UPSTREAM_SHA
Branch: $SYNC_BRANCH"

echo "Pushing $SYNC_BRANCH to $DEST_REPO_SLUG..."
git -C "$DEST_REPO" push -u origin "$SYNC_BRANCH" --quiet

echo "Opening PR..."
PR_URL="$(gh pr create --repo "$DEST_REPO_SLUG" --base "$BASE" --head "$SYNC_BRANCH" \
  --title "$COMMIT_TITLE" --body "$PR_BODY")"
echo ""
echo "PR opened: $PR_URL"
