#!/usr/bin/env bash
# The scratch ROOT deliberately gets no git init — it is the workspace above
# sibling repos. Each child becomes its own repo.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
for repo in repo-solo repo-mono; do
  ( cd "$repo" && git init -q && git add -A \
    && git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture" )
done
