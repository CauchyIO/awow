# Checks — install-step0-inherited. Fixture signals Step 0 inherited (.venv/
# + populated pointer stubs, no setup-progress.md). Mirrors rubric Q6–Q7.

pre() {
  dir-exists .venv
  file-exists .claude/commands/setup-awow.md
  file-exists .github/prompts/setup-awow.prompt.md
  file-absent setup-progress.md
}

post() {
  file-exists setup-progress.md
  file-contains setup-progress.md '\[x\].*Step 0'
  dir-exists .venv
}
