"""Regression test for the dist/<harness>/<plugin>/ layout (CAU-1653).

One folder per harness, one self-contained plugin per folder. Asserts, in order
of how badly each would fail silently:

  1. Every marketplace and root manifest resolves to a plugin folder that
     exists and carries that harness's manifest. Two marketplaces live at the
     REPO root — .claude-plugin/ (Claude Code) and .github/plugin/ (Copilot
     CLI, which checks that location first) — so each harness reaches its own
     folder; two manifests live at the dist/ root because Pi, opencode and
     Codex read them at the root of the repo they install.
  2. No harness folder carries another harness's surface. A Claude plugin with
     agent-skills/ inside it, or a Codex one with hooks/, is the single shared
     tree creeping back.
  3. context/ and handlers/ are byte-identical in every base-plugin folder,
     and so are the base plugin's tools. agent-skills/ is identical between the
     two COMBINED packages (Pi, opencode), and everything Codex ships — base
     plugin and bundle — is in them byte-for-byte: a combined package is the
     union, never a fork. The copies are what make each folder self-contained;
     drift between them is one harness silently running different machinery.
  4. Nothing is left at the old locations — dist/commands/, dist-telemetry/, …
     A stale tree there is still published by tools/sync-dist.sh.
  5. Every plugin folder is a registered generated root, so its orphans are swept.

Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-layout/test_layout.py
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

FAILURES: list[str] = []
DIST = gather.DIST_DIR

# harness folder -> the manifest that makes it installable there.
HARNESS_MANIFEST = {
    gather.CLAUDE_DIR: ".claude-plugin/plugin.json",
    gather.DIST_TELEMETRY_DIR: ".claude-plugin/plugin.json",
    gather.DIST_WORKFLOWS_DIR: ".claude-plugin/plugin.json",
    gather.CODEX_DIR: ".codex-plugin/plugin.json",
    gather.CODEX_WORKFLOWS_DIR: ".codex-plugin/plugin.json",
    gather.COPILOT_DIR: ".github/plugin/plugin.json",
    gather.COPILOT_WORKFLOWS_DIR: ".github/plugin/plugin.json",
    gather.OPENCODE_DIR: ".opencode/plugins/awow.js",
}

# Top-level entries a base-plugin folder may hold, per harness. `runtime` is
# shared; everything else is that harness's own surface.
RUNTIME = {"tools", "context", "handlers"}
ALLOWED = {
    gather.CLAUDE_DIR: RUNTIME | {".claude-plugin", "commands", "skills", "hooks", "README.md"},
    gather.CODEX_DIR: RUNTIME | {".codex-plugin", "agent-skills"},
    gather.PI_DIR: RUNTIME | {"agent-skills"},
    gather.OPENCODE_DIR: RUNTIME | {".opencode", "agent-skills"},
    gather.COPILOT_DIR: RUNTIME | {".github"},
}


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def files_under(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        return {}
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def check_entry_points() -> None:
    for folder, manifest in HARNESS_MANIFEST.items():
        if not (folder / manifest).is_file():
            FAILURES.append(f"{rel(folder)}/ has no {manifest} — not installable on its harness")

    # Repo-root marketplaces: relative sources resolve against the repo root.
    for mk_rel, want in (
        (".claude-plugin/marketplace.json", {"awow": gather.CLAUDE_DIR, "awow-telemetry": gather.DIST_TELEMETRY_DIR}),
        (".github/plugin/marketplace.json", {"awow": gather.COPILOT_DIR}),
    ):
        entries = {p["name"]: p.get("source") for p in json.loads((REPO_ROOT / mk_rel).read_text())["plugins"]}
        for name, folder in want.items():
            expected = "./" + rel(folder)
            if entries.get(name) != expected:
                FAILURES.append(f"{mk_rel}: {name} source == {entries.get(name)!r}, expected {expected!r}")
        for name, source in entries.items():
            if not isinstance(source, str) or not (REPO_ROOT / source).is_dir():
                FAILURES.append(f"{mk_rel}: {name} source {source!r} is not a folder in this repo")

    # dist/-root manifests: paths resolve against dist/, the published repo root.
    pkg = json.loads(gather.PI_MANIFEST.read_text())
    declared = [pkg.get("main", "")] + list(pkg.get("pi", {}).get("skills", []))
    for path in declared:
        if not path.startswith("./") or not (DIST / path).exists():
            FAILURES.append(f"dist/package.json declares {path!r}, which does not resolve under dist/")
    if not (DIST / pkg.get("main", "")).is_relative_to(gather.OPENCODE_DIR):
        FAILURES.append("dist/package.json `main` does not point into dist/opencode/awow/")
    if not any((DIST / s).is_relative_to(gather.PI_DIR) for s in pkg.get("pi", {}).get("skills", [])):
        FAILURES.append("dist/package.json `pi.skills` does not point into dist/pi/awow/")

    source = json.loads(gather.CODEX_MARKETPLACE.read_text())["plugins"][0]["source"]
    if source.get("source") != "local" or not str(source.get("path", "")).startswith("./"):
        FAILURES.append(f"Codex marketplace source is {source!r}; expected a `local` source with a ./ path")
    elif (DIST / source["path"]).resolve() != gather.CODEX_DIR.resolve():
        FAILURES.append(f"Codex marketplace path {source['path']!r} is not dist/codex/awow/")


def check_no_foreign_surface() -> None:
    for folder, allowed in ALLOWED.items():
        if not folder.is_dir():
            FAILURES.append(f"{rel(folder)}/ is missing")
            continue
        extra = {p.name for p in folder.iterdir()} - allowed
        if extra:
            FAILURES.append(
                f"{rel(folder)}/ holds {sorted(extra)} — another harness's surface, or an "
                "unplanned entry; a harness folder carries only what that harness uses"
            )


def check_copies_identical() -> None:
    base = list(ALLOWED)
    for part in ("context", "handlers"):
        reference = files_under(base[0] / part)
        if not reference:
            FAILURES.append(f"{rel(base[0])}/{part}/ is empty")
        for folder in base[1:]:
            if files_under(folder / part) != reference:
                FAILURES.append(f"{part}/ differs between {rel(base[0])}/ and {rel(folder)}/")
    # tools/: every folder carries the base plugin's tools, identically. A
    # combined package may carry the bundle's tools on top.
    reference = files_under(base[0] / "tools")
    for folder in base[1:]:
        have = files_under(folder / "tools")
        for name, data in reference.items():
            if have.get(name) != data:
                FAILURES.append(f"tools/{name} differs between {rel(base[0])}/ and {rel(folder)}/")
        if folder not in (gather.PI_DIR, gather.OPENCODE_DIR) and set(have) != set(reference):
            FAILURES.append(f"{rel(folder)}/tools/ carries tools the base plugin does not")

    # Named literally — see the note in tests/workflows-split/: expectations
    # must not come from the constant under test.
    combined = [gather.PI_DIR, gather.OPENCODE_DIR]
    reference = files_under(combined[0] / "agent-skills")
    for folder in combined[1:]:
        if files_under(folder / "agent-skills") != reference:
            FAILURES.append(f"agent-skills/ differs between {rel(combined[0])}/ and {rel(folder)}/")
    # A combined package is the union of what Codex ships in two folders.
    for part_root in (gather.CODEX_DIR, gather.CODEX_WORKFLOWS_DIR):
        for name, data in files_under(part_root / "agent-skills").items():
            if reference.get(name) != data:
                FAILURES.append(
                    f"{rel(part_root)}/agent-skills/{name} is missing from, or differs in, the "
                    f"combined {rel(combined[0])}/ — Pi and opencode users would lose or fork it"
                )
    split = set(files_under(gather.CODEX_DIR / "agent-skills")) | set(files_under(gather.CODEX_WORKFLOWS_DIR / "agent-skills"))
    if set(reference) != split:
        FAILURES.append(f"the combined package carries skills Codex ships nowhere: {sorted(set(reference) - split)[:5]}")


def check_old_locations_gone() -> None:
    for old in ("dist-telemetry", "dist-workflows"):
        if (REPO_ROOT / old).exists():
            FAILURES.append(f"{old}/ still exists — it moved under dist/claude/")
    for old in ("commands", "skills", "agent-skills", "hooks", "tools", "context", "handlers",
                ".claude-plugin", ".codex-plugin", ".github", ".opencode", "m365/appPackage"):
        if (DIST / old).exists():
            FAILURES.append(f"dist/{old} still exists at the old location — sync-dist.sh would publish it")
    allowed_top = {"README.md", "package.json", ".agents", "claude", "codex", "copilot", "pi", "opencode", "m365"}
    extra = {p.name for p in DIST.iterdir()} - allowed_top
    if extra:
        FAILURES.append(f"dist/ root holds unexpected entries: {sorted(extra)}")


def check_generated_roots() -> None:
    for folder in list(HARNESS_MANIFEST) + [gather.PI_DIR]:  # Pi has no manifest of its own
        if folder not in gather.GENERATED_ROOTS:
            FAILURES.append(f"{rel(folder)}/ is not in GENERATED_ROOTS — its stale files would never be swept")
    if DIST not in gather.SURFACE_ROOTS["all"]:
        FAILURES.append("dist/ is not swept by --surface all, so a stale old-layout tree would survive a rebuild")


def main() -> int:
    check_entry_points()
    check_no_foreign_surface()
    check_copies_identical()
    check_old_locations_gone()
    check_generated_roots()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Payload layout OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
