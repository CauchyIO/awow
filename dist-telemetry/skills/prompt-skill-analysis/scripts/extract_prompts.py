"""
Normalize a Claude Code session into a single JSON document of prompts + stats.

Accepts either:
  - a raw Claude Code session JSONL file (one record per line: user/assistant/system/...)
  - an mlflow_export directory produced by the mlflow-export skill (traces.jsonl + manifest.json)

Writes a single JSON file with a uniform shape that the calling model can read
and turn into a markdown prompt-skill assessment. The script computes objective
stats only (counts, length distributions, simple regex flags). Qualitative
judgments are left to the model.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

QUESTION_RE = re.compile(r"\?")
CORRECTION_RE = re.compile(
    r"\b(no|nope|actually|wait|stop|don'?t|not that|i meant|never mind|nvm|undo|revert)\b",
    re.I,
)
POLITE_RE = re.compile(r"\b(please|thanks|thank you|thx|appreciate)\b", re.I)
EMPHATIC_RE = re.compile(r"(!!|\?\?|!\?|\?!)")
IMPERATIVE_OPENERS = {
    "add", "build", "create", "delete", "deploy", "do", "fix", "generate",
    "implement", "make", "merge", "move", "open", "push", "remove", "rename",
    "run", "save", "set", "show", "start", "stop", "switch", "update", "use",
    "write", "commit", "test", "check", "go",
}
TICKET_RE = re.compile(r"\b(CAU|LIN|JIRA|ENG|INF|SEC)-\d+\b", re.I)
FILE_REF_RE = re.compile(
    r"(?:[A-Za-z0-9_./-]+\.(?:py|tf|md|json|yaml|yml|toml|sh|js|ts|tsx|jsx|sql|ipynb|html|css|csv|txt|cfg|ini|env))"
    r"|(?:[A-Za-z0-9_-]+\.(?:py|tf|md|json|yaml|yml|toml|sh|js|ts|tsx|jsx|sql))"
)
URL_RE = re.compile(r"https?://\S+")


def first_word(text: str) -> str:
    text = text.strip().lstrip("*-#>0123456789.) ")
    if not text:
        return ""
    return re.split(r"[\s,;:]", text, maxsplit=1)[0].lower()


def words(text: str) -> int:
    return len(text.split())


def safe_iso(ms_or_iso) -> str:
    if ms_or_iso is None:
        return ""
    if isinstance(ms_or_iso, (int, float)):
        try:
            return datetime.fromtimestamp(ms_or_iso / 1000, tz=timezone.utc).isoformat()
        except Exception:
            return str(ms_or_iso)
    return str(ms_or_iso)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def load_raw_jsonl(path: Path):
    """Parse a raw Claude Code session JSONL file.

    Returns one synthetic 'session' (the file is a single session) with
    chronological prompts.
    """
    prompts = []
    tool_calls = {}  # id -> name
    session_id = path.stem
    cwd = ""
    git_branch = ""
    first_ts = ""
    last_ts = ""

    # Pass 1: index tool_use blocks so we can match tool_results to a tool name
    with path.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") == "assistant":
                content = rec.get("message", {}).get("content")
                if isinstance(content, list):
                    for blk in content:
                        if isinstance(blk, dict) and blk.get("type") == "tool_use":
                            tool_calls[blk.get("id")] = blk.get("name", "?")

    # Pass 2: walk turns
    pending_user = None  # the last real user prompt awaiting a response
    last_tools = []      # tool names called by the assistant before the next user turn
    response_buf = []    # assistant text segments since last user prompt

    def flush_user():
        nonlocal pending_user, last_tools, response_buf
        if pending_user is not None:
            pending_user["response_excerpt"] = " ".join(response_buf)[:600]
            pending_user["tools"] = list(last_tools)
            prompts.append(pending_user)
        pending_user = None
        last_tools = []
        response_buf = []

    with path.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = rec.get("type")
            ts = rec.get("timestamp", "")
            if ts:
                first_ts = first_ts or ts
                last_ts = ts
            if not cwd:
                cwd = rec.get("cwd", "") or cwd
            if not git_branch:
                git_branch = rec.get("gitBranch", "") or git_branch

            if t == "user":
                content = rec.get("message", {}).get("content")
                user_text = None
                if isinstance(content, str):
                    user_text = content
                elif isinstance(content, list):
                    text_blocks = [b for b in content if isinstance(b, dict) and b.get("type") == "text"]
                    if text_blocks:
                        user_text = "\n".join(b.get("text", "") for b in text_blocks)
                if user_text is not None:
                    flush_user()
                    pending_user = {
                        "i": len(prompts),
                        "ts": ts,
                        "text": user_text,
                    }

            elif t == "assistant":
                content = rec.get("message", {}).get("content")
                if not isinstance(content, list):
                    continue
                for blk in content:
                    if not isinstance(blk, dict):
                        continue
                    bt = blk.get("type")
                    if bt == "text":
                        response_buf.append(blk.get("text", ""))
                    elif bt == "tool_use":
                        last_tools.append(blk.get("name", "?"))

    flush_user()

    sessions = [
        {
            "session_id": session_id,
            "source_path": str(path),
            "working_directory": cwd,
            "git_branch": git_branch,
            "git_remote_url": "",
            "first_time": first_ts,
            "last_time": last_ts,
            "prompts": prompts,
        }
    ]
    return sessions


def load_mlflow_export(directory: Path):
    """Parse an mlflow_export directory."""
    traces_path = directory / "traces.jsonl"
    manifest_path = directory / "manifest.json"
    if not traces_path.exists():
        raise SystemExit(f"traces.jsonl not found in {directory}")

    sessions: dict[str, dict] = {}

    with traces_path.open() as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            info = rec.get("info", {}) or {}
            tags = info.get("tags", {}) or {}
            meta = info.get("trace_metadata", {}) or {}

            session_id = (
                tags.get("mlflow.trace.session")
                or meta.get("mlflow.trace.session")
                or info.get("client_request_id")
                or "unknown"
            )

            try:
                req = json.loads(rec.get("request", "{}"))
            except Exception:
                req = {}
            try:
                resp = json.loads(rec.get("response", "{}"))
            except Exception:
                resp = {}

            prompt_text = req.get("prompt", "") if isinstance(req, dict) else str(req)
            response_text = resp.get("response", "") if isinstance(resp, dict) else str(resp)

            try:
                token_usage = json.loads(meta.get("mlflow.trace.tokenUsage", "{}"))
            except Exception:
                token_usage = {}

            tools = []
            for span in rec.get("spans", []) or []:
                name = span.get("name", "") if isinstance(span, dict) else ""
                if name.startswith("tool_"):
                    tools.append(name[len("tool_"):])

            sess = sessions.setdefault(
                session_id,
                {
                    "session_id": session_id,
                    "source_path": str(traces_path),
                    "working_directory": meta.get("mlflow.trace.working_directory")
                    or tags.get("mlflow.trace.working_directory", ""),
                    "git_branch": tags.get("git.branch", ""),
                    "git_remote_url": tags.get("git.remote_url", ""),
                    "first_time": None,
                    "last_time": None,
                    "prompts": [],
                },
            )
            sess["prompts"].append(
                {
                    "i": -1,  # filled after sort
                    "ts": safe_iso(info.get("request_time")),
                    "request_time_ms": info.get("request_time"),
                    "execution_duration_ms": info.get("execution_duration"),
                    "text": prompt_text,
                    "response_excerpt": (response_text or "")[:600],
                    "tools": tools,
                    "tokens": {
                        "input": token_usage.get("input_tokens"),
                        "output": token_usage.get("output_tokens"),
                        "total": token_usage.get("total_tokens"),
                    },
                }
            )

    out = []
    for sid, sess in sessions.items():
        sess["prompts"].sort(key=lambda p: p.get("request_time_ms") or 0)
        for i, p in enumerate(sess["prompts"]):
            p["i"] = i
        if sess["prompts"]:
            sess["first_time"] = sess["prompts"][0]["ts"]
            sess["last_time"] = sess["prompts"][-1]["ts"]
        out.append(sess)

    out.sort(key=lambda s: s["first_time"] or "")
    return out


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def classify_prompt(text: str) -> dict:
    text = text or ""
    stripped = text.strip()
    fw = first_word(stripped)
    return {
        "words": words(stripped),
        "chars": len(stripped),
        "is_question": bool(QUESTION_RE.search(stripped)),
        "is_imperative_opener": fw in IMPERATIVE_OPENERS,
        "has_correction_marker": bool(CORRECTION_RE.search(stripped)),
        "is_polite": bool(POLITE_RE.search(stripped)),
        "is_emphatic": bool(EMPHATIC_RE.search(stripped)),
        "has_ticket_ref": bool(TICKET_RE.search(stripped)),
        "has_file_ref": bool(FILE_REF_RE.search(stripped)),
        "has_url": bool(URL_RE.search(stripped)),
        "has_code_fence": "```" in stripped,
        "has_numbered_structure": bool(re.search(r"(?m)^\s*\d+[\.\)]\s", stripped)),
        "first_word": fw,
    }


def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def compute_stats(sessions):
    all_prompts = [p for s in sessions for p in s["prompts"]]
    n = len(all_prompts)
    if n == 0:
        return {"total_prompts": 0, "total_sessions": len(sessions)}

    classified = [classify_prompt(p["text"]) for p in all_prompts]
    word_counts = [c["words"] for c in classified]

    def pct(key):
        return round(sum(1 for c in classified if c[key]) / n, 3)

    tool_counter = Counter()
    for p in all_prompts:
        for t in p.get("tools", []):
            tool_counter[t] += 1

    first_words = Counter(c["first_word"] for c in classified if c["first_word"])

    # Inter-prompt gaps (per session)
    gaps_seconds = []
    for s in sessions:
        ts_list = []
        for p in s["prompts"]:
            ms = p.get("request_time_ms")
            if ms is None and p.get("ts"):
                try:
                    ms = int(datetime.fromisoformat(p["ts"].replace("Z", "+00:00")).timestamp() * 1000)
                except Exception:
                    ms = None
            ts_list.append(ms)
        for i in range(1, len(ts_list)):
            if ts_list[i] is not None and ts_list[i - 1] is not None:
                gaps_seconds.append((ts_list[i] - ts_list[i - 1]) / 1000)

    in_tokens = [p.get("tokens", {}).get("input") for p in all_prompts if p.get("tokens")]
    out_tokens = [p.get("tokens", {}).get("output") for p in all_prompts if p.get("tokens")]
    in_tokens = [x for x in in_tokens if isinstance(x, (int, float))]
    out_tokens = [x for x in out_tokens if isinstance(x, (int, float))]

    return {
        "total_sessions": len(sessions),
        "total_prompts": n,
        "prompt_words": {
            "min": min(word_counts),
            "p25": round(percentile(word_counts, 0.25), 1),
            "median": round(statistics.median(word_counts), 1),
            "p75": round(percentile(word_counts, 0.75), 1),
            "max": max(word_counts),
            "mean": round(statistics.mean(word_counts), 1),
        },
        "share": {
            "questions": pct("is_question"),
            "imperative_openers": pct("is_imperative_opener"),
            "correction_markers": pct("has_correction_marker"),
            "polite": pct("is_polite"),
            "emphatic": pct("is_emphatic"),
            "ticket_refs": pct("has_ticket_ref"),
            "file_refs": pct("has_file_ref"),
            "urls": pct("has_url"),
            "code_fence": pct("has_code_fence"),
            "numbered_structure": pct("has_numbered_structure"),
            "very_short_le5_words": round(sum(1 for w in word_counts if w <= 5) / n, 3),
            "terse_le10_words": round(sum(1 for w in word_counts if w <= 10) / n, 3),
        },
        "first_words_top10": first_words.most_common(10),
        "tool_use_top15": tool_counter.most_common(15),
        "inter_prompt_seconds": (
            {
                "p25": round(percentile(gaps_seconds, 0.25), 1),
                "median": round(statistics.median(gaps_seconds), 1),
                "p75": round(percentile(gaps_seconds, 0.75), 1),
                "max": round(max(gaps_seconds), 1),
                "n": len(gaps_seconds),
            }
            if gaps_seconds
            else None
        ),
        "tokens": {
            "input": (
                {
                    "median": round(statistics.median(in_tokens), 1),
                    "p75": round(percentile(in_tokens, 0.75), 1),
                    "max": int(max(in_tokens)),
                }
                if in_tokens
                else None
            ),
            "output": (
                {
                    "median": round(statistics.median(out_tokens), 1),
                    "p75": round(percentile(out_tokens, 0.75), 1),
                    "max": int(max(out_tokens)),
                }
                if out_tokens
                else None
            ),
        },
        "session_size_distribution": sorted([len(s["prompts"]) for s in sessions]),
    }


def per_session_stats(sessions):
    out = []
    for s in sessions:
        prompts = s["prompts"]
        if not prompts:
            continue
        classified = [classify_prompt(p["text"]) for p in prompts]
        n = len(prompts)
        word_counts = [c["words"] for c in classified]
        tool_counter = Counter(t for p in prompts for t in p.get("tools", []))
        out.append(
            {
                "session_id": s["session_id"],
                "working_directory": s.get("working_directory", ""),
                "git_branch": s.get("git_branch", ""),
                "first_time": s.get("first_time", ""),
                "last_time": s.get("last_time", ""),
                "n_prompts": n,
                "median_words": round(statistics.median(word_counts), 1),
                "share_questions": round(sum(1 for c in classified if c["is_question"]) / n, 3),
                "share_corrections": round(sum(1 for c in classified if c["has_correction_marker"]) / n, 3),
                "share_imperative": round(sum(1 for c in classified if c["is_imperative_opener"]) / n, 3),
                "tool_use_top5": tool_counter.most_common(5),
            }
        )
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def truncate_prompt(text: str, n: int) -> str:
    text = text or ""
    if len(text) <= n:
        return text
    return text[:n] + f" …[+{len(text)-n} chars]"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="path to a .jsonl file or an mlflow_export directory")
    ap.add_argument("--out", required=True, help="path to write the analysis JSON")
    ap.add_argument(
        "--max-prompt-chars",
        type=int,
        default=2000,
        help="truncate each prompt to this many chars in the output (default 2000)",
    )
    args = ap.parse_args()

    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"input does not exist: {src}")

    if src.is_dir():
        if not (src / "traces.jsonl").exists():
            raise SystemExit(f"directory has no traces.jsonl: {src}")
        input_type = "mlflow_export"
        sessions = load_mlflow_export(src)
    else:
        input_type = "raw_jsonl"
        sessions = load_raw_jsonl(src)

    # Truncate prompts and response excerpts in-place to keep the JSON small
    for s in sessions:
        for p in s["prompts"]:
            p["text"] = truncate_prompt(p["text"], args.max_prompt_chars)
            if "response_excerpt" in p:
                p["response_excerpt"] = truncate_prompt(p["response_excerpt"], 600)

    aggregate = compute_stats(sessions)
    per_session = per_session_stats(sessions)

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(
            {
                "input_type": input_type,
                "input_path": str(src),
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "aggregate_stats": aggregate,
                "per_session_stats": per_session,
                "sessions": sessions,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Wrote {out_path}")
    print(f"Input type: {input_type}")
    print(f"Sessions: {aggregate['total_sessions']}, Prompts: {aggregate['total_prompts']}")
    if aggregate.get("prompt_words"):
        pw = aggregate["prompt_words"]
        print(f"Prompt length (words): median={pw['median']}, p25={pw['p25']}, p75={pw['p75']}, max={pw['max']}")
    if aggregate.get("share"):
        sh = aggregate["share"]
        print(
            "Share — "
            f"questions={sh['questions']:.0%}, imperative={sh['imperative_openers']:.0%}, "
            f"corrections={sh['correction_markers']:.0%}, ticket_refs={sh['ticket_refs']:.0%}"
        )


if __name__ == "__main__":
    main()
