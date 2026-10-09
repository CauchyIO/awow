#!/usr/bin/env bash
# anchored-repo: the scratch is an anchored project repo; anchor-checkout/ inside it stands
# in for the local clone of the anchor, with an origin matching the committed anchor: URL.
# The local link and the profile are written after the commit so they stay untracked, as
# .awow/ state is in real life. The link carries the absolute scratch path.
set -euo pipefail
SCRATCH="${1:?usage: setup script receives the scratch dir}"
cd "$SCRATCH"
git -C anchor-checkout init -q
git -C anchor-checkout remote add origin https://github.com/example-team/anchor.git
git -C anchor-checkout add -A
git -C anchor-checkout -c user.email=fixture@test -c user.name=fixture commit -qm "anchor fixture"
git init -q
printf '.awow/\nanchor-checkout/\n' > .gitignore
git add -A
git -c user.email=fixture@test -c user.name=fixture commit -qm "fixture"
mkdir -p .awow
printf '{"remote": "https://github.com/example-team/anchor.git", "path": "%s/anchor-checkout"}\n' "$SCRATCH" > .awow/anchor.json
cat > .awow/profile.json <<'EOF'
{"board_identity": {"sample": "sam"}, "confirmed": "2026-09-23"}
EOF
