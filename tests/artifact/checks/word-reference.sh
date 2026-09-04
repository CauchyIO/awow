# Checks — word-reference. The sentinel colour proves the reference doc was applied.

pre() {
  file-exists brief.md
  file-exists diagram.png
  file-exists context/design-system/templates/word/reference.docx
  file-contains context/tooling/design-system.md "^mode: in-repo"
  file-contains context/tooling/design-system.md "^word_reference: \"context/design-system/templates/word/reference.docx\""
  zip-member-contains context/design-system/templates/word/reference.docx word/styles.xml FF00AA
  file-absent out/brief.docx
}

post() {
  file-exists out/brief.docx
  zip-member-contains out/brief.docx word/styles.xml FF00AA
  zip-member-contains out/brief.docx word/document.xml "Acceptance criteria"
  zip-member-contains out/brief.docx word/document.xml "w:tbl"
  zip-member-contains out/brief.docx word/document.xml "a:blip"
  file-absent out/brief.html
  file-contains context/tooling/board.md "AR-1 .* In Review"
}
