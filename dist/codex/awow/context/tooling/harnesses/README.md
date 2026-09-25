# context/tooling/harnesses/

Reference instructions per agent harness. One file per supported harness.

`/setup-awow` detects which harness the user is on and loads the matching reference. The real signal is which harness the model is running inside; corroborating on-disk signals are `.claude/`, `.github/`, a repo-root `AGENTS.md` with `.codex-plugin/` (Codex), `.pi/` (Pi), and `.opencode/` or `opencode.json` (opencode).

## Supported harnesses

Six, decided for 1.0.0 (CAU-1627). Every harness installs the same built payload; the source is `.agents/`, rendered once per harness by `tools/gather.py` into `dist/<harness>/<plugin>/`. "Supported" promises three things per row: the install route works, the optional `awow-workflows` bundle can be added beside core, and the behaviour has been exercised. The last column is the truth today, not the aim; CAU-1648 moves it.

| Harness | Reference | Install core | Workflows bundle | Tested for 1.0.0 |
|---|---|---|---|---|
| Claude Code | `claude-code.md` | `/plugin marketplace add CauchyIO/awow`, `/plugin install awow@awow` | second plugin, `awow-workflows@awow` | yes — dry runs and the eval suites |
| GitHub Copilot CLI | `copilot.md` | `copilot plugin marketplace add CauchyIO/awow`, `copilot plugin install awow@awow` | second plugin, `awow-workflows@awow` | install route from the vendor's docs; not yet run |
| Codex | `codex.md` | `codex plugin marketplace add https://github.com/CauchyIO/awow-dist`, `codex plugin add awow@awow` | second plugin, `awow-workflows@awow` | install route from the vendor's docs; not yet run |
| Pi | `pi.md` | `pi install git:github.com/CauchyIO/awow-dist` | included — one package carries core and the bundle | install route from the vendor's docs; not yet run |
| opencode | `opencode.md` | `opencode plugin awow@git+https://github.com/CauchyIO/awow-dist.git` | included — one package carries core and the bundle | install route from the vendor's docs; not yet run |
| Microsoft 365 Copilot | `m365-copilot.md` | a declarative agent from `gather.py --surface m365`, sideloaded | not applicable — no repo, no commands; the agent reads awow's context | pilot: built and budget-checked in CI; not yet run against a tenant |

Claude Code and GitHub Copilot install from the awow repo, whose marketplace manifests serve `dist/claude/` and `dist/copilot/`; Codex, Pi and opencode install from `CauchyIO/awow-dist`, where `tools/sync-dist.sh` publishes the built payloads. Codex, Pi and opencode also read the repo-root `AGENTS.md` natively, so a repo carrying one steers them with no install; the commands reach them as skills through the payload. Pi and opencode install a whole repository as one package and cannot add a plugin from a subfolder, which is why their package carries core and the bundle together. Nothing is mirrored into a repo's own harness folders. `m365-copilot.md` is a pilot: it targets non-technical users with no repo — see that file for scope and limits.

## Why multiple

The supported harnesses have non-overlapping user bases. Single-harness defaults exclude real audiences; carrying one reference file per harness keeps the starter pack usable for any of them from the same `.agents/` source.

## Adding a new harness

Same shape. The file documents what the harness provides (slash commands? agent skills? hooks?), how the built payload reaches it, and the settings file format.
