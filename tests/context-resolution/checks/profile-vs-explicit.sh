# Checks — profile-default. Read-only command; mechanical facts are fixture
# integrity plus the profile surviving. Ladder conduct is the rubric's.

pre() {
  file-exists context/tooling/board.md
  file-exists context/tooling/board-product.md
  file-exists .awow/profile.json
  file-contains .awow/profile.json '"default_board": "product"'
}

post() {
  file-exists .awow/profile.json
  file-contains .awow/profile.json '"default_board": "product"'
}
