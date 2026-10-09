#!/usr/bin/env python3
"""Export Claude Code sessions for one project into a human-readable dump.

Reads the per-session JSONL logs Claude Code keeps under
  ~/.claude/projects/<encoded-path>/<session-id>.jsonl
and renders each chosen session into a plain-text transcript matching the
`examples/aircraft-alert/_exports/` format, plus an INDEX.md and a manifest.json
that the `usage-analysis` skill consumes.

This is the data-collection half of claude-analyzer. The companion `build.py`
reads the same JSONL for timing/token metrics; this script produces the readable
transcripts a coach (human or model) actually reads.

Typical flow (driven by the session-export skill):
  1. list-projects   — find the project's session directory
  2. list-sessions   — see the menu of sessions, with sizes, to scope the dump
  3. export          — render the chosen sessions + INDEX.md + manifest.json

Examples:
  python3 export_sessions.py list-projects
  python3 export_sessions.py list-sessions --project-path ~/repos/myapp
  python3 export_sessions.py export --project-path ~/repos/myapp \
      --out exports/myapp --since 2026-05-01 --exclude /awow: --redact
  python3 export_sessions.py scan exports/myapp          # secret check only
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

PROJECTS_ROOT = os.path.expanduser("~/.claude/projects")
SEP = "=" * 70

# ---------------------------------------------------------------------------
# Secret detection — known credential shapes. Used to warn before a dump is
# shared and, with --redact, to replace the secret in-place. Kept deliberately
# narrow (known prefixes) so base64 image data and hashes aren't false-flagged.
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    # key=value assignments naming a secret (catches RAPIDAPI_KEY=…, api_key: …)
    ("named-secret-assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|rapidapi[_-]?key)\b"
        r"\s*[:=]\s*['\"]?([A-Za-z0-9_\-./+]{16,})['\"]?")),
]
# Obvious placeholders that should never be flagged.
_PLACEHOLDER = re.compile(r"(?i)\b(dummy|placeholder|example|redacted|your[_-]?key|xxx+|<[^>]+>)\b")


def scan_text(text):
    """Return a list of (pattern_name, matched_snippet) for likely secrets."""
    hits = []
    for name, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            snippet = m.group(0)
            if _PLACEHOLDER.search(snippet):
                continue
            # for the named-assignment pattern the value is group(1)
            value = m.group(1) if (name == "named-secret-assignment" and m.groups()) else snippet
            if _PLACEHOLDER.search(value):
                continue
            hits.append((name, snippet))
    return hits


def redact_text(text):
    """Replace detected secrets with a labelled placeholder. Returns (text, n)."""
    n = 0

    def _sub_factory(name):
        def _sub(m):
            nonlocal n
            snippet = m.group(0)
            if _PLACEHOLDER.search(snippet):
                return snippet
            n += 1
            if name == "named-secret-assignment" and m.groups():
                return snippet.replace(m.group(1), "«REDACTED-SECRET»")
            return "«REDACTED-SECRET»"
        return _sub

    for name, pat in SECRET_PATTERNS:
        text = pat.sub(_sub_factory(name), text)
    return text, n


# ---------------------------------------------------------------------------
# Project / session discovery
# ---------------------------------------------------------------------------
def encode_project_path(path):
    """Mirror Claude Code's project-dir naming: non-alphanumerics -> '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.path.expanduser(path)))


def decode_project_dir(name):
    """Best-effort reverse of the encoding (lossy — '-' is ambiguous). Used only
    for display in list-projects, so an approximate path is acceptable."""
    return "/" + name.strip("-").replace("-", "/")


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def fmt_ts(dt):
    """Human timestamp in UTC, matching the example dump format."""
    if dt is None:
        return "(unknown)"
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def resolve_project_dir(args):
    """Return the ~/.claude/projects/<x> directory for the requested project."""
    if getattr(args, "project_dir", None):
        d = os.path.expanduser(args.project_dir)
    elif getattr(args, "project_path", None):
        d = os.path.join(PROJECTS_ROOT, encode_project_path(args.project_path))
    else:
        raise SystemExit("error: provide --project-path or --project-dir")
    if not os.path.isdir(d):
        raise SystemExit(f"error: session directory not found: {d}\n"
                         f"run 'list-projects' to see available projects")
    return d


def iter_records(path):
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def summarize_session(path):
    """Lightweight pass: title, time span, real-prompt count. No rendering."""
    sid = os.path.basename(path)[:-len(".jsonl")]
    rec = {"id": sid, "short": sid[:8], "title": None, "start": None,
           "end": None, "prompts": 0, "messages": 0,
           "raw_bytes": os.path.getsize(path)}
    first_prompt = None
    for o in iter_records(path):
        if o.get("type") == "ai-title" and o.get("aiTitle"):
            rec["title"] = o["aiTitle"]
        ts = parse_ts(o.get("timestamp"))
        if ts:
            if rec["start"] is None or ts < rec["start"]:
                rec["start"] = ts
            if rec["end"] is None or ts > rec["end"]:
                rec["end"] = ts
        msg = o.get("message")
        if o.get("type") in ("user", "assistant") and isinstance(msg, dict) and not o.get("isMeta"):
            rec["messages"] += 1
            c = msg.get("content")
            if o.get("type") == "user" and isinstance(c, str) and c.strip():
                rec["prompts"] += 1
                if first_prompt is None:
                    first_prompt = c.strip()
    if not rec["title"]:
        rec["title"] = _clean_title(first_prompt) if first_prompt else "(untitled session)"
    return rec


def _clean_title(t):
    if not t:
        return "(untitled session)"
    t = re.sub(r"</?(?:local-)?command-[a-z]+>|</?command-args>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return (t[:70] or "(untitled session)")


# ---------------------------------------------------------------------------
# Transcript rendering
# ---------------------------------------------------------------------------
def _block_to_text(block):
    """Render one content block (assistant or user) to transcript text."""
    if not isinstance(block, dict):
        return str(block)
    bt = block.get("type")
    if bt == "text":
        return block.get("text", "")
    if bt == "thinking":
        return None  # extended-thinking blocks are dropped from the readable dump
    if bt == "tool_use":
        inp = block.get("input")
        try:
            pretty = json.dumps(inp, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            pretty = str(inp)
        return f"[tool_use: {block.get('name')}]\n{pretty}"
    if bt == "tool_result":
        content = block.get("content")
        if isinstance(content, list):
            parts = [p.get("text", "") if isinstance(p, dict) and p.get("type") == "text"
                     else ("[image]" if isinstance(p, dict) and p.get("type") == "image"
                           else str(p)) for p in content]
            body = "\n".join(parts)
        elif content is None:
            body = ""
        else:
            body = str(content)
        return f"[tool_result]\n{body}"
    if bt == "image":
        return "[image]"
    return json.dumps(block, ensure_ascii=False)


def render_session(path):
    """Render a full session JSONL into the plain-text transcript format."""
    sid = os.path.basename(path)[:-len(".jsonl")]
    start = None
    body_chunks = []
    for o in iter_records(path):
        ts = parse_ts(o.get("timestamp"))
        if ts and start is None:
            start = ts
        t = o.get("type")
        msg = o.get("message")
        if t not in ("user", "assistant") or not isinstance(msg, dict) or o.get("isMeta"):
            continue
        c = msg.get("content")
        if isinstance(c, str):
            text = c
        elif isinstance(c, list):
            rendered = [_block_to_text(b) for b in c]
            text = "\n\n".join(r for r in rendered if r)
        else:
            text = ""
        if not text.strip():
            continue
        header = f"{SEP}\n{t.upper()}  [{fmt_ts(ts)}]\n{SEP}"
        body_chunks.append(f"{header}\n{text}\n")
    transcript = f"# Session {sid}\nStarted: {fmt_ts(start)}\n\n" + "\n".join(body_chunks)
    return transcript


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_list_projects(args):
    entries = []
    for d in sorted(glob.glob(os.path.join(PROJECTS_ROOT, "*"))):
        if not os.path.isdir(d):
            continue
        jsonl = glob.glob(os.path.join(d, "*.jsonl"))
        if not jsonl:
            continue
        spans = [summarize_session(f)["start"] for f in jsonl]
        spans = [s for s in spans if s]
        rng = (f"{fmt_ts(min(spans))} .. {fmt_ts(max(spans))}" if spans else "(no timestamps)")
        entries.append((len(jsonl), os.path.basename(d), rng))
    if not entries:
        print(f"No projects with sessions found under {PROJECTS_ROOT}")
        return
    print(f"Projects under {PROJECTS_ROOT}:\n")
    for n, name, rng in sorted(entries, key=lambda e: e[1]):
        print(f"  {n:4d} sessions  {rng}")
        print(f"               dir: {name}")
        print(f"               ~path: {decode_project_dir(name)}\n")
    print("Pass the real path with --project-path, or the dir name with --project-dir.")


def _gather_sessions(args):
    project_dir = resolve_project_dir(args)
    files = sorted(glob.glob(os.path.join(project_dir, "*.jsonl")))
    sessions = [summarize_session(f) for f in files]
    sessions = [s for s in sessions if s["start"] is not None]
    sessions.sort(key=lambda s: s["start"])
    # path map for rendering
    by_id = {os.path.basename(f)[:-len(".jsonl")]: f for f in files}
    return project_dir, sessions, by_id


def _apply_filters(sessions, by_id, args):
    """Return (kept, excluded) honouring --since/--until/--sessions/--exclude."""
    since = _parse_date(args.since) if getattr(args, "since", None) else None
    until = _parse_date(args.until, end=True) if getattr(args, "until", None) else None
    only = None
    if getattr(args, "sessions", None):
        only = {s.strip() for s in args.sessions.split(",") if s.strip()}
    excludes = getattr(args, "exclude", None) or []

    kept, excluded = [], []
    for s in sessions:
        reason = None
        if since and s["start"] < since:
            reason = "before --since"
        elif until and s["start"] > until:
            reason = "after --until"
        elif only and s["id"] not in only and s["short"] not in only:
            reason = "not in --sessions"
        else:
            for ex in excludes:
                hay = render_session(by_id[s["id"]]) if ex.startswith("~") else (s["title"] or "")
                needle = ex[1:] if ex.startswith("~") else ex
                if needle in hay:
                    reason = f"matched --exclude {ex}"
                    break
        (excluded if reason else kept).append({**s, "_reason": reason})
    return kept, excluded


def _parse_date(s, end=False):
    dt = datetime.datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    if end and len(s) <= 10:  # date-only --until means end of that day
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt


def cmd_list_sessions(args):
    _, sessions, by_id = _gather_sessions(args)
    kept, excluded = _apply_filters(sessions, by_id, args)
    total_kb = sum(s["raw_bytes"] for s in kept) / 1024
    print(f"{len(kept)} session(s) in scope "
          f"({len(excluded)} filtered out), ~{total_kb:.0f} KB of raw logs:\n")
    print(f"  {'short':8}  {'started (UTC)':19}  {'prompts':>7}  {'KB':>5}  title")
    for s in kept:
        print(f"  {s['short']:8}  {fmt_ts(s['start']):19}  {s['prompts']:>7}  "
              f"{s['raw_bytes']/1024:>5.0f}  {s['title'][:60]}")
    if excluded:
        print(f"\nFiltered out ({len(excluded)}):")
        for s in excluded:
            print(f"  {s['short']:8}  {s['_reason']}  — {s['title'][:50]}")
    # token-cost hint for the analysis step (rough: ~4 chars/token of transcript)
    est_tokens = int(total_kb * 1024 / 4)
    print(f"\nFull-coaching read cost ≈ {est_tokens:,} input tokens "
          f"across {len(kept)} transcripts (rendered size differs from raw).")


def cmd_export(args):
    project_dir, sessions, by_id = _gather_sessions(args)
    kept, excluded = _apply_filters(sessions, by_id, args)
    if not kept:
        raise SystemExit("error: no sessions in scope after filters — nothing to export")

    out = os.path.expanduser(args.out)
    os.makedirs(out, exist_ok=True)

    project_path = (os.path.abspath(os.path.expanduser(args.project_path))
                    if getattr(args, "project_path", None) else None)

    manifest_sessions = []
    flagged = []  # (short, [(name, snippet)])
    total_bytes = 0
    for s in kept:
        transcript = render_session(by_id[s["id"]])
        hits = scan_text(transcript)
        n_redacted = 0
        if hits and args.redact:
            transcript, n_redacted = redact_text(transcript)
        elif hits:
            flagged.append((s["short"], hits))
        txt_path = os.path.join(out, s["id"] + ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(transcript)
        b = len(transcript.encode("utf-8"))
        total_bytes += b
        manifest_sessions.append({
            "id": s["id"], "short": s["short"], "start": s["start"].isoformat(),
            "title": s["title"], "prompts": s["prompts"], "messages": s["messages"],
            "bytes": b, "secrets_redacted": n_redacted,
        })

    # INDEX.md — dated, links each transcript (mirrors the example dump)
    title = args.title or (os.path.basename(project_path) if project_path else os.path.basename(out))
    index_lines = [f"# {title} — exported sessions", ""]
    for s in sorted(manifest_sessions, key=lambda x: x["start"]):
        index_lines.append(f"- {fmt_ts(parse_ts(s['start']))}  [{s['id']}.txt]({s['id']}.txt)")
    with open(os.path.join(out, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")

    # manifest.json — consumed by the usage-analysis skill
    manifest = {
        "title": title,
        "project_path": project_path,
        "project_dir": project_dir,
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "session_count": len(manifest_sessions),
        "total_bytes": total_bytes,
        "est_read_tokens": total_bytes // 4,
        "sessions": manifest_sessions,
        "excluded": [{"id": s["id"], "short": s["short"], "reason": s["_reason"]}
                     for s in excluded],
    }
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Exported {len(manifest_sessions)} session(s) to {out}/")
    print(f"  total transcript size: {total_bytes/1024:.0f} KB "
          f"(≈ {total_bytes//4:,} tokens to read in full coaching)")
    print(f"  wrote INDEX.md and manifest.json")
    if excluded:
        print(f"  filtered out {len(excluded)} session(s)")
    _report_secrets(flagged, redacted=args.redact, manifest_sessions=manifest_sessions)


def cmd_scan(args):
    """Scan an existing dump directory for secrets without re-exporting."""
    target = os.path.expanduser(args.dir)
    txts = sorted(glob.glob(os.path.join(target, "*.txt")))
    if not txts:
        raise SystemExit(f"no .txt transcripts found in {target}")
    flagged = []
    for p in txts:
        text = open(p, encoding="utf-8").read()
        hits = scan_text(text)
        if hits and args.redact:
            text, n = redact_text(text)
            with open(p, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"  redacted {n} secret(s) in {os.path.basename(p)}")
        elif hits:
            flagged.append((os.path.basename(p), hits))
    if args.redact:
        print("Redaction pass complete.")
    else:
        _report_secrets(flagged, redacted=False)


def _report_secrets(flagged, redacted, manifest_sessions=None):
    if redacted:
        n = sum(s.get("secrets_redacted", 0) for s in (manifest_sessions or []))
        if n:
            print(f"  ⚠ redacted {n} likely secret(s) across the dump (--redact)")
        else:
            print("  ✓ no secrets detected")
        return
    if not flagged:
        print("  ✓ no secrets detected by the scanner")
        return
    print("\n  ⚠ POTENTIAL SECRETS DETECTED — review before sharing this dump:")
    for who, hits in flagged:
        for name, snippet in hits[:5]:
            shown = snippet if len(snippet) < 60 else snippet[:57] + "…"
            print(f"    {who}: [{name}] {shown}")
    print("  Re-run with --redact to replace them with «REDACTED-SECRET», "
          "and rotate any real key.")


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    def add_project_args(p):
        g = p.add_mutually_exclusive_group(required=True)
        g.add_argument("--project-path", help="Real project path (encoded to find sessions)")
        g.add_argument("--project-dir", help="Direct ~/.claude/projects/<x> dir name or path")

    def add_filter_args(p):
        p.add_argument("--since", help="Only sessions starting on/after this date (YYYY-MM-DD)")
        p.add_argument("--until", help="Only sessions starting on/before this date (YYYY-MM-DD)")
        p.add_argument("--sessions", help="Comma-separated session ids/short-ids to include")
        p.add_argument("--exclude", action="append", default=[],
                       help="Drop sessions whose title contains SUBSTR; prefix '~' to match "
                            "transcript body (repeatable, e.g. --exclude ~/awow:)")

    p = sub.add_parser("list-projects", help="List projects that have sessions")
    p.set_defaults(func=cmd_list_projects)

    p = sub.add_parser("list-sessions", help="Show the session menu for a project")
    add_project_args(p)
    add_filter_args(p)
    p.set_defaults(func=cmd_list_sessions)

    p = sub.add_parser("export", help="Render chosen sessions to a dump directory")
    add_project_args(p)
    add_filter_args(p)
    p.add_argument("--out", required=True, help="Output directory for the dump")
    p.add_argument("--title", help="Human title for INDEX.md / manifest (default: project name)")
    p.add_argument("--redact", action="store_true",
                   help="Replace detected secrets with «REDACTED-SECRET» instead of warning")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("scan", help="Scan an existing dump dir for secrets")
    p.add_argument("dir", help="Dump directory to scan")
    p.add_argument("--redact", action="store_true", help="Redact in place instead of warning")
    p.set_defaults(func=cmd_scan)

    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
