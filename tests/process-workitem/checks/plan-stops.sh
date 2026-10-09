# Checks — plan-stops. One plan file appears under proposals/; code and board are
# untouched. Mirrors Q3 and Q5.

pre() {
  file-exists context/tooling/board.md
  file-contains board/issues/T-102.md '^state: todo'
  file-not-contains src/checkout.py 'WELCOME10'
  dir-absent proposals
}

post() {
  file-exists proposals/T-102.md
  file-contains proposals/T-102.md '[Aa]rchetype'
  file-contains proposals/T-102.md 'src/checkout\.py'
  file-contains proposals/T-102.md 'tests/test_checkout\.py'
  file-contains proposals/T-102.md '[Vv]erification'
  file-not-contains src/checkout.py 'WELCOME10'
  file-not-contains tests/test_checkout.py 'WELCOME10'
  file-contains board/issues/T-102.md '^state: todo'
  file-not-contains board/issues/T-102.md '## Comments'
  dir-absent .git/refs/heads/feature
}
