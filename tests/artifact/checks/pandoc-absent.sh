# Checks — pandoc-absent. Nothing was delivered, so nothing may claim it was.

pre() {
  file-exists brief.md
  file-contains context/tooling/design-system.md "mode: absent"
  file-absent out/brief.docx
}

post() {
  file-absent out/brief.docx
  file-not-contains context/tooling/board.md "AR-1 .* In Review"
  file-not-contains context/tooling/board.md "AR-1 .* Done"
}
