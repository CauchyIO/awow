"""Manifest integrity over the built payload.

`gather.py --check` proves dist/ matches what the generator would produce. That
is not the same as the payload being installable: a manifest can declare a path
the generator never plans, and the check stays green because the generator and
its output agree. That is exactly how the Copilot plugin came to declare
`.github/plugin/skills/` while shipping nothing there (AWO-155).

Two assertions over the real committed payload, which is the artifact
`tools/sync-dist.sh` publishes:

1. Every path a manifest declares resolves on disk.
2. Every manifest version equals the canonical `.claude-plugin/plugin.json`,
   so no harness silently ships a stale version number.

A third sweep fails on any manifest under a payload root that is not listed in
EXTRACTORS, so a newly added manifest cannot ship unvalidated.

Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-manifests/test_manifest_integrity.py
"""
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
PAYLOAD_ROOTS = ("dist", "dist-telemetry")

# Manifests that are payload *inputs* rather than shipped artifacts, or that
# declare no filesystem paths at all.
NO_DECLARED_PATHS: tuple[str, ...] = (
    # source "./" is the payload root itself, which trivially exists.
    "dist/.agents/plugins/marketplace.json",
)

FAILURES: list[str] = []


def _string_values(doc: dict, *keys: str) -> list[str]:
    """Collect the string paths at the named top-level keys, accepting either a
    bare string or a list of strings. A dict value (Codex's load-bearing empty
    `hooks: {}`) declares no path and is skipped."""
    found = []
    for key in keys:
        value = doc.get(key)
        if isinstance(value, str):
            found.append(value)
        elif isinstance(value, list):
            found.extend(v for v in value if isinstance(v, str))
    return found


def _claude_paths(doc: dict) -> list[str]:
    return _string_values(doc, "commands", "skills", "hooks", "agents")


def _codex_paths(doc: dict) -> list[str]:
    return _string_values(doc, "skills")


def _copilot_paths(doc: dict) -> list[str]:
    return _string_values(doc, "skills")


def _package_paths(doc: dict) -> list[str]:
    found = _string_values(doc, "main")
    pi = doc.get("pi")
    if isinstance(pi, dict):
        found.extend(s for s in pi.get("skills", []) if isinstance(s, str))
    return found


HOOK_COMMAND = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"\s]+)")


def _hook_paths(doc: dict) -> list[str]:
    """Hook commands are shell strings rooted at ${CLAUDE_PLUGIN_ROOT}. A hook
    pointing at a missing script breaks every session in the installed plugin,
    so the referenced executable must exist in the payload."""
    found = []
    for entries in doc.get("hooks", {}).values():
        for entry in entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                found.extend(HOOK_COMMAND.findall(command))
    return found


EXTRACTORS = {
    "dist/.claude-plugin/plugin.json": _claude_paths,
    "dist/.codex-plugin/plugin.json": _codex_paths,
    "dist/.github/plugin/plugin.json": _copilot_paths,
    "dist/package.json": _package_paths,
    "dist/hooks/hooks.json": _hook_paths,
    "dist-telemetry/.claude-plugin/plugin.json": _claude_paths,
}


def _payload_manifests() -> list[Path]:
    """Every .json under a payload root that looks like a manifest. Excludes
    context/ (shipped data, not configuration) and m365/ (its own package,
    covered by tests/m365)."""
    found = []
    for root in PAYLOAD_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for path in base.rglob("*.json"):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if "/context/" in rel or f"/{root}/m365/" in f"/{rel}":
                continue
            found.append(path)
    return sorted(found)


def main() -> int:
    canonical = json.loads(CANONICAL_MANIFEST.read_text())["version"]

    known = set(EXTRACTORS) | set(NO_DECLARED_PATHS)
    for manifest in _payload_manifests():
        rel = manifest.relative_to(REPO_ROOT).as_posix()
        root = REPO_ROOT / rel.split("/", 1)[0]
        doc = json.loads(manifest.read_text())

        if rel not in known:
            FAILURES.append(
                f"{rel}: manifest not covered by this test — add it to "
                "EXTRACTORS (or NO_DECLARED_PATHS if it declares no paths)"
            )
            continue

        for declared in EXTRACTORS.get(rel, lambda _doc: [])(doc):
            # Prefix strip, not lstrip: lstrip("./") would eat the leading dot
            # of a dotfile path like ".github/plugin/skills/".
            relative = declared[2:] if declared.startswith("./") else declared
            target = root / relative
            if not target.exists():
                FAILURES.append(
                    f"{rel}: declares {declared!r}, which does not exist in the "
                    f"payload (looked for {target.relative_to(REPO_ROOT)})"
                )
            elif target.is_dir() and not any(target.iterdir()):
                FAILURES.append(
                    f"{rel}: declares {declared!r}, which exists but is empty — "
                    "the harness would install a plugin with nothing in it"
                )

        version = doc.get("version")
        if version is not None and version != canonical:
            FAILURES.append(
                f"{rel}: version {version!r} != canonical {canonical!r} from "
                f"{CANONICAL_MANIFEST.relative_to(REPO_ROOT)} — derive it in the "
                "planner instead of hand-maintaining a second copy"
            )

    if FAILURES:
        print("FAIL — payload manifest integrity")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1

    print(f"ok — payload manifests consistent at version {canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
