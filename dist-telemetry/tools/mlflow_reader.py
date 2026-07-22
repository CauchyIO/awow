#!/usr/bin/env python3
"""Canonical reader for an `mlflow_export/` dir (the `mlflow-export` skill's output).

Single source of truth for how every consumer pulls fields out of a raw MLflow
trace. Both `tools/session_timeline.py` (the timeline dashboard) and the
`awow-usage-coach` extractor import these accessors instead of reaching into the
`mlflow.*` metadata strings themselves — so when the export format shifts there is
ONE place to fix, and drift can't silently diverge between consumers.

It also owns the `sessions.json` contract: `SESSIONS_SCHEMA_VERSION` is stamped onto
every emitted doc, and `validate_sessions_doc` fails loud (raises) on a missing key
or version mismatch rather than letting the consumer render blanks. Per the repo's
error-handling rules: fail fast, fail loud — no silent degradation.
"""
import json

# Bump when the raw-trace accessors below change in a way consumers must notice.
TRACE_READER_VERSION = 1
# Bump when the sessions.json shape emitted by session_timeline.build() changes.
SESSIONS_SCHEMA_VERSION = 1


def _info(tr):
    return tr.get("info") or {}


def _meta(tr):
    return _info(tr).get("trace_metadata") or {}


def _tags(tr):
    return _info(tr).get("tags") or {}


def _json(s):
    """Parse a value that may be a JSON string, dict/list, or None."""
    if s is None or s == "":
        return None
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return None


# ---- identity / grouping -------------------------------------------------

def session_id(tr):
    m, t, info = _meta(tr), _tags(tr), _info(tr)
    return (m.get("mlflow.trace.session") or t.get("mlflow.trace.session")
            or info.get("client_request_id") or info.get("trace_id") or "unknown")


def user(tr):
    """Raw user string (may be an email); use local_part() to normalize."""
    m, t = _meta(tr), _tags(tr)
    return m.get("mlflow.user") or m.get("mlflow.trace.user") or t.get("mlflow.user") or ""


def local_part(u, lower=False):
    """'casper@cauchy.io' -> 'casper'. Returns None for an empty user."""
    u = (u or "").strip()
    if lower:
        u = u.lower()
    return u.split("@", 1)[0] or None


def working_directory(tr):
    m, t = _meta(tr), _tags(tr)
    return m.get("mlflow.trace.working_directory") or t.get("mlflow.trace.working_directory") or ""


def git_branch(tr):
    t, m = _tags(tr), _meta(tr)
    return t.get("git.branch") or m.get("mlflow.source.git.branch") or ""


def git_remote_url(tr):
    return _tags(tr).get("git.remote_url", "")


# ---- timing --------------------------------------------------------------

def request_time_ms(tr):
    return _info(tr).get("request_time")


def duration_ms(tr):
    return _info(tr).get("execution_duration") or 0


# ---- content -------------------------------------------------------------

def files_modified(tr):
    """Relative paths the trace edited (JSON-stringified list tag). [] if absent."""
    raw = _tags(tr).get("files.modified", "[]")
    v = _json(raw)
    return v if isinstance(v, list) else []


def tokens(tr):
    """Per-trace cumulative token usage, broken out by kind. Prefers the schema-v3
    `tokens.*` tags, falling back to the older `mlflow.trace.tokenUsage` blob.

    NOTE: these are CUMULATIVE per trace (cache_read sums every turn's re-read of the
    prompt), so they measure cost, not a per-turn context window.
    """
    t = _tags(tr)
    tu = _json(_meta(tr).get("mlflow.trace.tokenUsage")) or {}

    def pick(tag_key, *blob_keys):
        v = t.get(tag_key)
        if v is None:
            for bk in blob_keys:
                if isinstance(tu, dict) and tu.get(bk) is not None:
                    v = tu.get(bk)
                    break
        try:
            return int(v)
        except (TypeError, ValueError):
            return 0

    return {
        "in": pick("tokens.input", "input_tokens"),
        "out": pick("tokens.output", "output_tokens"),
        "cache_read": pick("tokens.cache_read", "cache_read_input_tokens"),
        "cache_write": pick("tokens.cache_creation", "cache_creation_input_tokens"),
    }


def spans(tr):
    """The trace's spans (each a dict with at least a 'name'). [] if absent."""
    sp = tr.get("spans")
    return sp if isinstance(sp, list) else []


def first_prompt(tr):
    """First user prompt of the conversation, from traceInputs, if present."""
    ti = _json(_meta(tr).get("mlflow.traceInputs"))
    if isinstance(ti, dict) and ti.get("prompt"):
        return str(ti["prompt"]).strip()
    return None


def request_payload(tr):
    """Top-level `request` field parsed to a dict ({} on failure)."""
    v = _json(tr.get("request"))
    return v if isinstance(v, dict) else {}


def response_payload(tr):
    """Top-level `response` field parsed to a dict ({} on failure)."""
    v = _json(tr.get("response"))
    return v if isinstance(v, dict) else {}


# ---- sessions.json contract ---------------------------------------------

# Keys the timeline template hard-depends on; missing any means a broken view.
_REQUIRED_DOC_KEYS = (
    "schema_version", "source", "generated", "sessions", "totals", "users",
    "file_edges", "topic_edges", "handoff_edges", "idle_gaps",
)
_REQUIRED_SESSION_KEYS = (
    "id", "short", "title", "area", "areas", "start", "end", "duration_min",
    "user", "readonly", "files", "read_files", "edit_count", "msg_count",
    "tool_count", "peak_context", "in_tokens", "out_tokens", "cache_read", "cache_write",
)
_REQUIRED_TOTALS_KEYS = ("in_tokens", "out_tokens", "cache_read", "cache_write")


def validate_sessions_doc(data):
    """Raise ValueError if `data` isn't a well-formed sessions.json for this version.

    Called before the doc is written / inlined into the HTML, so a contract drift
    surfaces as a crash at build time instead of a silently blank dashboard.
    """
    if not isinstance(data, dict):
        raise ValueError(f"sessions doc must be a dict, got {type(data).__name__}")
    missing = [k for k in _REQUIRED_DOC_KEYS if k not in data]
    if missing:
        raise ValueError(f"sessions doc missing top-level keys: {missing}")
    if data["schema_version"] != SESSIONS_SCHEMA_VERSION:
        raise ValueError(
            f"sessions schema_version {data['schema_version']!r} != expected "
            f"{SESSIONS_SCHEMA_VERSION} — producer/consumer are out of sync")
    if not isinstance(data["totals"], dict) or [k for k in _REQUIRED_TOTALS_KEYS if k not in data["totals"]]:
        raise ValueError(f"sessions doc 'totals' missing keys (need {_REQUIRED_TOTALS_KEYS})")
    if not isinstance(data["sessions"], list):
        raise ValueError("sessions doc 'sessions' must be a list")
    for i, s in enumerate(data["sessions"]):
        bad = [k for k in _REQUIRED_SESSION_KEYS if k not in s]
        if bad:
            raise ValueError(f"session #{i} ({s.get('id','?')}) missing keys: {bad}")
    return data
