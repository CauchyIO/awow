# Checks — stale-sidecar. The stale header must be gone, the real hash present.
# The hash is the frozen notes.docx's — see fixtures/make-office-fixtures.sh.

pre() {
  file-exists notes/notes.docx
  file-exists notes/notes.docx.md
  file-contains notes/notes.docx.md "^source_sha256: 0{64}$"
  file-contains notes/notes.docx.md "^STALE$"
}

post() {
  file-contains notes/notes.docx.md "^source_sha256: 72bf72fdd203bb3afe0860d35b763285c97bace7c136a6d70dafa889e1de64af$"
  file-not-contains notes/notes.docx.md "0{64}"
  file-not-contains notes/notes.docx.md "^STALE$"
  file-contains notes/notes.docx.md "Priya"
}
