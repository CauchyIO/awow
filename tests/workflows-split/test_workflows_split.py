"""Regression test for the workflows channel split in tools/gather.py (CAU-1632).

awow splits into a five-command core (dist/claude/awow/) and one optional
workflows bundle (dist/claude/awow-workflows/). No harness but Claude Code can express a plugin-to-plugin
dependency, so neither plugin declares one: each is self-contained, and the
core skills the bundle's commands invoke are copied into it.

Asserts, in order of how badly each would fail silently:

  1. Routing rule — `channel: workflows` parses identically in gather.py and
     tools/lint-paths.py, and ships_in() answers every (channel, payload) pair.
  2. Placement on a synthetic source tree, both directions — a workflows
     command/skill lands in every bundle folder (Claude, Codex, Copilot) and on
     NO base-plugin surface of those harnesses; a core one is the mirror image.
     Pi and opencode are the exception that matters: they install a whole repo
     as one package, so their combined awow folder must carry BOTH — tagging a
     command `workflows` must never delete it for their users. Synthetic, so
     the machinery is proven before any real command is tagged.
  3. Exactly-one-home on the real tree — every shipped skill is in one payload
     root, except WORKFLOWS_SHARED_SKILLS, which are in exactly awow and
     awow-workflows and byte-identical in both. A flat-name harness keeps the
     first of two same-named skills; identical copies make that harmless, a
     drifted copy makes it a coin toss.
  4. Self-containment — every path a bundle body names, as
     ${CLAUDE_PLUGIN_ROOT}/… or as the agent-skills form ../../…, resolves INSIDE
     that bundle folder, on every harness. {AWOW_ROOT} is a plugin's own root,
     so a copied skill that reads core's context/ lands on nothing.
  4b. Skill self-containment — every awow skill a bundle body invokes ("the
     `x` skill") ships in that same bundle folder. A shared skill that invokes
     another core skill drags it along: workitem-write names board-target, so
     it is shared too. Core is held to the mirror
     image — it may name a bundle-only skill solely in the using-awow routing
     line, which tells the agent what to do when a route is absent.
  5. Manifest — named awow-workflows, no `dependencies` key, version lockstep.
  6. Surface scope — a Claude Code plugin folder: no hooks (would double-inject
     using-awow) and no other harness's manifest or surface inside it. The
     bundle reaches another harness as its own dist/<harness>/awow-workflows/
     folder, never by widening this one.
  7. Generated root — dist/claude/awow-workflows/ is registered, and an unplanned file
     under it is reported as an orphan.
  8. Marketplace gate — on every harness with a marketplace (Claude Code,
     Copilot, Codex) the bundle is listed if and only if it ships commands, so
     an empty plugin is never installable.

Pure stdlib; no pytest, no network.

Run:  python3 tests/workflows-split/test_workflows_split.py
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))

gather = importlib.import_module("gather")

_spec = importlib.util.spec_from_file_location(
    "lint_paths", REPO_ROOT / "tools" / "lint-paths.py"
)
lint_paths = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint_paths)

FAILURES: list[str] = []


def files_under(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def top_names(root: Path) -> set[str]:
    return {f.split("/")[0] for f in files_under(root)}


# ---------- 1. routing rule ----------


def check_routing_rule() -> None:
    text = '---\nchannel: workflows\ndescription: "x"\n---\n\n# x\n'
    a, b = gather.declared_channel(text), lint_paths.channel(text)
    if (a, b) != ("workflows", "workflows"):
        FAILURES.append(f"channel parsers on `workflows`: gather={a!r} lint={b!r}")
    if not gather.is_workflows_channel(text):
        FAILURES.append("is_workflows_channel is False for channel: workflows")
    if gather.is_vendored_channel(text) or gather.is_telemetry_channel(text):
        FAILURES.append("channel: workflows also reads as vendored or telemetry")

    def fm(channel: str | None) -> str:
        line = f"channel: {channel}\n" if channel else ""
        return f'---\n{line}description: "x"\n---\n'

    # (declared channel, payload) -> ships?
    table = {
        (None, "both"): True, (None, "workflows"): False, (None, "telemetry"): False,
        ("bootstrap", "both"): True, ("bootstrap", "workflows"): False,
        ("workflows", "both"): False, ("workflows", "workflows"): True,
        ("workflows", "telemetry"): False,
        ("telemetry", "both"): False, ("telemetry", "workflows"): False,
        ("telemetry", "telemetry"): True,
        ("vendored", "both"): False, ("vendored", "workflows"): False,
        ("vendored", "telemetry"): False,
    }
    for (channel, payload), want in table.items():
        got = gather.ships_in(fm(channel), payload)
        if got != want:
            FAILURES.append(f"ships_in(channel={channel!r}, {payload!r}) == {got}, expected {want}")


# ---------- 2. placement on a synthetic tree ----------


def _write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def check_synthetic_placement() -> None:
    saved = (gather.AGENTS_DIR, gather.WORKFLOWS_SHARED_SKILLS)
    with tempfile.TemporaryDirectory() as tmp:
        agents = Path(tmp) / ".agents"
        cmd = lambda ch, af="": (  # noqa: E731
            f'---\n{ch}{af}description: "probe"\n---\n\n# probe\n\nBody.\n'
        )
        _write(agents / "commands" / "core-cmd.md", cmd(""))
        _write(agents / "commands" / "wf-cmd.md", cmd("channel: workflows\n", "autofire: true\n"))
        _write(agents / "commands" / "vend-cmd.md", cmd("channel: vendored\n"))
        skill = lambda name, ch: (  # noqa: E731
            f'---\nname: {name}\n{ch}description: "probe"\n---\n\n# {name}\n'
        )
        _write(agents / "skills" / "core-skill" / "SKILL.md", skill("core-skill", ""))
        _write(agents / "skills" / "shared-skill" / "SKILL.md", skill("shared-skill", ""))
        _write(agents / "skills" / "wf-skill" / "SKILL.md", skill("wf-skill", "channel: workflows\n"))
        _write(agents / "skills" / "wf-decl.md", skill("wf-decl", "channel: workflows\n"))
        gather.AGENTS_DIR = agents
        gather.WORKFLOWS_SHARED_SKILLS = ("shared-skill",)
        try:
            base = {p.target for p in gather.dist_surface_plans()}
            wf = {p.target for p in gather.workflows_surface_plans()}
            tele = {p.target for p in gather.plan_telemetry()}
            codex_market = json.loads(next(
                p.content for p in gather.plan_codex() if p.target == gather.CODEX_MARKETPLACE))
        finally:
            gather.AGENTS_DIR, gather.WORKFLOWS_SHARED_SKILLS = saved

    D, W = gather.CLAUDE_DIR, gather.DIST_WORKFLOWS_DIR
    C = gather.COPILOT_DIR
    base_surfaces = {
        "commands": lambda n: D / "commands" / f"{n}.md",
        "skills": lambda n: D / "skills" / n / "SKILL.md",
        "copilot prompts": lambda n: C / ".github" / "prompts" / f"{n}.prompt.md",
        "copilot skills": lambda n: C / ".github" / "plugin" / "skills" / n / "SKILL.md",
    }
    # Base-only agent-skills folders: a harness that can install the bundle
    # separately. The combined ones (Pi, opencode) are asserted apart, below.
    # Named literally, never read from gather.COMBINED_ROOTS: a test that takes
    # its expectations from the constant under test passes when that constant
    # is wrong — emptying it would drop these assertions with the behaviour.
    combined_roots = (gather.PI_DIR, gather.OPENCODE_DIR)
    if tuple(gather.COMBINED_ROOTS) != combined_roots:
        FAILURES.append(
            f"gather.COMBINED_ROOTS == {[r.parent.name for r in gather.COMBINED_ROOTS]}, expected "
            "['pi', 'opencode'] — both install a whole repo as one package"
        )
    for root in (gather.CODEX_DIR,):
        base_surfaces[f"{root.parent.name} agent-skills"] = (
            lambda n, root=root: root / "agent-skills" / n / "SKILL.md"
        )
    agent_skill_labels = [k for k in base_surfaces if k.endswith("agent-skills")]
    CW, PW = gather.CODEX_WORKFLOWS_DIR, gather.COPILOT_WORKFLOWS_DIR
    bundle_command = {
        "claude bundle": W / "commands" / "wf-cmd.md",
        "codex bundle": CW / "agent-skills" / "wf-cmd" / "SKILL.md",
        "copilot bundle": PW / ".github" / "prompts" / "wf-cmd.prompt.md",
    }
    bundle_skill = {
        "claude bundle": lambda n: W / "skills" / n / "SKILL.md",
        "codex bundle": lambda n: CW / "agent-skills" / n / "SKILL.md",
        "copilot bundle": lambda n: PW / ".github" / "plugin" / "skills" / n / "SKILL.md",
    }

    def expect(present: bool, targets: set, path: Path, why: str) -> None:
        if (path in targets) != present:
            rel = path.relative_to(REPO_ROOT)
            FAILURES.append(f"synthetic: {rel} {'missing' if present else 'present'} — {why}")

    # A workflows command: in the bundle (and autofired there), on no base surface.
    for label, path in bundle_command.items():
        expect(True, wf, path, f"workflows command not in the {label}")
    expect(True, wf, W / "skills" / "wf-cmd" / "SKILL.md", "autofire workflows command not mirrored as a bundle skill")
    for label, at in base_surfaces.items():
        expect(False, base, at("wf-cmd"), f"workflows command leaked onto base {label}")
    # Workflows skills (directory and declarative forms).
    for name in ("wf-skill", "wf-decl"):
        for label, at in bundle_skill.items():
            expect(True, wf, at(name), f"workflows skill not in the {label}")
        for label in ("skills", "copilot skills", *agent_skill_labels):
            expect(False, base, base_surfaces[label](name), f"workflows skill leaked onto base {label}")
    # A core command and skill: the mirror image.
    expect(True, base, D / "commands" / "core-cmd.md", "core command missing from base")
    for label in agent_skill_labels:
        expect(True, base, base_surfaces[label]("core-cmd"), f"core command missing from {label}")
    expect(False, wf, W / "commands" / "core-cmd.md", "core command leaked into the bundle")
    expect(False, wf, CW / "agent-skills" / "core-cmd" / "SKILL.md", "core command leaked into the codex bundle")
    expect(True, base, D / "skills" / "core-skill" / "SKILL.md", "core skill missing from base")
    for label, at in bundle_skill.items():
        expect(False, wf, at("core-skill"), f"unshared core skill leaked into the {label}")
    # The shared skill: both, on every harness that has a bundle folder.
    expect(True, base, D / "skills" / "shared-skill" / "SKILL.md", "shared skill missing from base")
    for label, at in bundle_skill.items():
        expect(True, wf, at("shared-skill"), f"shared skill missing from the {label}")
    # Combined packages (Pi, opencode): ONE folder carries base and bundle, each
    # source exactly once.
    for root in combined_roots:
        h = root.parent.name
        for name in ("core-cmd", "wf-cmd", "core-skill", "wf-skill", "wf-decl", "shared-skill"):
            expect(True, base, root / "agent-skills" / name / "SKILL.md",
                   f"{name} missing from the combined {h} package — tagging it must not delete it there")
        expect(False, base, root / "agent-skills" / "vend-cmd" / "SKILL.md", f"vendored command shipped to {h}")
    # The generated Codex marketplace lists the bundle once it ships a command.
    listed = [p["name"] for p in codex_market["plugins"]]
    if listed != ["awow", "awow-workflows"]:
        FAILURES.append(f"synthetic: Codex marketplace lists {listed} for a bundle WITH commands")
    # Vendored ships nowhere; telemetry takes nothing from this tree.
    for targets, root in ((base, D), (wf, W)):
        expect(False, targets, root / "commands" / "vend-cmd.md", "vendored command shipped")
    if any("probe" in t.as_posix() or t.name == "wf-cmd.md" for t in tele):
        FAILURES.append("synthetic: a workflows source reached dist/claude/awow-telemetry/")

    # A shared skill that stops being a `both` skill must fail the build loudly.
    saved_shared = gather.WORKFLOWS_SHARED_SKILLS
    gather.WORKFLOWS_SHARED_SKILLS = ("no-such-skill",)
    try:
        gather.plan_workflows()
        FAILURES.append("plan_workflows accepted a WORKFLOWS_SHARED_SKILLS name that is not a skill")
    except SystemExit:
        pass
    finally:
        gather.WORKFLOWS_SHARED_SKILLS = saved_shared


# ---------- 3. exactly one home, shared copies identical ----------


def check_one_home() -> None:
    roots = {
        "awow": gather.CLAUDE_DIR / "skills",
        "awow-telemetry": gather.DIST_TELEMETRY_DIR / "skills",
        "awow-workflows": gather.DIST_WORKFLOWS_DIR / "skills",
    }
    homes: dict[str, list[str]] = {}
    for label, root in roots.items():
        for name in top_names(root):
            homes.setdefault(name, []).append(label)
    shared = set(gather.WORKFLOWS_SHARED_SKILLS)
    for name, where in sorted(homes.items()):
        want = ["awow", "awow-workflows"] if name in shared else None
        if want is not None:
            if sorted(where) != want:
                FAILURES.append(f"shared skill {name} is in {sorted(where)}, expected {want}")
        elif len(where) != 1:
            FAILURES.append(
                f"skill {name} ships in {sorted(where)} — a flat-name harness keeps only "
                "the first; share it via WORKFLOWS_SHARED_SKILLS or give it one home"
            )
    for name in sorted(shared):
        a, b = roots["awow"] / name, roots["awow-workflows"] / name
        if files_under(a) != files_under(b):
            FAILURES.append(f"shared skill {name}: file sets differ between awow and awow-workflows")
            continue
        for rel in sorted(files_under(a)):
            if (a / rel).read_bytes() != (b / rel).read_bytes():
                FAILURES.append(f"shared skill {name}/{rel} is not byte-identical across the two payloads")

    # The same holds on every harness that has a bundle folder beside its base
    # plugin: shared skills and bundled context are byte-identical copies.
    pairs = (
        (gather.CLAUDE_DIR, gather.DIST_WORKFLOWS_DIR, "skills"),
        (gather.CODEX_DIR, gather.CODEX_WORKFLOWS_DIR, "agent-skills"),
        (gather.COPILOT_DIR, gather.COPILOT_WORKFLOWS_DIR, ".github/plugin/skills"),
    )
    for base_root, bundle_root, skills_rel in pairs:
        where = bundle_root.relative_to(REPO_ROOT).as_posix()
        for name in sorted(shared):
            a, b = base_root / skills_rel / name, bundle_root / skills_rel / name
            if not files_under(b):
                FAILURES.append(f"{where}: shared skill {name} is missing")
            for rel in sorted(files_under(b)):
                if not (a / rel).is_file() or (a / rel).read_bytes() != (b / rel).read_bytes():
                    FAILURES.append(f"{where}: shared skill {name}/{rel} is not byte-identical to the base plugin's")
        for rel in sorted(files_under(bundle_root / "context")):
            base_file = base_root / "context" / rel
            if not base_file.is_file():
                FAILURES.append(f"{where}/context/{rel} has no counterpart in the base plugin")
            elif base_file.read_bytes() != (bundle_root / "context" / rel).read_bytes():
                FAILURES.append(f"{where}/context/{rel} is not byte-identical to the base plugin's")


# ---------- 4. self-containment ----------


def check_self_contained() -> None:
    plugin_form = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")
    # The agent-skills form: relative to the skill folder, so ../../ is the
    # plugin folder. The lookbehind keeps a longer ../../../ from matching, and
    # skips a markdown link target — `](../../context/team/…)` is a link for a
    # human reading the source repo, to team data no payload ships, not a read.
    relative_form = re.compile(r"(?<![\w./(])\.\./\.\./([A-Za-z0-9_][A-Za-z0-9_./-]*)")
    for root in gather.WORKFLOWS_ROOTS:
        for path in sorted(root.rglob("*.md")):
            text = path.read_text()
            refs = set(plugin_form.findall(text)) | set(relative_form.findall(text))
            for ref in sorted(refs):
                ref = ref.rstrip("./")
                # A directory reference resolves if the directory exists; a
                # placeholder path (`boards/<your-board>/…`) never reaches here —
                # the character class stops at `<`, leaving the real prefix.
                if ref and not (root / ref).exists():
                    FAILURES.append(
                        f"{path.relative_to(REPO_ROOT)} reads <plugin>/{ref}, which "
                        f"{root.relative_to(REPO_ROOT)}/ does not ship — add it to WORKFLOWS_CONTEXT_PATHS / "
                        "WORKFLOWS_TOOL_PATHS, or the read lands on nothing"
                    )


# ---------- 4b. skill self-containment ----------

SKILL_MENTION = re.compile(r"`([a-z0-9][a-z0-9-]*)`\s+skill")


def _skill_names(skills_dir: Path) -> set[str]:
    return {p.parent.name for p in skills_dir.glob("*/SKILL.md")}


def check_skill_references() -> None:
    folders = {
        gather.DIST_WORKFLOWS_DIR: "skills",
        gather.CODEX_WORKFLOWS_DIR: "agent-skills",
        gather.COPILOT_WORKFLOWS_DIR: ".github/plugin/skills",
    }
    core_skills = _skill_names(gather.CLAUDE_DIR / "skills")
    known = core_skills | _skill_names(gather.DIST_WORKFLOWS_DIR / "skills")
    for root, skills_rel in folders.items():
        have = _skill_names(root / skills_rel)
        for path in sorted(root.rglob("*.md")):
            for name in sorted(set(SKILL_MENTION.findall(path.read_text())) & known - have):
                FAILURES.append(
                    f"{path.relative_to(REPO_ROOT)} invokes the `{name}` skill, which "
                    f"{root.relative_to(REPO_ROOT)}/ does not ship — add it to WORKFLOWS_SHARED_SKILLS "
                    "(or tag it `channel: workflows` if only the bundle uses it)"
                )
    # Core: a bundle-only skill may be named only by the using-awow routing line.
    bundle_only = known - core_skills
    for path in sorted(gather.CLAUDE_DIR.rglob("*.md")):
        if path.parent.name == "using-awow":
            continue
        for name in sorted(set(SKILL_MENTION.findall(path.read_text())) & bundle_only):
            FAILURES.append(
                f"{path.relative_to(REPO_ROOT)} invokes the `{name}` skill, which ships only in "
                "awow-workflows — a core-only install does not have it"
            )


# ---------- 5 + 6. manifest and surface scope ----------

# bundle folder -> (its manifest, the top-level entries that folder may hold).
BUNDLE_FOLDERS = {
    gather.DIST_WORKFLOWS_DIR: (".claude-plugin/plugin.json",
                                {".claude-plugin", "commands", "skills", "tools", "context", "handlers", "README.md"}),
    gather.CODEX_WORKFLOWS_DIR: (".codex-plugin/plugin.json",
                                 {".codex-plugin", "agent-skills", "tools", "context", "handlers"}),
    gather.COPILOT_WORKFLOWS_DIR: (".github/plugin/plugin.json",
                                   {".github", "tools", "context", "handlers"}),
}


def check_manifest_and_scope() -> None:
    canonical = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
    if set(BUNDLE_FOLDERS) != set(gather.WORKFLOWS_ROOTS):
        FAILURES.append("BUNDLE_FOLDERS is out of step with gather.WORKFLOWS_ROOTS — a bundle folder is untested")
    for root, (manifest_rel, allowed) in BUNDLE_FOLDERS.items():
        where = root.relative_to(REPO_ROOT).as_posix()
        manifest_path = root / manifest_rel
        if not manifest_path.is_file():
            FAILURES.append(f"{where}/{manifest_rel} is missing")
            continue
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("name") != "awow-workflows":
            FAILURES.append(f"{where}: bundle is named {manifest.get('name')!r}, expected 'awow-workflows'")
        if "dependencies" in manifest:
            FAILURES.append(
                f"{where}: manifest declares `dependencies` — only Claude Code can resolve one; "
                "the bundle is self-contained on every harness (CAU-1632)"
            )
        if manifest.get("version") != canonical:
            FAILURES.append(f"{where}: version {manifest.get('version')!r} != canonical {canonical!r}")

        # No hooks anywhere (a second copy would double-inject using-awow), and
        # no other harness's surface inside this harness's folder.
        extra = {p.name for p in root.iterdir()} - allowed
        if extra:
            FAILURES.append(
                f"{where}/ holds {sorted(extra)} — hooks, or another harness's surface; "
                "the bundle reaches a harness as its own dist/<harness>/awow-workflows/"
            )

        tools = files_under(root / "tools")
        if tools != set(gather.WORKFLOWS_TOOL_PATHS):
            FAILURES.append(f"{where}/tools/ == {sorted(tools)}, expected {sorted(gather.WORKFLOWS_TOOL_PATHS)}")

    both = set(gather.WORKFLOWS_TOOL_PATHS) & set(gather.PLUGIN_TOOL_PATHS)
    if both:
        FAILURES.append(f"tool(s) shipped in both plugins: {sorted(both)} — a tool moves, it is not copied")
    # A combined package carries both tool lists; nothing may be lost there.
    for root in (gather.PI_DIR, gather.OPENCODE_DIR):
        want = set(gather.PLUGIN_TOOL_PATHS) | set(gather.WORKFLOWS_TOOL_PATHS)
        if files_under(root / "tools") != want:
            FAILURES.append(f"{root.relative_to(REPO_ROOT)}/tools/ does not carry the base AND bundle tools")


# ---------- 7. generated root ----------


def check_generated_root() -> None:
    for root in gather.WORKFLOWS_ROOTS:
        where = root.relative_to(REPO_ROOT).as_posix()
        if root not in gather.GENERATED_ROOTS:
            FAILURES.append(f"{where}/ is not in GENERATED_ROOTS — its stale files would never be swept")
        if root not in gather.SURFACE_ROOTS["all"] or root not in gather.SURFACE_ROOTS["workflows"]:
            FAILURES.append(f"{where}/ is not swept by --surface all and --surface workflows")
    probe = gather.DIST_WORKFLOWS_DIR / "skills" / "orphan-probe" / "SKILL.md"
    created = []
    d = probe.parent
    while not d.exists():
        created.append(d)
        d = d.parent
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text("---\nname: orphan-probe\n---\n")
    try:
        planned = {p.target for p in gather.workflows_surface_plans()}
        orphans = gather.find_orphans(planned, list(gather.WORKFLOWS_ROOTS))
        if probe not in orphans:
            FAILURES.append("an unplanned file under dist/claude/awow-workflows/ was not reported as an orphan")
    finally:
        probe.unlink(missing_ok=True)
        for d in created:
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()


# ---------- 8. marketplace gate ----------


def check_marketplace_gate() -> None:
    has_commands = bool(files_under(gather.DIST_WORKFLOWS_DIR / "commands"))
    if has_commands != gather.workflows_has_commands():
        FAILURES.append("workflows_has_commands() disagrees with the built bundle — the Codex gate is wrong")

    def listing(name: str, plugins: list, source_of, want_source: str) -> None:
        entries = {p["name"]: p for p in plugins}
        listed = "awow-workflows" in entries
        if has_commands and not listed:
            FAILURES.append(f"the bundle ships commands but the {name} marketplace does not list awow-workflows")
        if listed and not has_commands:
            FAILURES.append(f"the {name} marketplace lists awow-workflows but the bundle ships no commands — an empty plugin is installable")
        if listed and source_of(entries["awow-workflows"]) != want_source:
            FAILURES.append(f"{name} marketplace: awow-workflows source == {source_of(entries['awow-workflows'])!r}, expected {want_source!r}")

    for name, rel, want in (
        ("Claude Code", ".claude-plugin/marketplace.json", "./dist/claude/awow-workflows"),
        ("Copilot", ".github/plugin/marketplace.json", "./dist/copilot/awow-workflows"),
    ):
        plugins = json.loads((REPO_ROOT / rel).read_text()).get("plugins", [])
        listing(name, plugins, lambda e: e.get("source"), want)
    codex = json.loads(gather.CODEX_MARKETPLACE.read_text()).get("plugins", [])
    listing("Codex", codex, lambda e: e.get("source", {}).get("path"), "./codex/awow-workflows")


def main() -> int:
    check_routing_rule()
    check_synthetic_placement()
    check_one_home()
    check_self_contained()
    check_skill_references()
    check_manifest_and_scope()
    check_generated_root()
    check_marketplace_gate()
    for f in FAILURES:
        print(f"FAIL {f}")
    if FAILURES:
        print(f"\n{len(FAILURES)} failure(s).", file=sys.stderr)
        return 1
    print("Workflows split OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
