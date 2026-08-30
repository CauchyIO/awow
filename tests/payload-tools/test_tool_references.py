"""Every tool a shipped prompt body invokes must exist in that same payload.

`gather.py` rewrites `{AWOW_TOOLS}` per surface — `${CLAUDE_PLUGIN_ROOT}/tools`
for the plugin bodies, `../../tools` for the Agent Skills bodies — and ships
only the runtime slice of `tools/` (PLUGIN_TOOL_PATHS / TELEMETRY_TOOL_PATHS).
Nothing ties the two together: a body can name a script the slice never
carries, `gather.py --check` stays green because generator and output agree,
and the adopter finds out when the command runs. That is how `/okr-cascade`
shipped for months telling the agent to run `cascade_check.py` from a payload
that did not contain it.

`tests/gather-tokens/` proves the substitution strings; `tests/payload-manifests/`
proves manifest-declared paths resolve. This is the third leg: every rewritten
tool reference in every shipped body resolves to a file inside its payload root.

- `${CLAUDE_PLUGIN_ROOT}/tools/<x>` must exist at `<root>/tools/<x>`.
- `../../tools/<x>` is resolved relative to the referencing file, so a body
  copied to the wrong depth fails here rather than at the adopter.

Raw `{AWOW_TOOLS}` tokens are not checked: the ones that survive are the
documented `{{…}}` escapes in `using-awow`, naming the vocabulary rather than
using it. Pure stdlib; no pytest, no network.

Run:  python3 tests/payload-tools/test_tool_references.py
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_ROOTS = ("dist", "dist-telemetry")

# The two rendered forms of {AWOW_TOOLS}/<path> (gather.py PLUGIN_TOKEN_SUBSTITUTIONS
# and AGENT_SKILLS_TOKEN_SUBSTITUTIONS). The path class stops at whitespace,
# quotes, and backticks, which is how bodies delimit a path in prose and shell.
PLUGIN_FORM = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/tools/([A-Za-z0-9_./-]+)")
RELATIVE_FORM = re.compile(r"(?<![\w./])(\.\./\.\./tools/[A-Za-z0-9_./-]+)")


def _shipped_files(root: Path) -> list[Path]:
    """Every file under the payload root except the m365 package (its own
    build, covered by tests/m365)."""
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and "m365" not in p.relative_to(root).parts
    )


def _references(path: Path) -> list[tuple[str, Path]]:
    """(reference as written, resolved target) for every tool path in the file."""
    text = path.read_text(encoding="utf-8")
    root = REPO_ROOT / path.relative_to(REPO_ROOT).parts[0]
    found = []
    for rel in PLUGIN_FORM.findall(text):
        found.append((f"${{CLAUDE_PLUGIN_ROOT}}/tools/{rel}", root / "tools" / rel))
    for ref in RELATIVE_FORM.findall(text):
        found.append((ref, (path.parent / ref).resolve()))
    return found


def main() -> int:
    failures: list[str] = []
    checked = 0
    for root_name in PAYLOAD_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for path in _shipped_files(root):
            for written, target in _references(path):
                checked += 1
                if target.is_file():
                    continue
                failures.append(
                    f"{path.relative_to(REPO_ROOT)}: references {written!r}, "
                    f"but {target.relative_to(REPO_ROOT)} is not in the payload — "
                    "add it to the tool list in tools/gather.py or drop the reference"
                )

    if failures:
        print("FAIL — payload tool references")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"ok — {checked} tool reference(s) resolve inside their payload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
