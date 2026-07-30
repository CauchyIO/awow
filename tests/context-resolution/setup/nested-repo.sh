#!/usr/bin/env bash
# vendor-tool/ must become a real git repo BEFORE the outer commit: only then
# does the outer `git add -A` record it as a 160000 gitlink (a submodule-style
# boundary marker) instead of tracking vendor-tool/README.md as an ordinary
# 100644 blob. Order matters — an outer-owned blob would falsely signal to an
# agent inspecting `git ls-files`/`git status` from the outer root that
# vendor-tool's content belongs to the outer repo, defeating the boundary
# this scenario tests.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH/vendor-tool"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "vendored fixture"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
