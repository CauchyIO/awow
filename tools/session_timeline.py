#!/usr/bin/env python3
"""Build an interactive timeline + meta-analysis of a project's agent sessions.

Reads from one of two sources and emits the same data layer + view:
  - Claude Code logs under ~/.claude/projects/<encoded-path>/ (--project-path),
  - an mlflow_export/ dir of Databricks traces (--mlflow-export), which supports
    multiple users and is the path the mlflow-export skill produces.
Outputs:
  - sessions.json : one clean record per session (the reusable data layer)
  - timeline.html : self-contained interactive view (no server, no CDN)

The visual, zero-setup entry to awow's session analysis, driven by the
/project-retrospective command. stdlib-only. The multi-day calendar view engages
automatically when sessions span more than one day.

Usage:
  python tools/session_timeline.py --project-path <repo> --out <dir> --tz-offset 2
  python tools/session_timeline.py --mlflow-export <mlflow_export-dir> --out <dir>
  python tools/session_timeline.py --project-path <repo> --transcripts <dir-with-*.txt> \
      --coach-dir <dir-with-reviews> --overview <overview.md> --out <dir>

Route all output to the gitignored coach_reviews/ — it is private session data.
"""
import argparse, collections, glob, json, os, re, datetime, html

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
STOP = set("the a an and or to of for in on with into from this that is are be "
           "i you it we they fix add use using make build set get app run new "
           "claude code session project file files screen page based".split())


def encode_project_path(path):
    """Mirror Claude Code's project-dir naming: non-alphanumerics -> '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.path.expanduser(path)))


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def clean_title(t):
    """Strip slash-command markup and collapse whitespace from a session title."""
    if not t:
        return t
    t = re.sub(r"<command-[a-z]+>|</command-[a-z]+>|<local-command-[a-z]+>|"
               r"</local-command-[a-z]+>|<command-args>|</command-args>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t or "(untitled session)"


def tokenize(text):
    toks = re.findall(r"[a-zA-Z][a-zA-Z0-9]+", (text or "").lower())
    return {t for t in toks if t not in STOP and len(t) > 2}


READ_TOOLS = {"Read", "Grep", "Glob"}


def new_record(sid):
    """The normalized session record every source loader produces.
    Downstream build() depends only on these keys; loaders fill what their
    source can supply (Claude logs fill files; MLflow leaves them empty)."""
    return {
        "id": sid, "short": sid[:8], "title": None, "branch": None,
        "start": None, "end": None, "files": set(), "read_files": set(),
        "file_first": {}, "file_last": {},
        "edit_count": 0, "msg_count": 0, "tool_count": 0, "first_prompt": None,
        "peak_context": 0, "out_tokens": 0, "events": [],
        "in_tokens": 0, "cache_read": 0, "cache_write": 0,
        "user": None, "working_directory": None, "tools": {},
    }


def load_session(path):
    """Load one Claude Code session JSONL into a normalized record."""
    sid = os.path.basename(path)[:-len(".jsonl")]
    rec = new_record(sid)
    branch_counts = {}
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = o.get("type")
            if t == "ai-title" and o.get("aiTitle"):
                rec["title"] = o["aiTitle"]
            br = o.get("gitBranch")
            if br:
                branch_counts[br] = branch_counts.get(br, 0) + 1
            if rec["working_directory"] is None and o.get("cwd"):
                rec["working_directory"] = o["cwd"]
            ts = parse_ts(o.get("timestamp"))
            if ts:
                if rec["start"] is None or ts < rec["start"]:
                    rec["start"] = ts
                if rec["end"] is None or ts > rec["end"]:
                    rec["end"] = ts
            msg = o.get("message")
            if t in ("user", "assistant") and isinstance(msg, dict) and not o.get("isMeta"):
                rec["msg_count"] += 1
                if ts:
                    rec["events"].append(ts)
                if t == "assistant":
                    u = msg.get("usage") or {}
                    if u:
                        # full prompt size at this turn = how much context was in play
                        ctx = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                               + u.get("cache_creation_input_tokens", 0))
                        rec["peak_context"] = max(rec["peak_context"], ctx)
                        rec["out_tokens"] += u.get("output_tokens", 0)
                        # cumulative token usage across the session, broken out by kind:
                        # fresh input ("read"), output ("write"), and the two cache buckets
                        rec["in_tokens"] += u.get("input_tokens", 0)
                        rec["cache_read"] += u.get("cache_read_input_tokens", 0)
                        rec["cache_write"] += u.get("cache_creation_input_tokens", 0)
                c = msg.get("content")
                if (rec["first_prompt"] is None and t == "user"
                        and isinstance(c, str) and c.strip()):
                    rec["first_prompt"] = c.strip()[:200]
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_use":
                            rec["tool_count"] += 1
                            name = b.get("name")
                            if name:
                                rec["tools"][name] = rec["tools"].get(name, 0) + 1
                            inp = b.get("input") or {}
                            fp = inp.get("file_path") or inp.get("path") or inp.get("notebook_path")
                            if name in EDIT_TOOLS and fp:
                                rec["files"].add(fp)
                                rec["edit_count"] += 1
                                if ts:  # track first/last edit time per file for handoff inference
                                    if fp not in rec["file_first"] or ts < rec["file_first"][fp]:
                                        rec["file_first"][fp] = ts
                                    if fp not in rec["file_last"] or ts > rec["file_last"][fp]:
                                        rec["file_last"][fp] = ts
                            elif name in READ_TOOLS and fp:
                                rec["read_files"].add(fp)
    rec["branch"] = max(branch_counts, key=branch_counts.get) if branch_counts else "(none)"
    rec["title"] = clean_title(rec["title"] or (rec["first_prompt"] or "(untitled session)")[:60])
    return rec


def functional_area(rel_path):
    """Top-level area within the project: 'ios/', 'docs/', or 'core' for root files."""
    if rel_path.startswith("../") or rel_path.startswith("/"):
        return "external"
    parts = rel_path.split("/")
    return parts[0] + "/" if len(parts) > 1 else "core"


def ms_to_dt(ms):
    """Epoch milliseconds (int/float/str) -> aware UTC datetime, or None."""
    if ms is None:
        return None
    try:
        return datetime.datetime.fromtimestamp(int(ms) / 1000, tz=datetime.timezone.utc)
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def _user_local(u):
    """Normalize a user to its local-part: 'casper@cauchy.io' -> 'casper'."""
    return (u or "").split("@")[0] or None


def load_from_mlflow_export(export_dir, user_filter=None):
    """Load an mlflow_export/ dir (traces.jsonl) into normalized session records.

    A trace is one whole Claude conversation (spans = llm_call_N + tool_<Name>),
    grouped into sessions by trace_metadata['mlflow.trace.session']. Spans in
    current exports carry only a name (the span body fails to serialize), so file
    paths and per-span timing are unavailable — files stay empty and the area is
    derived from the working directory. Tokens come from info.tags (schema v3),
    falling back to trace_metadata['mlflow.trace.tokenUsage'] (older schema).
    """
    traces_path = os.path.join(export_dir, "traces.jsonl")
    if not os.path.isfile(traces_path):
        raise SystemExit(f"No traces.jsonl in {export_dir} — not an mlflow_export dir")

    sessions = {}
    with open(traces_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                tr = json.loads(line)
            except json.JSONDecodeError:
                continue
            info = tr.get("info") or {}
            meta = info.get("trace_metadata") or {}
            tags = info.get("tags") or {}

            user = meta.get("mlflow.user") or meta.get("mlflow.trace.user") or tags.get("mlflow.user")
            if user_filter and _user_local(user) != _user_local(user_filter):
                continue

            sid = (meta.get("mlflow.trace.session") or tags.get("mlflow.trace.session")
                   or info.get("client_request_id") or info.get("trace_id") or "unknown")
            rec = sessions.get(sid)
            if rec is None:
                rec = new_record(sid)
                sessions[sid] = rec

            start = ms_to_dt(info.get("request_time"))
            dur_ms = info.get("execution_duration") or 0
            end = ms_to_dt((info.get("request_time") or 0) + (dur_ms or 0)) if start else None
            for ev in (start, end):
                if ev:
                    rec["events"].append(ev)
                    if rec["start"] is None or ev < rec["start"]:
                        rec["start"] = ev
                    if rec["end"] is None or ev > rec["end"]:
                        rec["end"] = ev

            if rec["user"] is None and user:
                rec["user"] = _user_local(user)
            wd = meta.get("mlflow.trace.working_directory")
            if rec["working_directory"] is None and wd:
                rec["working_directory"] = wd
            br = tags.get("git.branch") or meta.get("mlflow.source.git.branch")
            if br:
                rec["branch"] = br

            # tokens: tags (schema v3) first, then the older tokenUsage blob
            def _tok(key_tag, *meta_keys):
                v = tags.get(key_tag)
                if v is None:
                    tu = _parse_json(meta.get("mlflow.trace.tokenUsage"))
                    for mk in meta_keys:
                        if isinstance(tu, dict) and tu.get(mk) is not None:
                            v = tu.get(mk)
                            break
                try:
                    return int(v)
                except (TypeError, ValueError):
                    return 0

            rec["in_tokens"] += _tok("tokens.input", "input_tokens")
            rec["out_tokens"] += _tok("tokens.output", "output_tokens")
            rec["cache_read"] += _tok("tokens.cache_read", "cache_read_input_tokens")
            rec["cache_write"] += _tok("tokens.cache_creation", "cache_creation_input_tokens")
            # NOTE: MLflow tags are CUMULATIVE per trace (cache_read sums every turn's
            # re-read of the prompt), so they measure cost, not the per-turn context
            # window. peak_context is left 0 (unknown) for MLflow — unlike Claude logs,
            # where it's a true per-turn maximum.

            # spans: count turns (llm_call*) and tools (tool_<Name>)
            for sp in tr.get("spans") or []:
                name = sp.get("name") if isinstance(sp, dict) else None
                if not name:
                    continue
                if name.startswith("tool_"):
                    tool = name[len("tool_"):]
                    rec["tool_count"] += 1
                    rec["tools"][tool] = rec["tools"].get(tool, 0) + 1
                    # opportunistic: a fixed export may carry file paths in attributes
                    attrs = sp.get("attributes") or {}
                    fp = attrs.get("file_path") or attrs.get("path")
                    if tool in EDIT_TOOLS and fp:
                        rec["files"].add(fp)
                        rec["edit_count"] += 1
                    elif tool in READ_TOOLS and fp:
                        rec["read_files"].add(fp)
                elif name.startswith("llm_call"):
                    rec["msg_count"] += 1

            # title: first conversation's prompt
            if rec["first_prompt"] is None:
                ti = _parse_json(meta.get("mlflow.traceInputs"))
                if isinstance(ti, dict) and ti.get("prompt"):
                    rec["first_prompt"] = str(ti["prompt"]).strip()[:200]

    out = []
    for rec in sessions.values():
        if rec["start"] is None:
            continue
        if rec["msg_count"] == 0:
            rec["msg_count"] = 1  # at least the conversation itself
        rec["branch"] = rec["branch"] or "(none)"
        rec["title"] = clean_title(rec["title"] or (rec["first_prompt"] or "(untitled session)")[:60])
        out.append(rec)
    return out


def _parse_json(s):
    if not s:
        return None
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return None


def load_coach_review(coach_dir, short):
    """Return the per-session coach review (raw markdown) if one exists, else None.
    Reviews for sessions excluded from the analysis live in <coach_dir>/excluded/
    and are flagged so the view can label them."""
    if not coach_dir:
        return None
    main_p = os.path.join(coach_dir, short + ".md")
    excl_p = os.path.join(coach_dir, "excluded", short + ".md")
    if os.path.exists(main_p):
        return {"md": open(main_p, encoding="utf-8").read(), "excluded": False, "path": main_p}
    if os.path.exists(excl_p):
        return {"md": open(excl_p, encoding="utf-8").read(), "excluded": True, "path": excl_p}
    return None


def build(sessions, project_dir, project_root, transcripts_dir, coach_dir=None,
          overview_file=None, source="claude-logs"):
    """Compute edges/idle/totals and assemble the data layer from pre-loaded,
    normalized session records (from any source loader)."""
    sessions = [s for s in sessions if s["start"] is not None]
    # When a transcript dir is given, scope to that exported snapshot — keeps the
    # view stable and excludes unrelated/live sessions still being written.
    if transcripts_dir:
        sessions = [s for s in sessions if find_transcript(transcripts_dir, s["id"])]
    sessions.sort(key=lambda s: s["start"])

    root = os.path.abspath(os.path.expanduser(project_root)) if project_root else ""

    def rel(fp):
        if root and fp.startswith(root):
            return fp[len(root):].lstrip("/") or os.path.basename(fp)
        return os.path.relpath(fp, root) if root else fp

    # shared-file edges (weight = number of files both sessions edited)
    file_edges = []
    for i in range(len(sessions)):
        for j in range(i + 1, len(sessions)):
            shared = sessions[i]["files"] & sessions[j]["files"]
            if shared:
                file_edges.append({"source": i, "target": j, "weight": len(shared),
                                   "files": sorted(rel(f) for f in shared)})

    # topic-similarity edges (Jaccard of title+filename tokens >= threshold)
    tok = [tokenize(s["title"]) | {t for f in s["files"] for t in tokenize(os.path.basename(f))}
           for s in sessions]
    topic_edges = []
    for i in range(len(sessions)):
        for j in range(i + 1, len(sessions)):
            a, b = tok[i], tok[j]
            if not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            if jac >= 0.18:
                topic_edges.append({"source": i, "target": j,
                                   "weight": round(jac, 3),
                                   "shared": sorted(a & b)[:8]})

    # inferred handoff DAG, per-file last-writer:
    # for each file B edits, link back to whoever most recently edited THAT file
    # before B first touched it. Aggregates to one directed edge per (predecessor, B).
    # This is temporally sound and avoids the "huge session claims everything" bias.
    handoff = collections.defaultdict(lambda: {"files": [], "anchor": None})
    for j, b in enumerate(sessions):
        for f, b_first in b["file_first"].items():
            best_i, best_t = None, None
            for i, a in enumerate(sessions):
                if i == j or f not in a["file_last"]:
                    continue
                if a["file_last"][f] < b_first and (best_t is None or a["file_last"][f] > best_t):
                    best_t, best_i = a["file_last"][f], i
            if best_i is not None:
                ent = handoff[(best_i, j)]
                ent["files"].append(rel(f))
                # anchor the arrow at the predecessor's last edit of the earliest such file
                if ent["anchor"] is None or best_t < ent["anchor"]:
                    ent["anchor"] = best_t
    handoff_edges = []
    for (i, j), ent in handoff.items():
        handoff_edges.append({
            "source": i, "target": j, "weight": len(ent["files"]),
            "anchor": ent["anchor"].isoformat(),
            "gap_min": round((sessions[j]["start"] - ent["anchor"]).total_seconds() / 60, 1),
            "shared": sorted(ent["files"])[:8],
        })
    handoff_edges.sort(key=lambda e: (e["source"], e["target"]))

    out = []
    for s in sessions:
        edited = sorted(rel(f) for f in s["files"])
        read = sorted(rel(f) for f in s["read_files"])
        # functional area from edits, falling back to reads for research sessions.
        # When no file data exists (e.g. MLflow traces), fall back to the working
        # directory's basename so bars still group/colour meaningfully.
        basis = edited or read
        areas = collections.Counter(functional_area(f) for f in basis)
        if areas:
            dominant = areas.most_common(1)[0][0]
        elif s.get("working_directory"):
            dominant = os.path.basename(s["working_directory"].rstrip("/")) + "/"
            areas = collections.Counter({dominant: 1})
        else:
            dominant = "ops/other"
        out.append({
            "id": s["id"], "short": s["short"], "title": s["title"],
            "branch": s["branch"], "area": dominant,
            "areas": dict(areas),
            "user": s.get("user"), "working_directory": s.get("working_directory"),
            "tools": dict(sorted(s.get("tools", {}).items(), key=lambda kv: -kv[1])),
            # MLflow traces don't expose edits, so "read-only" can't be inferred there
            "readonly": (s["edit_count"] == 0) if source != "mlflow" else False,
            "start": s["start"].isoformat(), "end": s["end"].isoformat(),
            "duration_min": round((s["end"] - s["start"]).total_seconds() / 60, 1),
            "files": edited, "read_files": read,
            "edit_count": s["edit_count"], "msg_count": s["msg_count"],
            "tool_count": s["tool_count"],
            "peak_context": s["peak_context"], "out_tokens": s["out_tokens"],
            "in_tokens": s["in_tokens"], "cache_read": s["cache_read"],
            "cache_write": s["cache_write"],
            "transcript": find_transcript(transcripts_dir, s["id"]),
            "coach": load_coach_review(coach_dir, s["short"]),
        })
    # True idle gaps: stretches where NO session logged any event — i.e. all open
    # sessions were waiting on the human. Interval coverage hides these (a session
    # left open spans the gap), so we look at the spacing between actual events.
    IDLE_MIN = 8  # minutes; below this is normal think/run time, not "away"
    allev = sorted(t for s in sessions for t in s["events"])
    idle_gaps = []
    for a, b in zip(allev, allev[1:]):
        mins = (b - a).total_seconds() / 60
        if mins >= IDLE_MIN:
            idle_gaps.append({"start": a.isoformat(), "end": b.isoformat(), "min": round(mins)})

    overview = ""
    if overview_file and os.path.exists(overview_file):
        overview = open(overview_file, encoding="utf-8").read()

    # project-wide token totals across every included session
    totals = {
        "in_tokens": sum(s["in_tokens"] for s in out),
        "out_tokens": sum(s["out_tokens"] for s in out),
        "cache_read": sum(s["cache_read"] for s in out),
        "cache_write": sum(s["cache_write"] for s in out),
    }
    # per-user rollup (distinct users + their session counts); drives the view's
    # colour-by-user mode. For Claude logs this is usually a single (or null) user.
    user_counts = collections.Counter(s["user"] for s in out if s.get("user"))
    users = [{"user": u, "sessions": n} for u, n in user_counts.most_common()]

    return {
        "project_dir": project_dir, "root": root, "source": source,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "sessions": out, "file_edges": file_edges, "topic_edges": topic_edges,
        "handoff_edges": handoff_edges, "overview": overview, "idle_gaps": idle_gaps,
        "totals": totals, "users": users,
    }


def find_transcript(transcripts_dir, sid):
    if not transcripts_dir:
        return None
    p = os.path.join(transcripts_dir, sid + ".txt")
    return p if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--project-path", help="Real project path; encoded to find Claude Code sessions")
    g.add_argument("--project-dir", help="Direct path to the ~/.claude/projects/<x> dir")
    g.add_argument("--mlflow-export", help="Path to an mlflow_export dir (traces.jsonl) to analyse instead")
    ap.add_argument("--project-root", help="Real repo path, to relativize files into areas "
                                           "(inferred from --project-path)")
    ap.add_argument("--user", help="Filter to one user (matches mlflow.user, local-part or email)")
    ap.add_argument("--transcripts", help="Dir of <session>.txt transcripts to link to")
    ap.add_argument("--coach-dir", help="Dir of <short>.md coach reviews to embed per session")
    ap.add_argument("--overview", help="Markdown file shown as the default 'overview' panel")
    ap.add_argument("--tz-offset", type=float, default=0.0,
                    help="Hours to add to the UTC logs for display (e.g. 2 for GMT+2). Default 0 (UTC).")
    ap.add_argument("--tz-label", default=None,
                    help="Timezone label shown in the view. Default derived from --tz-offset.")
    ap.add_argument("--context-window", type=int, default=200000,
                    help="Standard context window; sessions whose peak exceeds it are flagged. Default 200000.")
    ap.add_argument("--out", default=".", help="Output directory")
    args = ap.parse_args()

    off = args.tz_offset
    if args.tz_label:
        tz_label = args.tz_label
    elif off == 0:
        tz_label = "UTC"
    else:
        tz_label = f"GMT{'+' if off >= 0 else ''}{off:g}"

    project_root = ""
    if args.mlflow_export:
        source = "mlflow"
        export_dir = os.path.expanduser(args.mlflow_export)
        if not os.path.isdir(export_dir):
            raise SystemExit(f"mlflow_export dir not found: {export_dir}")
        sessions = load_from_mlflow_export(export_dir, user_filter=args.user)
        project_dir = export_dir
    else:
        source = "claude-logs"
        if args.project_path:
            project_root = os.path.abspath(os.path.expanduser(args.project_path))
            project_dir = os.path.join(os.path.expanduser("~/.claude/projects"),
                                       encode_project_path(args.project_path))
        else:
            project_dir = os.path.expanduser(args.project_dir)
            project_root = (os.path.abspath(os.path.expanduser(args.project_root))
                            if args.project_root else "")
        if not os.path.isdir(project_dir):
            raise SystemExit(f"Session dir not found: {project_dir}")
        files = sorted(glob.glob(os.path.join(project_dir, "*.jsonl")))
        sessions = [load_session(f) for f in files]
        if args.user:  # Claude logs rarely carry a user, but honour the filter if set
            sessions = [s for s in sessions if _user_local(s.get("user")) == _user_local(args.user)]

    transcripts = os.path.expanduser(args.transcripts) if args.transcripts else None
    coach = os.path.expanduser(args.coach_dir) if args.coach_dir else None
    overview = os.path.expanduser(args.overview) if args.overview else None
    data = build(sessions, project_dir, project_root, transcripts, coach, overview, source=source)
    os.makedirs(args.out, exist_ok=True)

    json_path = os.path.join(args.out, "sessions.json")
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    tmpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_timeline_template.html")
    with open(tmpl_path) as f:
        tmpl = f.read()
    html_out = (tmpl
                .replace("/*__DATA__*/null", json.dumps(data))
                .replace("__GENERATED__", html.escape(data["generated"]))
                .replace("__TZ_OFFSET_HOURS__", repr(off))
                .replace("__TZ_LABEL__", tz_label)
                .replace("__CTX_WINDOW__", str(args.context_window)))
    html_path = os.path.join(args.out, "timeline.html")
    with open(html_path, "w") as f:
        f.write(html_out)

    print(f"[{source}] {len(data['sessions'])} sessions, "
          f"{len(data['file_edges'])} shared-file edges, "
          f"{len(data['topic_edges'])} topic edges"
          + (f", {len(data['users'])} users" if data['users'] else ""))
    print(f"wrote {json_path}")
    print(f"wrote {html_path}")


if __name__ == "__main__":
    main()
