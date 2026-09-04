# Checks — docx-notes. Mechanical facts: fixture intact before; sidecar with
# provenance after. Reuse on the second turn is the rubric's (tool-call evidence).
# The hash is the frozen notes.docx's — see fixtures/make-office-fixtures.sh.

pre() {
  file-exists notes/notes.docx
  file-absent notes/notes.docx.md
  file-exists context/tooling/board.md
}

post() {
  file-exists notes/notes.docx.md
  file-contains notes/notes.docx.md "^source: notes.docx$"
  file-contains notes/notes.docx.md "^source_sha256: 48c559e09baab46a3472a41c7b6dc44938ae9e56693696e2e0a9fa2003c92ca4$"
  file-contains notes/notes.docx.md "^converted: [0-9]{4}-[0-9]{2}-[0-9]{2}$"
  file-contains notes/notes.docx.md "^converter: markitdown "
  file-contains notes/notes.docx.md "Priya"
  file-contains notes/notes.docx.md "Dana"
}
