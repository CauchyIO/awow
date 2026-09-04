# Checks — stale-sidecar. The stale header must be gone, the real hash present.
# The hash is the frozen notes.docx's — see fixtures/make-office-fixtures.sh.

pre() {
  file-exists notes/notes.docx
  file-exists notes/notes.docx.md
  file-contains notes/notes.docx.md "^source_sha256: 0{64}$"
  file-contains notes/notes.docx.md "^STALE$"
}

post() {
  file-contains notes/notes.docx.md "^source_sha256: 48c559e09baab46a3472a41c7b6dc44938ae9e56693696e2e0a9fa2003c92ca4$"
  file-not-contains notes/notes.docx.md "0{64}"
  file-not-contains notes/notes.docx.md "^STALE$"
  file-not-contains notes/notes.docx.md "^converted: 2026-01-01$"
  file-contains notes/notes.docx.md "^converted: [0-9]{4}-[0-9]{2}-[0-9]{2}$"
  file-contains notes/notes.docx.md "Priya"
  file-contains notes/notes.docx.md "Dana"
}
