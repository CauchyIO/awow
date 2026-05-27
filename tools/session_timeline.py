#!/usr/bin/env python3
"""Build an interactive timeline of a project's Claude Code sessions.

Reads the session JSONL files Claude Code stores under
~/.claude/projects/<encoded-path>/ and emits:
  - sessions.json  : one clean record per session (the reusable data layer)
  - timeline.html  : self-contained interactive view (vanilla JS + SVG; no server, no CDN)

The visual, zero-setup entry to awow's session analysis: unlike the trace path
(mlflow-export -> awow-usage-coach / prompt-skill-analysis), this needs no MLflow
or Databricks tracing wired up — it reads the raw Claude Code logs directly.
Claude Code only (Copilot has no equivalent local log). stdlib-only.

Usage:
  python tools/session_timeline.py --project-path <repo> --out .
  python tools/session_timeline.py --project-path <repo> --transcripts ./_exports \\
      --coach-dir ./coach_reviews --overview ./OVERVIEW.md --tz-offset 2
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


def load_session(path):
    sid = os.path.basename(path)[:-len(".jsonl")]
    rec = {
        "id": sid, "short": sid[:8], "title": None, "branch": None,
        "start": None, "end": None, "files": set(), "read_files": set(),
        "file_first": {}, "file_last": {},
        "edit_count": 0, "msg_count": 0, "tool_count": 0, "first_prompt": None,
        "peak_context": 0, "out_tokens": 0, "events": [],
    }
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
                c = msg.get("content")
                if (rec["first_prompt"] is None and t == "user"
                        and isinstance(c, str) and c.strip()):
                    rec["first_prompt"] = c.strip()[:200]
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_use":
                            rec["tool_count"] += 1
                            name = b.get("name")
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


def build(project_dir, project_root, transcripts_dir, coach_dir=None, overview_file=None):
    files = sorted(glob.glob(os.path.join(project_dir, "*.jsonl")))
    sessions = [load_session(f) for f in files]
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
        # functional area from edits, falling back to reads for research sessions
        basis = edited or read
        areas = collections.Counter(functional_area(f) for f in basis)
        dominant = areas.most_common(1)[0][0] if areas else "ops/other"
        out.append({
            "id": s["id"], "short": s["short"], "title": s["title"],
            "branch": s["branch"], "area": dominant,
            "areas": dict(areas),
            "readonly": s["edit_count"] == 0,
            "start": s["start"].isoformat(), "end": s["end"].isoformat(),
            "duration_min": round((s["end"] - s["start"]).total_seconds() / 60, 1),
            "files": edited, "read_files": read,
            "edit_count": s["edit_count"], "msg_count": s["msg_count"],
            "tool_count": s["tool_count"],
            "peak_context": s["peak_context"], "out_tokens": s["out_tokens"],
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

    return {
        "project_dir": project_dir, "root": root,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "sessions": out, "file_edges": file_edges, "topic_edges": topic_edges,
        "handoff_edges": handoff_edges, "overview": overview, "idle_gaps": idle_gaps,
    }


def find_transcript(transcripts_dir, sid):
    if not transcripts_dir:
        return None
    p = os.path.join(transcripts_dir, sid + ".txt")
    return p if os.path.exists(p) else None


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--project-path", help="Real project path; encoded to find sessions")
    g.add_argument("--project-dir", help="Direct path to the ~/.claude/projects/<x> dir")
    ap.add_argument("--project-root", help="Real repo path, to relativize files into areas "
                                           "(inferred from --project-path)")
    ap.add_argument("--transcripts", help="Dir of <session>.txt transcripts to link to")
    ap.add_argument("--coach-dir", help="Dir of <short>.md coach reviews to embed per session")
    ap.add_argument("--overview", help="Markdown file shown as the default 'overview' panel")
    ap.add_argument("--tz-offset", type=float, default=0.0,
                    help="Hours to add to the UTC logs for display (e.g. 2 for GMT+2). Default 0 (UTC).")
    ap.add_argument("--tz-label", default=None,
                    help="Timezone label shown in the view. Default derived from --tz-offset (UTC / GMT+N).")
    ap.add_argument("--context-window", type=int, default=200000,
                    help="Standard context window in tokens; sessions whose peak exceeds it are flagged. Default 200000.")
    ap.add_argument("--out", default=".", help="Output directory")
    args = ap.parse_args()

    off = args.tz_offset
    if args.tz_label:
        tz_label = args.tz_label
    elif off == 0:
        tz_label = "UTC"
    else:
        tz_label = f"GMT{'+' if off >= 0 else ''}{off:g}"

    if args.project_path:
        project_root = os.path.abspath(os.path.expanduser(args.project_path))
        project_dir = os.path.join(os.path.expanduser("~/.claude/projects"),
                                   encode_project_path(args.project_path))
    else:
        project_dir = os.path.expanduser(args.project_dir)
        project_root = os.path.abspath(os.path.expanduser(args.project_root)) if args.project_root else ""
    if not os.path.isdir(project_dir):
        raise SystemExit(f"Session dir not found: {project_dir}")

    transcripts = os.path.expanduser(args.transcripts) if args.transcripts else None
    coach = os.path.expanduser(args.coach_dir) if args.coach_dir else None
    overview = os.path.expanduser(args.overview) if args.overview else None
    data = build(project_dir, project_root, transcripts, coach, overview)
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

    print(f"{len(data['sessions'])} sessions, "
          f"{len(data['file_edges'])} shared-file edges, "
          f"{len(data['topic_edges'])} topic edges")
    print(f"wrote {json_path}")
    print(f"wrote {html_path}")


if __name__ == "__main__":
    main()
