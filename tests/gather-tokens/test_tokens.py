"""Regression test for the path-token substitution tables in tools/gather.py.

{AWOW_TOOLS} and {AWOW_ROOT} are resolved at build time per channel; {HUB} and
{PROJECT} ship as-is because the session reflex teaches their resolution. This
asserts all four behaviours on both channels, and that the agent-skills channel
never emits ${CLAUDE_PLUGIN_ROOT} (Codex and Pi cannot resolve it).

Pure stdlib; no pytest, no network.

Run:  python3 tests/gather-tokens/test_tokens.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

REPO_ROOT = Path(__file__).resolve().parents[2]

import importlib

gather = importlib.import_module("gather")

FAILURES = []


def check(label, actual, expected):
    if actual != expected:
        FAILURES.append(f"{label}\n  expected: {expected!r}\n  actual:   {actual!r}")


def main() -> int:
    plugin = gather.render_plugin_body
    skills = gather.render_agent_skills_body

    check(
        "plugin: {AWOW_ROOT} -> ${CLAUDE_PLUGIN_ROOT}",
        plugin("read {AWOW_ROOT}/context/tooling/mining.md"),
        "read ${CLAUDE_PLUGIN_ROOT}/context/tooling/mining.md",
    )
    check(
        "plugin: {AWOW_TOOLS} still resolves",
        plugin("run {AWOW_TOOLS}/gather.py"),
        "run ${CLAUDE_PLUGIN_ROOT}/tools/gather.py",
    )
    check(
        "agent-skills: {AWOW_ROOT} -> ../..",
        skills("read {AWOW_ROOT}/context/tooling/mining.md"),
        "read ../../context/tooling/mining.md",
    )
    check(
        "agent-skills: {AWOW_TOOLS} still resolves",
        skills("run {AWOW_TOOLS}/gather.py"),
        "run ../../tools/gather.py",
    )
    # {HUB}/{PROJECT} are session-resolved, never build-substituted.
    for name, render in (("plugin", plugin), ("agent-skills", skills)):
        check(
            f"{name}: {{HUB}} passes through",
            render("read {HUB}/context/tooling/board.md"),
            "read {HUB}/context/tooling/board.md",
        )
        check(
            f"{name}: {{PROJECT}} passes through",
            render("write {PROJECT}/proposals/x.md"),
            "write {PROJECT}/proposals/x.md",
        )
    # Codex and Pi cannot resolve ${CLAUDE_PLUGIN_ROOT}.
    out = skills("{AWOW_ROOT}/context/x.md and {AWOW_TOOLS}/y.py")
    if "${CLAUDE_PLUGIN_ROOT}" in out:
        FAILURES.append(f"agent-skills leaked ${{CLAUDE_PLUGIN_ROOT}}: {out!r}")

    # A file must be able to NAME a token without USING it. {{X}} escapes to {X}.
    check(
        "plugin: {{AWOW_ROOT}} escapes to a literal",
        plugin("the {{AWOW_ROOT}} token points at the payload"),
        "the {AWOW_ROOT} token points at the payload",
    )
    check(
        "agent-skills: {{AWOW_TOOLS}} escapes to a literal",
        skills("the {{AWOW_TOOLS}} token points at tools/"),
        "the {AWOW_TOOLS} token points at tools/",
    )
    # Escaping must not disable real substitution in the same string.
    check(
        "plugin: escaped and live tokens coexist",
        plugin("{{AWOW_ROOT}} resolves to {AWOW_ROOT}"),
        "{AWOW_ROOT} resolves to ${CLAUDE_PLUGIN_ROOT}",
    )
    # The always-on reflex text must survive intact on both channels.
    reflex = (REPO_ROOT / ".agents" / "skills" / "using-awow" / "SKILL.md").read_text()
    for name, render in (("plugin", plugin), ("agent-skills", skills)):
        out = render(reflex)
        for tok in ("{AWOW_ROOT}", "{AWOW_TOOLS}", "{HUB}", "{PROJECT}"):
            if tok not in out:
                FAILURES.append(
                    f"{name}: using-awow/SKILL.md ships with no literal {tok} — "
                    "the file that teaches the tokens must still name them"
                )

    # The escape is scoped to the four path tokens ON PURPOSE. A blanket
    # {{[A-Z_]+}} would also unwrap double-brace markers that belong to other
    # vocabularies — a prompt describing an HTML template's {{PLACEHOLDER}}
    # syntax would ship it as {PLACEHOLDER}, silently changing documented
    # markup. That is the same self-corruption this escape exists to prevent,
    # in reverse. Guard the scoping so a later refactor cannot widen it back.
    for name, render in (("plugin", plugin), ("agent-skills", skills)):
        for foreign in ("{{PLACEHOLDER}}", "{{VALUE}}", "{{ANY_OTHER_NAME}}"):
            check(
                f"{name}: {foreign} is not a path token and must pass through",
                render(f"the template uses {foreign} markers"),
                f"the template uses {foreign} markers",
            )

    # And the scoping must cover exactly the tokens the build substitutes —
    # a token added to a substitution table without being added to
    # PATH_TOKEN_NAMES could not be escaped in the prose that documents it.
    substituted = {t for t, _ in gather.PLUGIN_TOKEN_SUBSTITUTIONS}
    substituted |= {t for t, _ in gather.AGENT_SKILLS_TOKEN_SUBSTITUTIONS}
    escapable = {"{" + n + "}" for n in gather.PATH_TOKEN_NAMES}
    for tok in sorted(substituted - escapable):
        FAILURES.append(
            f"{tok} is substituted but absent from PATH_TOKEN_NAMES — "
            "prose documenting it could not be escaped"
        )

    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Path-token substitution OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
