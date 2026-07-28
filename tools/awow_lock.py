"""awow lockfile — track which starter-owned files a repo vendored, at what
version, so `/update-awow` can tell a clean update from a local edit from a
real conflict.

The lockfile at ``tools/awow.lock.json`` records, for every starter-owned file
this repo carries, the upstream content hash it was last reconciled against,
plus the awow version and the board/solo mode the repo was set up with. That
recorded hash is the **baseline** — the third leg of a 3-way compare:

    baseline (in the lock)  vs  local (this repo now)  vs  source (upstream now)

    baseline == local == source        -> skip        (nothing to do)
    baseline == local,  source != base -> update      (upstream moved; take it)
    source   == base,   local  != base -> keep-local  (you edited; upstream didn't)
    local    == source                 -> skip        (already converged)
    all three differ                   -> conflict     (both moved; write .awow)

Without the baseline, every file the team has ever touched looks like a
conflict forever. With it, updates are quiet and only surface genuine
three-way conflicts.

The lockfile IS the manifest: it lists exactly the files this repo vendored,
so board/solo trims and Step-9 skill drops are captured for free. A starter
file present upstream but absent from the lock is a genuinely *new* file; a
file in the lock but absent locally is one the team deleted and we must not
re-add.

Subcommands
-----------
    backfill   Create/refresh the baseline from the LOCAL tree (run at install
               time — at t0 local == upstream, so hashing local gives the
               correct baseline). Consumes tools/.awow-vendor-stamp if present.

               A repo that customized starter files BEFORE the lockfile existed
               must not backfill from the working tree: the edits would become
               the baseline and the next apply would overwrite them as clean
               updates. Two retrofit modes seed a truthful baseline instead:

               --baseline-ref <ref>  hash this repo's tree at <ref> — the
                                     commit where awow was originally vendored.
               --source <clone>      match each local file against every content
                                     version in the upstream clone's history.
                                     A match means pristine (baseline = local);
                                     no match means team-edited (baseline = the
                                     oldest upstream version, so the file lands
                                     as conflict/keep-local, never update).
                                     Files with no upstream history at all are
                                     team-owned and stay out of the lock. One
                                     blind spot: a file the team deleted looks
                                     identical to one never vendored, so it
                                     comes back as `new` on apply.
    status     Read-only. Offline: report version + which starter files you've
               locally modified. With --source: full 3-way plan + version delta.
    apply      Perform the update against --source: overwrite `update`/`new`
               files, write `<file>.awow` for conflicts, leave `keep-local`
               alone, then rewrite the baseline to the reconciled state.

Add --json to `status`/`apply` for machine output (used by /update-awow).

STARTER_PATHS / ALWAYS_EXCLUDE / SOLO_EXCLUDE mirror setup/awowify.sh. Keep the
two in sync — they define the same "what is starter-owned" boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
LOCK_REL = "tools/awow.lock.json"
STAMP_REL = "tools/.awow-vendor-stamp"

# Starter-owned roots — MIRRORS setup/awowify.sh STARTER_PATHS. Keep in sync.
STARTER_PATHS = [
    ".agents",
    "tools",
    "setup",
    "context",
    "mcps",
    "pyproject.toml",
    "SETUP.md",
    "REFERENCES.md",
]

# Never managed — maintainer-only tooling (MIRRORS awowify.sh EXCLUDES) plus the
# lock machinery's own files. Prefix-matched against POSIX relpaths.
ALWAYS_EXCLUDE = {
    "setup/awowify.sh",
    "setup/awowify.ps1",
    "tools/distribute.py",
    "tools/reset-adopter-state.py",
    "tools/sync-dist.sh",
    ".agents/commands/awow-reset.md",
    LOCK_REL,
    STAMP_REL,
}

# Dropped in solo mode — MIRRORS awowify.sh's SOLO excludes.
SOLO_EXCLUDE = {
    "context/company",
    "context/team/members.md",
    ".agents/commands/daily-digest.md",
    ".agents/commands/weekly-digest.md",
    ".agents/commands/cross-team-view.md",
    ".agents/commands/coaching-review.md",
    ".agents/commands/process-transcript.md",
}

BOARD_TOOLS = ["linear", "jira", "azure-devops", "github-issues"]

DEFAULT_MODE = {"board": "all", "solo": False}


# --------------------------------------------------------------------------- #
# starter-file enumeration
# --------------------------------------------------------------------------- #

def _hits(rel: str, patterns) -> bool:
    """True if rel equals a pattern or sits under one (prefix match)."""
    for p in patterns:
        if rel == p or rel.startswith(p + "/"):
            return True
    return False


def _excluded(rel: str, mode: dict) -> bool:
    if _hits(rel, ALWAYS_EXCLUDE):
        return True
    parts = rel.split("/")
    if "__pycache__" in parts:
        return True
    if rel.endswith(".awow") or rel.endswith(".pyc"):
        return True
    if parts[-1] == ".DS_Store":
        return True
    if mode.get("solo") and _hits(rel, SOLO_EXCLUDE):
        return True
    board = mode.get("board", "all")
    if board != "all":
        others = [f"context/tooling/boards/{t}" for t in BOARD_TOOLS if t != board]
        if _hits(rel, others):
            return True
    return False


def _tracked_files(root: Path):
    """git-tracked starter files under root, or None if root is not a git repo.

    The starter tree is *what's committed* — this keeps untracked junk (tracing
    logs, generated stubs, .venv) out of the baseline. Falls back to a
    filesystem walk when there is no git repo to consult.
    """
    proc = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", *STARTER_PATHS],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return sorted(x for x in proc.stdout.split("\0") if x)


def _walk_starter_files(root: Path, mode: dict):
    for rel_root in STARTER_PATHS:
        p = root / rel_root
        if not p.exists():
            continue
        if p.is_file():
            if not _excluded(rel_root, mode):
                yield rel_root
        else:
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(root).as_posix()
                    if not _excluded(rel, mode):
                        yield rel


def _iter_starter_files(root: Path, mode: dict):
    """Yield POSIX relpaths of every managed starter file under root."""
    tracked = _tracked_files(root)
    if tracked is None:
        yield from _walk_starter_files(root, mode)
        return
    for rel in tracked:
        if not _excluded(rel, mode) and (root / rel).is_file():
            yield rel


# --------------------------------------------------------------------------- #
# hashing, version, git, stamp, lock IO
# --------------------------------------------------------------------------- #

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _read_version(root: Path):
    """Read the awow version from the plugin manifest, if the tree carries one.

    Present in template repos (full tree); absent in awowify'd repos, whose
    version travels in the lock / vendor stamp instead.
    """
    for rel in (".claude-plugin/plugin.json", ".github/plugin/plugin.json"):
        p = root / rel
        if p.exists():
            version = json.loads(p.read_text()).get("version")
            if version:
                return version
    return None


def _git_commit(root: Path):
    """Short HEAD of root, or None if root is not a git repo / git is absent.

    None is a legitimate value here (commit is optional provenance metadata,
    the version is what drives updates) — this is explicit control flow on the
    return code, not a swallowed error.
    """
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return proc.stdout.strip()
    return None


def _read_stamp(root: Path):
    """Parse tools/.awow-vendor-stamp (key=value lines) written by awowify.sh."""
    p = root / STAMP_REL
    if not p.exists():
        return None
    stamp = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        stamp[key.strip()] = value.strip()
    return stamp


def _resolve_mode(lock, stamp) -> dict:
    if lock and lock.get("mode"):
        return lock["mode"]
    if stamp:
        return {
            "board": stamp.get("board", "all"),
            "solo": stamp.get("solo", "0") in ("1", "true", "True"),
        }
    return dict(DEFAULT_MODE)


def _load_lock(root: Path):
    p = root / LOCK_REL
    return json.loads(p.read_text()) if p.exists() else None


def _write_lock(root: Path, lock: dict) -> None:
    path = root / LOCK_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


# --------------------------------------------------------------------------- #
# retrofit baselines — repos that predate the lockfile
# --------------------------------------------------------------------------- #

def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _show_at_ref(repo: Path, ref: str, rel: str) -> bytes | None:
    """Blob content of rel at ref, or None if the path is absent at that ref.

    Absence is a legitimate answer the callers branch on; any other git
    failure (bad ref, not a repo) is raised by the caller that resolves refs.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{rel}"],
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _files_at_ref(repo: Path, ref: str, mode: dict) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "-z",
         ref, "--", *STARTER_PATHS],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"git ls-tree {ref} failed: {proc.stderr.strip()}")
    return [rel for rel in proc.stdout.split("\0")
            if rel and not _excluded(rel, mode)]


def _read_version_at_ref(repo: Path, ref: str):
    for rel in (".claude-plugin/plugin.json", ".github/plugin/plugin.json"):
        blob = _show_at_ref(repo, ref, rel)
        if blob is not None:
            version = json.loads(blob).get("version")
            if version:
                return version
    return None


def _baseline_from_ref(root: Path, ref: str, mode: dict) -> dict:
    """Baseline = this repo's starter tree as of ref (the vendor commit)."""
    files = {}
    for rel in _files_at_ref(root, ref, mode):
        blob = _show_at_ref(root, ref, rel)
        if blob is None:  # ls-tree listed it, so this is a real git failure
            raise SystemExit(f"could not read {ref}:{rel}")
        files[rel] = _sha256_bytes(blob)
    return files


def _history_hashes(source: Path, rels: set[str]) -> dict:
    """Every content hash each rel ever had anywhere in source's history."""
    proc = subprocess.run(
        ["git", "-C", str(source), "log", "--all", "--no-renames", "--raw",
         "--no-abbrev", "--format="],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"git log in {source} failed: {proc.stderr.strip()}")

    blobs_by_rel: dict[str, set] = {}
    for line in proc.stdout.splitlines():
        if not line.startswith(":"):
            continue
        meta, _, rel = line.partition("\t")
        if rel not in rels:
            continue
        new_blob = meta.split()[3]
        if set(new_blob) == {"0"}:  # deletion — no content on the new side
            continue
        blobs_by_rel.setdefault(rel, set()).add(new_blob)

    cache: dict[str, str] = {}
    hashes_by_rel = {}
    for rel, blobs in blobs_by_rel.items():
        hashes = set()
        for blob in blobs:
            if blob not in cache:
                p = subprocess.run(
                    ["git", "-C", str(source), "cat-file", "blob", blob],
                    capture_output=True,
                )
                if p.returncode != 0:
                    raise SystemExit(f"git cat-file {blob} in {source} failed")
                cache[blob] = _sha256_bytes(p.stdout)
            hashes.add(cache[blob])
        hashes_by_rel[rel] = hashes
    return hashes_by_rel


def _oldest_upstream_hash(source: Path, rel: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(source), "rev-list", "--reverse", "--all", "--", rel],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit(f"no history for {rel} in {source}")
    first = proc.stdout.splitlines()[0]
    blob = _show_at_ref(source, first, rel)
    if blob is None:
        raise SystemExit(f"could not read {first}:{rel} in {source}")
    return _sha256_bytes(blob)


def _baseline_from_source_history(root: Path, source: Path, mode: dict) -> dict:
    """Classify each local starter file against upstream's full history.

    Hash found in history -> pristine at some released version, baseline is
    the local hash. Not found -> team-edited, baseline is the oldest upstream
    version so the 3-way compare protects it. Never existed upstream ->
    team-owned, left unmanaged.
    """
    rels = list(_iter_starter_files(root, mode))
    history = _history_hashes(source, set(rels))
    files = {}
    for rel in rels:
        known = history.get(rel)
        if known is None:
            continue
        local_h = _sha256(root / rel)
        files[rel] = local_h if local_h in known else _oldest_upstream_hash(source, rel)
    return files


# --------------------------------------------------------------------------- #
# 3-way classification
# --------------------------------------------------------------------------- #

def _classify(base, local, src) -> str:
    if src is None:
        return "removed-upstream"   # upstream dropped it; leave local alone
    if local is None:
        return "removed-local"      # team deleted it; do not re-add
    if base == local == src:
        return "skip"
    if local == src:
        return "skip"               # already converged
    if local == base and src != base:
        return "update"
    if src == base and local != base:
        return "keep-local"
    return "conflict"               # base != local, src != base, local != src


def _compute_plan(root: Path, source: Path, lock: dict) -> dict:
    mode = lock.get("mode", dict(DEFAULT_MODE))
    base_map = lock.get("files", {})
    entries = []

    for rel, base_hash in sorted(base_map.items()):
        local_p = root / rel
        src_p = source / rel
        local_h = _sha256(local_p) if local_p.exists() else None
        src_h = _sha256(src_p) if src_p.exists() else None
        entries.append({"rel": rel, "verdict": _classify(base_hash, local_h, src_h)})

    # Starter files upstream carries but the lock does not know about.
    known = set(base_map)
    for rel in _iter_starter_files(source, mode):
        if rel in known:
            continue
        local_p = root / rel
        if not local_p.exists():
            entries.append({"rel": rel, "verdict": "new"})
        else:
            # Present locally but untracked by the lock — adopt if identical,
            # else surface as a conflict so nothing is silently clobbered.
            same = _sha256(local_p) == _sha256(source / rel)
            entries.append({"rel": rel, "verdict": "skip" if same else "conflict"})

    entries.sort(key=lambda e: e["rel"])
    return {
        "from_version": lock.get("awow_version"),
        "to_version": _read_version(source),
        "from_commit": lock.get("source_commit"),
        "to_commit": _git_commit(source),
        "entries": entries,
    }


def _baseline_from_source(root: Path, source: Path, mode: dict, old_files: dict) -> dict:
    """New baseline after a reconcile: source hash for everything upstream ships,
    local hash for files upstream dropped but the team kept."""
    files = {}
    for rel in _iter_starter_files(source, mode):
        files[rel] = _sha256(source / rel)
    for rel in old_files:
        if rel not in files and (root / rel).exists():
            files[rel] = _sha256(root / rel)
    return files


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #

def cmd_backfill(root: Path, baseline_ref: str | None = None,
                 source: Path | None = None) -> int:
    lock = _load_lock(root)
    stamp = _read_stamp(root)
    mode = _resolve_mode(lock, stamp)

    version = (
        (stamp or {}).get("awow_version")
        or (lock or {}).get("awow_version")
        or (baseline_ref and _read_version_at_ref(root, baseline_ref))
        or _read_version(root)
    )
    commit = (stamp or {}).get("source_commit") or (lock or {}).get("source_commit") or _git_commit(root)

    if baseline_ref:
        files = _baseline_from_ref(root, baseline_ref, mode)
    elif source:
        files = _baseline_from_source_history(root, source, mode)
    else:
        # t0 install: local == upstream, so hashing the working tree is the
        # correct baseline. Re-hash an existing lock's file set if present.
        if lock and lock.get("files"):
            rels = list(lock["files"])
        else:
            rels = list(_iter_starter_files(root, mode))
        files = {rel: _sha256(root / rel) for rel in rels if (root / rel).exists()}

    _write_lock(root, {
        "awow_version": version,
        "source_commit": commit,
        "mode": mode,
        "files": files,
    })
    if stamp is not None:
        (root / STAMP_REL).unlink()

    print(f"awow.lock.json baseline: {len(files)} files at version "
          f"{version or 'unknown'} ({commit or 'no-commit'})")
    return 0


def cmd_status(root: Path, source: Path | None, as_json: bool) -> int:
    lock = _load_lock(root)
    if lock is None:
        msg = "No tools/awow.lock.json — run setup/install.sh to establish a baseline."
        print(json.dumps({"error": msg}) if as_json else msg)
        return 1

    if source is None:
        modified = []
        for rel, base in lock.get("files", {}).items():
            p = root / rel
            if not p.exists():
                modified.append({"rel": rel, "state": "deleted"})
            elif _sha256(p) != base:
                modified.append({"rel": rel, "state": "modified"})
        modified.sort(key=lambda e: e["rel"])
        report = {
            "awow_version": lock.get("awow_version"),
            "source_commit": lock.get("source_commit"),
            "managed": len(lock.get("files", {})),
            "locally_modified": modified,
            "source_checked": False,
        }
        if as_json:
            print(json.dumps(report, indent=2))
        else:
            _print_offline(report)
        return 0

    plan = _compute_plan(root, source, lock)
    if as_json:
        print(json.dumps(plan, indent=2))
    else:
        _print_plan(plan)
    return 0


def cmd_apply(root: Path, source: Path, as_json: bool) -> int:
    lock = _load_lock(root)
    if lock is None:
        raise SystemExit("No tools/awow.lock.json — run setup/install.sh first.")

    plan = _compute_plan(root, source, lock)
    counts: dict[str, int] = {}
    conflicts, updated, added = [], [], []
    for e in plan["entries"]:
        rel, verdict = e["rel"], e["verdict"]
        counts[verdict] = counts.get(verdict, 0) + 1
        if verdict == "update":
            _copy(source / rel, root / rel)
            updated.append(rel)
        elif verdict == "new":
            _copy(source / rel, root / rel)
            added.append(rel)
        elif verdict == "conflict":
            _copy(source / rel, root / (rel + ".awow"))
            conflicts.append(rel)
        # skip / keep-local / removed-* -> no file operation

    mode = lock.get("mode", dict(DEFAULT_MODE))
    _write_lock(root, {
        "awow_version": plan["to_version"],
        "source_commit": plan["to_commit"],
        "mode": mode,
        "files": _baseline_from_source(root, source, mode, lock.get("files", {})),
    })

    result = {
        "from_version": plan["from_version"],
        "to_version": plan["to_version"],
        "counts": counts,
        "updated": sorted(updated),
        "added": sorted(added),
        "conflicts": sorted(conflicts),
    }
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        _print_apply(result)
    return 0


# --------------------------------------------------------------------------- #
# human output
# --------------------------------------------------------------------------- #

def _print_offline(r: dict) -> None:
    print(f"awow version: {r['awow_version'] or 'unknown'} ({r['source_commit'] or 'no-commit'})")
    print(f"managed starter files: {r['managed']}")
    if r["locally_modified"]:
        print(f"locally modified: {len(r['locally_modified'])}")
        for e in r["locally_modified"]:
            print(f"  {e['state']}: {e['rel']}")
    else:
        print("no local modifications to starter files")
    print("\n(no source given — pass --source <awow clone or plugin root> to check for updates)")


def _version_line(plan: dict) -> str:
    frm = plan["from_version"] or "unknown"
    to = plan["to_version"] or "unknown"
    arrow = "up to date" if frm == to else f"{frm} -> {to}"
    return f"awow version: {arrow}"


def _group(plan: dict) -> dict:
    g: dict[str, list] = {}
    for e in plan["entries"]:
        g.setdefault(e["verdict"], []).append(e["rel"])
    return g


def _print_plan(plan: dict) -> None:
    print(_version_line(plan))
    g = _group(plan)
    order = ["update", "new", "conflict", "keep-local", "removed-upstream", "removed-local", "skip"]
    labels = {
        "update": "will update (upstream changed, you didn't)",
        "new": "will add (new upstream file)",
        "conflict": "conflict (both changed — saved as <file>.awow to merge)",
        "keep-local": "kept (your local edits, upstream unchanged)",
        "removed-upstream": "upstream removed (left in place)",
        "removed-local": "you deleted (not re-added)",
        "skip": "unchanged",
    }
    for verdict in order:
        rels = g.get(verdict, [])
        if not rels:
            continue
        print(f"\n{labels[verdict]}: {len(rels)}")
        if verdict in ("update", "new", "conflict"):
            for rel in rels:
                print(f"  {rel}")


def _print_apply(r: dict) -> None:
    frm, to = r["from_version"] or "unknown", r["to_version"] or "unknown"
    print(f"awow updated: {frm} -> {to}")
    print(f"  updated:   {len(r['updated'])}")
    print(f"  added:     {len(r['added'])}")
    print(f"  conflicts: {len(r['conflicts'])}")
    for rel in r["conflicts"]:
        print(f"    - {rel}.awow")
    if r["conflicts"]:
        print("\nMerge each .awow into your file, then delete the .awow.")
    print("\nNext: run `python tools/gather.py` to re-mirror the harness stubs.")


# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="target repo root (default: this repo)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_back = sub.add_parser("backfill", help="create/refresh the baseline from the local tree")
    retrofit = p_back.add_mutually_exclusive_group()
    retrofit.add_argument("--baseline-ref",
                          help="git ref of THIS repo to hash the baseline from "
                               "(the commit where awow was originally vendored)")
    retrofit.add_argument("--source", type=Path,
                          help="upstream awow clone; classify each local file by "
                               "matching it against the clone's full history")

    p_status = sub.add_parser("status", help="report version + drift (read-only)")
    p_status.add_argument("--source", type=Path, help="upstream awow clone / plugin root to compare against")
    p_status.add_argument("--json", action="store_true")

    p_apply = sub.add_parser("apply", help="apply the update against --source")
    p_apply.add_argument("--source", type=Path, required=True, help="upstream awow clone / plugin root")
    p_apply.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "backfill":
        return cmd_backfill(
            root,
            baseline_ref=args.baseline_ref,
            source=args.source.resolve() if args.source else None,
        )
    if args.cmd == "status":
        return cmd_status(root, args.source.resolve() if args.source else None, args.json)
    if args.cmd == "apply":
        return cmd_apply(root, args.source.resolve(), args.json)
    parser.error(f"unknown command {args.cmd}")


if __name__ == "__main__":
    sys.exit(main())
