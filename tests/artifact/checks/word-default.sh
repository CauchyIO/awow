# Checks — word-default. Mechanical facts: fixture intact before; docx from
# markdown, board moved, no HTML after. Gate conduct is the rubric's.

pre() {
  file-exists brief.md
  file-exists diagram.png
  file-exists context/tooling/board.md
  file-contains context/tooling/design-system.md "^mode: absent"
  file-absent out/brief.docx
}

post() {
  file-exists out/brief.docx
  zip-member-contains out/brief.docx word/document.xml "Q3 stakeholder one-pager"
  zip-member-contains out/brief.docx word/document.xml "Acceptance criteria"
  zip-member-contains out/brief.docx word/document.xml "w:tbl"
  zip-member-contains out/brief.docx word/document.xml "a:blip"
  file-absent out/brief.html
  file-contains context/tooling/board.md "AR-1 .* In Review"
}
