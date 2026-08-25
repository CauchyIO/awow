#!/usr/bin/env bash
# Build a real post-lockfile vendored adopter: the v0.9.2 starter surface from
# this repo's history, the lockfile re-seeded at the pristine vendor state by
# the scratch's own engine, then two committed team edits.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VENDOR_TAG=v0.9.2

rm -f "$SCRATCH/.fixture"
git -C "$REPO_ROOT" archive "$VENDOR_TAG" \
  .agents tools setup context mcps pyproject.toml SETUP.md REFERENCES.md \
  .claude .github .opencode .gitignore AGENTS.md setup-progress.md \
  | tar -x -C "$SCRATCH"

cd "$SCRATCH"
git init -q
git config user.email eval@fixture.local
git config user.name "awow eval fixture"
git add -A
git commit -qm "vendor awow v0.9.2"

# The archived lock is the maintainer repo's own baseline, not this adopter's.
# Re-seed at the pristine vendor state with the vendored engine — exactly what
# install.sh did — so team edits below classify as edited against it.
rm tools/awow.lock.json
python3 tools/awow_lock.py backfill
git add -A
git commit -qm "seed awow lockfile"

cat >> .agents/commands/_workitem-archetypes/feature.md <<'EDIT'

## Team rule (local)

Every feature story links its KB entry before review.
EDIT
printf '\nTeam note: digests are posted to the #eng-daily channel.\n' >> .agents/commands/daily-digest.md
git add -A
git commit -qm "team edits to archetype and digest command"

mkdir -p .awow-payload
cp -R "$REPO_ROOT/dist/." .awow-payload/
