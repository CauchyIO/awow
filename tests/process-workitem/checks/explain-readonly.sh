# Checks — explain-readonly. Explain changes nothing: the fixture is byte-for-byte as it
# was, and none of the places the deeper depths write to come into existence. Mirrors Q4.

pre() {
  file-exists context/tooling/board.md
  file-contains board/issues/T-102.md '^state: todo'
  file-contains src/checkout.py 'accepted but not applied yet'
  file-not-contains src/checkout.py 'WELCOME10'
  dir-absent proposals
  dir-absent .awow
}

post() {
  file-contains board/issues/T-102.md '^state: todo'
  file-not-contains board/issues/T-102.md '## Comments'
  file-contains board/issues/T-101.md '^state: done'
  file-contains src/checkout.py 'accepted but not applied yet'
  file-not-contains src/checkout.py 'WELCOME10'
  file-not-contains tests/test_checkout.py 'WELCOME10'
  dir-absent proposals
  file-absent .git/refs/heads/feature
}
