#!/usr/bin/env bash
# Repo boundary as in the other scenarios, plus the invoker profile — written
# after the commit so it stays untracked, exactly as .awow/ state is in real life.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git init -q
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
mkdir -p .awow
cat > .awow/profile.json <<'EOF'
{"board_identity": {"sample": "sam"}, "hats": ["engineering"], "default_board": "product", "confirmed": "2026-08-18"}
EOF
