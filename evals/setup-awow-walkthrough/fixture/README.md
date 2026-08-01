# Fixture: seed-stub context tree

This fixture is the workspace the session is staged into: a repo where awow is
installed but `/setup-awow` has not been run — the `context/` tree is in seed-stub
state. Stub-handling is a deliberate discriminator: strong models qualify their
output against stubs; weak models treat stubs as settled facts and invent the rest.

Minimal stub set for the walkthrough scenario. The canonical, fully-populated
Fikkert & Zn. fixture (populated variant, board seed, material) lands in Phase 2
at `tests/fixtures/fikkert/` and this fixture will then compose from it.
