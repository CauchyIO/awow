#!/usr/bin/env bash
# Build notes.docx once from office-notes.md, mirror the docx-notes fixture into
# stale-sidecar with a deliberately stale sidecar, and print the docx's SHA-256 —
# paste it into checks/docx-notes.sh and checks/stale-sidecar.sh.
#
# Needs pandoc; CI never runs it. notes.docx is FROZEN: its hash is a constant in
# both checks files, so this script refuses to overwrite an existing one. Pass
# --force to rebuild deliberately, then update both checks files with the hash
# printed below. The plaintext source stays here, outside every scenario fixture,
# so no scratch workspace ever ships a readable twin of the .docx under test.
set -euo pipefail
cd "$(dirname "$0")"

DOCX=docx-notes/notes/notes.docx
if [ -e "$DOCX" ] && [ "${1:-}" != "--force" ]; then
  echo "$DOCX exists and is frozen; pass --force to rebuild (then update both checks files)" >&2
  exit 1
fi

mkdir -p docx-notes/notes
# pandoc stamps dcterms:created and zip mtimes from the wall clock, so two builds
# seconds apart differ. Pinning SOURCE_DATE_EPOCH makes the rebuild byte-identical,
# which is what lets --force reproduce the frozen hash instead of inventing a new one.
export SOURCE_DATE_EPOCH=1788480000
pandoc office-notes.md --from gfm --to docx -o "$DOCX"

rm -rf stale-sidecar && mkdir -p stale-sidecar && cp -R docx-notes/. stale-sidecar/
cat > stale-sidecar/notes/notes.docx.md <<'MD'
---
source: notes.docx
source_sha256: 0000000000000000000000000000000000000000000000000000000000000000
converted: 2026-01-01
converter: markitdown 0.1.7
---
STALE
MD

python3 -c "import hashlib,sys;print('SHA256', hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$DOCX"
