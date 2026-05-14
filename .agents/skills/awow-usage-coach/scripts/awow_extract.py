"""Extract usage signals from a Claude Code mlflow export, tuned for awow.

Reads an mlflow_export/ directory (produced by the mlflow-export skill),
filters to sessions in the target repo, then computes team-aggregate and
per-user signals across three lenses:

  1. INTENT SHAPE — every prompt is classified into one of seven intent
     labels (investigate / plan / propose / implement / refine / verify /
     document). Vocabulary-agnostic, so it works whether or not the team
     uses awow's exact slash commands.
  2. SEQUENCE PATTERNS — bigrams and trigrams of intent transitions per
     session (e.g. investigate→implement→verify) surface the working
     rhythm. Compared subject-vs-team in self-coach mode.
  3. EDIT PATTERNS — files.modified is pulled from each trace's tags and
     bucketed by location/type (proposal / context / agents-config /
     code / config / markdown / other). Crossed with intent so reports
     can say "when teammates 'propose', 70% of touched files are .md;
     when you 'propose', 30% are .md and 50% are code".

Awow-specific vocabulary signals (slash commands, proposal-first paths,
placement decision tree) are kept as a SECONDARY lens — emitted when
present, never required.

Usage:
    python3 awow_extract.py \\
        --input /path/to/mlflow_export \\
        --out   /path/to/awow_usage.json \\
        [--awow-root ../awow] \\
        [--include-path /path/to/other/repo]... \\
        [--user <email-or-short-name>]

If --user is set, the JSON gains a 'subject' block isolating that user's
prompts and a 'baseline' block with the rest of the team, ready for
side-by-side reporting.

If --include-path is given (repeatable), sessions whose working_directory
matches any listed path are also kept — useful for treating a sibling
repo as a stand-in when awow has no traces yet.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# awow surface: what we know exists in the repo
# ---------------------------------------------------------------------------

# Commands declared under .agents/commands/. The set is enumerated so reports
# can call out *coverage* (which exist, which are unused).
KNOWN_COMMANDS = {
    "setup-awow": "kickoff",
    "awow-add": "meta",
    "awow-status": "meta",
    "refinement-prep": "seed",
    "process-workitem": "seed",
    "process-transcript": "seed",
    "release-notes": "spread",
    "board-skill": "spread",
    "sprint-review-prep": "spread",
    "claudetracing-setup": "standardise",
    "daily-digest": "standardise",
    "weekly-digest": "standardise",
    "programme-board-projection": "standardise",
    "cross-team-view": "standardise",
}

# Canonical paths the awow style guide treats as "expensive to change" — the
# proposal-first rule says drafts go to proposals/ first.
CANONICAL_PATH_RE = re.compile(
    r"\b(context/team/|context/knowledge-base/|context/company/|context/tooling/|\.agents/|CLAUDE\.md|AGENTS\.md)",
    re.I,
)
PROPOSAL_PATH_RE = re.compile(r"\bproposals?/", re.I)

# Board / story vocabulary — used to detect intent vs status vs durable.
BOARD_VERBS = re.compile(
    r"\b(create|update|edit|rewrite|write|add|set|change|move|close|reopen|comment)\b",
    re.I,
)
STORY_NOUNS = re.compile(r"\b(story|ticket|issue|epic|workitem|work item|backlog item)\b", re.I)
KB_NOUNS = re.compile(r"\b(knowledge[- ]base|kb|runbook|adr|decision record|glossary)\b", re.I)
COMMENT_NOUNS = re.compile(r"\b(comment|status|update|progress|blocker)\b", re.I)

# "Minimum useful body" anti-patterns the user might still phrase.
BLOAT_HINTS = re.compile(
    r"\b(context section|considerations|recap|meeting recap|background section|"
    r"fill in.*background|expand|elaborate|flesh out|verbose)\b",
    re.I,
)
BREVITY_HINTS = re.compile(
    r"\b(short|terse|minim(al|um)|brief|one[- ]liner|three sentences|"
    r"acceptance criteria|just the intent|don'?t add)\b",
    re.I,
)

# Slash-command opener at the start of a prompt.
SLASH_CMD_RE = re.compile(r"^\s*/([a-zA-Z][\w-]*)")

# Phase keywords (helps tell what the team is doing, not which command was used).
PHASE_KEYWORDS = {
    "kickoff": re.compile(r"\b(setup|bootstrap|onboard|wizard|kickoff)\b", re.I),
    "seed": re.compile(r"\b(refinement|workitem|work item|transcript|seed phase)\b", re.I),
    "spread": re.compile(r"\b(release[- ]?notes|sprint review|board[- ]?skill|spread phase)\b", re.I),
    "standardise": re.compile(r"\b(digest|programme board|cross[- ]?team|voice memo|claudetracing)\b", re.I),
}

# Proposal-first signals.
PROPOSAL_HINTS = re.compile(
    r"\b(propose|proposal|draft|first[- ]?draft|draft to proposals|write to proposals)\b",
    re.I,
)
DIRECT_WRITE_HINTS = re.compile(
    r"\b(just write|update directly|push to (main|master)|edit (the )?(context|kb|knowledge base|board)|"
    r"go ahead and (write|commit|push))\b",
    re.I,
)

# ---------------------------------------------------------------------------
# Intent taxonomy (vocabulary-agnostic — works regardless of slash commands)
# ---------------------------------------------------------------------------
#
# Order matters: each prompt is checked against patterns in this order, and
# the first match wins. So put more-specific patterns first.

INTENT_PATTERNS: list[tuple[str, re.Pattern]] = [
    # "Refine / iterate" — corrections and redirects. Catch these first so a
    # prompt like "no, actually delete it instead" classifies as refine, not
    # implement.
    (
        "refine",
        re.compile(
            r"^\s*(no[,\.\s!\?]|nope|actually,?|wait[,\.\s]|hold on|instead|"
            r"i mean(t)?|let me rephrase|undo|revert|nvm|never mind|stop[,\.\s]|"
            r"that'?s wrong|not (what|that)|rather|let'?s redo)",
            re.I,
        ),
    ),
    # "Propose / draft" — explicit drafting intent.
    (
        "propose",
        re.compile(
            r"\b(propose|proposal|draft|sketch|outline|first[- ]?draft|put together|"
            r"write up a proposal|write a draft|drafting)\b",
            re.I,
        ),
    ),
    # "Plan" — strategy / approach / trade-off framing.
    (
        "plan",
        re.compile(
            r"\b(should we|what (do you|would you) (think|recommend)|recommend|"
            r"approach|strategy|strategi[sz]e|trade[- ]?off|architecture|design|"
            r"consider|plan (for|to|out)|options?\b|alternatives?|pros and cons|"
            r"how should|what'?s the best way)\b",
            re.I,
        ),
    ),
    # "Verify / test" — checks, confirmation, validation.
    (
        "verify",
        re.compile(
            r"\b(verify|confirm|validate|make sure|sanity[- ]?check|"
            r"check (that|if|whether|the|this|that it|its)|"
            r"does (it|this|that) work|did (it|this|that) work|"
            r"run (the )?tests?|test (it|this|that)|is it (working|correct))\b",
            re.I,
        ),
    ),
    # "Document" — capture, record, kb, docs.
    (
        "document",
        re.compile(
            r"\b(document(ation)?|write up|note (down|this)|capture (in|to|the)|"
            r"put (it |this )?(in|into) (the )?(kb|knowledge[- ]?base|readme|doc|"
            r"notes|adr)|kb entry|runbook|add a note|record (this|the|that))\b",
            re.I,
        ),
    ),
    # "Implement" — imperative verbs that move bits or code.
    (
        "implement",
        re.compile(
            r"^\s*(add|create|build|implement|fix|update|run|deploy|merge|commit|"
            r"push|delete|remove|generate|rename|edit|write|make|refactor|"
            r"move|change|set|install|configure|patch)\b|"
            r"\b(can you (add|create|fix|implement|update|build|run|delete|remove|"
            r"generate|rename|edit|refactor))\b",
            re.I,
        ),
    ),
    # "Investigate" — questions, look-ups, exploration. Also catches "give
    # me / share / show me X" requests, which are information-retrieval not
    # state-changing.
    (
        "investigate",
        re.compile(
            r"^\s*(can you (check|see|find|look|tell)|could you (check|see|find)|"
            r"is there|are there|what'?s|what is|what are|how (do|does|can|is|are)|"
            r"where (is|are|do|does)|why (is|are|do|does)|when (do|does|did)|"
            r"do we|does it|are we|is the|is this|tell me|show me|find|search|"
            r"look for|grep|list|inspect|debug|investigate|why is|"
            r"(give|share|send|paste|show|describe|explain|summari[sz]e|render|"
            r"format|output|fetch|pull|grab|copy) (me|us|it|that|this|the|a |an |"
            r"some|all))\b|\?\s*$",
            re.I,
        ),
    ),
    # "Inform" — declarative status updates and observations. Catches the
    # "I did X / it does Y / the bug is Z" shape that's neither a question
    # nor a command. Tolerates a leading list marker like "1." or "2)".
    (
        "inform",
        re.compile(
            r"^\s*([0-9]+[\.\)]\s+)?"
            r"(i (just |already |only |then |also |then also )?"
            r"(did|tried|got|saw|noticed|found|checked|added|removed|configured|"
            r"set ?up|sent|received|ran|tested|updated|installed|deployed|"
            r"created|deleted|fixed|implemented|opened|closed|see|think|notice|"
            r"believe|assume|have|am|was|was just|'?ve|'?m)"
            r"|(it|that|this) (is|was|just|seems|appears|looks|did|does|has|have|"
            r"didn'?t|doesn'?t|isn'?t|wasn'?t)"
            r"|now (it|this|the)"
            r"|there (is|are|was|were|seems)"
            r"|the (issue|problem|bug|error|test|build|deploy|file|code|change|"
            r"fix|result|output) (is|was|appears)"
            r"|nothing|nope[,\.\s]|yes[,\.\s])",
            re.I,
        ),
    ),
]


def classify_intent(text: str) -> str:
    text = text or ""
    for label, rx in INTENT_PATTERNS:
        if rx.search(text):
            return label
    # Pure "?" at end with no opener still counts as investigate.
    if text.strip().endswith("?"):
        return "investigate"
    return "other"


# ---------------------------------------------------------------------------
# File-modification classifier (used on tags["files.modified"])
# ---------------------------------------------------------------------------


def file_type(path: str) -> str:
    p = (path or "").lower()
    if "/proposals/" in p or p.startswith("proposals/"):
        return "proposal"
    if "/context/team/" in p or "/context/knowledge-base/" in p or "/context/" in p:
        return "context"
    if "/.agents/" in p or p.startswith(".agents/") or p.endswith("/claude.md") or p.endswith("/agents.md"):
        return "agents-config"
    if p.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".rb", ".c", ".cpp", ".cs", ".kt", ".swift")):
        return "code"
    if p.endswith((".tf", ".tfvars", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".env")):
        return "config"
    if p.endswith((".sql", ".ipynb", ".csv", ".parquet")):
        return "data"
    if p.endswith(".md"):
        return "markdown"
    if p.endswith((".sh", ".ps1", ".bat")):
        return "script"
    return "other"


def bucket_files(paths: list[str]) -> dict[str, int]:
    out: Counter = Counter()
    for p in paths or []:
        out[file_type(p)] += 1
    return dict(out)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def normalize_user(u: str | None) -> str:
    if not u:
        return ""
    u = u.strip().lower()
    return u.split("@", 1)[0]


def load_mlflow_export(directory: Path) -> list[dict]:
    """Return a list of session dicts; same shape as prompt-skill-analysis."""
    traces_path = directory / "traces.jsonl"
    if not traces_path.exists():
        raise SystemExit(f"traces.jsonl not found in {directory}")

    sessions: dict[str, dict] = {}
    with traces_path.open() as fh:
        for line in fh:
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

            user_raw = (
                meta.get("mlflow.trace.user")
                or tags.get("mlflow.user")
                or meta.get("mlflow.user")
                or ""
            )
            working_dir = (
                meta.get("mlflow.trace.working_directory")
                or tags.get("mlflow.trace.working_directory", "")
                or ""
            )

            sess = sessions.setdefault(
                session_id,
                {
                    "session_id": session_id,
                    "working_directory": working_dir,
                    "git_branch": tags.get("git.branch", ""),
                    "git_remote_url": tags.get("git.remote_url", ""),
                    "user_raw": user_raw,
                    "user": normalize_user(user_raw),
                    "first_time_ms": None,
                    "last_time_ms": None,
                    "prompts": [],
                },
            )
            # files.modified is a JSON-stringified list of relative paths.
            files_raw = tags.get("files.modified", "[]")
            try:
                files_mod = json.loads(files_raw) if isinstance(files_raw, str) else (files_raw or [])
            except Exception:
                files_mod = []
            if not isinstance(files_mod, list):
                files_mod = []

            sess["prompts"].append(
                {
                    "request_time_ms": info.get("request_time"),
                    "text": prompt_text,
                    "response_excerpt": (response_text or "")[:800],
                    "files_modified": files_mod,
                    "file_buckets": bucket_files(files_mod),
                }
            )

    out = []
    for sess in sessions.values():
        sess["prompts"].sort(key=lambda p: p.get("request_time_ms") or 0)
        if sess["prompts"]:
            sess["first_time_ms"] = sess["prompts"][0]["request_time_ms"]
            sess["last_time_ms"] = sess["prompts"][-1]["request_time_ms"]
        out.append(sess)
    out.sort(key=lambda s: s.get("first_time_ms") or 0)
    return out


def is_target_session(sess: dict, awow_root: Path, include_paths: list[Path]) -> bool:
    """A session belongs to the target set if its working_directory matches
    the awow root, contains 'awow' in its path, or matches one of the
    explicit --include-path entries.
    """
    wd = (sess.get("working_directory") or "").rstrip("/")
    if not wd:
        return False
    if "/awow" in wd or wd.endswith("/awow"):
        return True
    try:
        wd_resolved = Path(wd).resolve()
    except Exception:
        return False
    if wd_resolved == awow_root.resolve():
        return True
    for p in include_paths:
        try:
            if wd_resolved == p.resolve():
                return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------------


def classify_prompt(text: str) -> dict:
    text = text or ""
    stripped = text.strip()
    m = SLASH_CMD_RE.match(stripped)
    slash = m.group(1).lower() if m else None

    canonical_targets = CANONICAL_PATH_RE.findall(text)
    proposal_targets = PROPOSAL_PATH_RE.findall(text)

    return {
        "intent": classify_intent(text),
        "slash_command": slash,
        "phase_keywords": [p for p, rx in PHASE_KEYWORDS.items() if rx.search(text)],
        "mentions_story": bool(STORY_NOUNS.search(text)),
        "mentions_kb": bool(KB_NOUNS.search(text)),
        "mentions_comment_concept": bool(COMMENT_NOUNS.search(text)),
        "board_verbs": bool(BOARD_VERBS.search(text)),
        "mentions_canonical_path": bool(canonical_targets),
        "mentions_proposal_path": bool(proposal_targets),
        "proposal_first_signal": bool(PROPOSAL_HINTS.search(text)),
        "direct_write_signal": bool(DIRECT_WRITE_HINTS.search(text)),
        "bloat_signal": bool(BLOAT_HINTS.search(text)),
        "brevity_signal": bool(BREVITY_HINTS.search(text)),
        "words": len(stripped.split()),
    }


def ngrams(seq: list[str], n: int) -> list[tuple]:
    return [tuple(seq[i : i + n]) for i in range(len(seq) - n + 1)] if len(seq) >= n else []


def intent_sequence_stats(sessions: list[dict]) -> dict:
    """Compute intent bigrams/trigrams and per-intent rollups across sessions."""
    intent_counter: Counter = Counter()
    bigram_counter: Counter = Counter()
    trigram_counter: Counter = Counter()

    # Per-intent: how many prompts, how often files were touched, file-type mix.
    per_intent: dict[str, dict] = defaultdict(
        lambda: {"n_prompts": 0, "n_with_files": 0, "file_buckets": Counter(), "median_words": []}
    )

    # Session-level shape: what fraction of each session is what intent.
    session_shapes: list[dict] = []

    for sess in sessions:
        seq = [classify_intent(p["text"]) for p in sess["prompts"]]
        intent_counter.update(seq)
        bigram_counter.update(ngrams(seq, 2))
        trigram_counter.update(ngrams(seq, 3))

        for p, label in zip(sess["prompts"], seq):
            per_intent[label]["n_prompts"] += 1
            per_intent[label]["median_words"].append(len((p["text"] or "").split()))
            if p.get("files_modified"):
                per_intent[label]["n_with_files"] += 1
                per_intent[label]["file_buckets"].update(p.get("file_buckets") or {})

        if seq:
            sess_counter = Counter(seq)
            n = len(seq)
            session_shapes.append(
                {
                    "session_id": sess["session_id"],
                    "user": sess.get("user", ""),
                    "n_prompts": n,
                    "first_intent": seq[0],
                    "shape": {k: round(v / n, 3) for k, v in sess_counter.most_common()},
                    "sequence_preview": seq[:20],
                }
            )

    # Materialize per-intent.
    pi_out = {}
    for label, agg in per_intent.items():
        wc = agg["median_words"]
        pi_out[label] = {
            "n_prompts": agg["n_prompts"],
            "share": round(agg["n_prompts"] / max(intent_counter.total(), 1), 3),
            "n_with_files": agg["n_with_files"],
            "files_touch_rate": round(agg["n_with_files"] / agg["n_prompts"], 3) if agg["n_prompts"] else 0,
            "file_buckets": dict(agg["file_buckets"].most_common()),
            "median_words": round(statistics.median(wc), 1) if wc else 0,
        }

    return {
        "intent_counts": intent_counter.most_common(),
        "intent_shares": {k: round(v / intent_counter.total(), 3) for k, v in intent_counter.most_common()}
        if intent_counter.total()
        else {},
        "bigrams_top15": [
            {"seq": "→".join(b), "count": c} for b, c in bigram_counter.most_common(15)
        ],
        "trigrams_top10": [
            {"seq": "→".join(t), "count": c} for t, c in trigram_counter.most_common(10)
        ],
        "per_intent": pi_out,
        "session_shapes": session_shapes,
    }


def edit_footprint(prompts: list[dict]) -> dict:
    """Roll up file modifications across prompts."""
    all_files: list[str] = []
    bucket_counter: Counter = Counter()
    prompts_with_files = 0
    for p in prompts:
        files = p.get("files_modified") or []
        if files:
            prompts_with_files += 1
            all_files.extend(files)
            bucket_counter.update(p.get("file_buckets") or {})
    path_counter = Counter(all_files)
    return {
        "n_prompts_with_files": prompts_with_files,
        "share_prompts_with_files": round(prompts_with_files / len(prompts), 3) if prompts else 0,
        "total_file_modifications": len(all_files),
        "unique_files": len(path_counter),
        "file_buckets": dict(bucket_counter.most_common()),
        "top_files_top20": path_counter.most_common(20),
    }


def aggregate(prompts: list[dict], classified: list[dict], sessions: list[dict] | None = None) -> dict:
    n = len(prompts)
    if n == 0:
        return {"n_prompts": 0}

    cmd_counter = Counter(c["slash_command"] for c in classified if c["slash_command"])
    phase_counter = Counter(p for c in classified for p in c["phase_keywords"])

    def share(key):
        return round(sum(1 for c in classified if c[key]) / n, 3)

    # Proposal-first vs direct-write *intent* per prompt that mentions a canonical
    # path. This is the load-bearing awow style signal.
    canon_prompts = [c for c in classified if c["mentions_canonical_path"]]
    proposal_first_when_canonical = (
        round(sum(1 for c in canon_prompts if c["proposal_first_signal"]) / len(canon_prompts), 3)
        if canon_prompts
        else None
    )
    direct_write_when_canonical = (
        round(sum(1 for c in canon_prompts if c["direct_write_signal"]) / len(canon_prompts), 3)
        if canon_prompts
        else None
    )

    # Placement-decision-tree compliance heuristic. When a prompt mentions a
    # story and also uses a board verb, did it ALSO mention the kb (durable)
    # or 'comment' (status)? Pure story+verb without either suggests the user
    # may be cramming everything into the story body.
    story_board = [c for c in classified if c["mentions_story"] and c["board_verbs"]]
    story_classifies = (
        round(
            sum(1 for c in story_board if c["mentions_kb"] or c["mentions_comment_concept"])
            / len(story_board),
            3,
        )
        if story_board
        else None
    )

    word_counts = [c["words"] for c in classified]

    # Intent + sequence analysis. Falls back to a flat shape if no sessions
    # were passed (e.g. when called for a per-user slice on raw prompts).
    seq_block = (
        intent_sequence_stats(sessions)
        if sessions
        else {
            "intent_counts": Counter(c["intent"] for c in classified).most_common(),
            "intent_shares": {
                k: round(v / n, 3)
                for k, v in Counter(c["intent"] for c in classified).most_common()
            },
            "bigrams_top15": [],
            "trigrams_top10": [],
            "per_intent": {},
            "session_shapes": [],
        }
    )

    edit_block = edit_footprint(prompts)

    return {
        "n_prompts": n,
        "intent": seq_block,
        "edit_footprint": edit_block,
        "slash_commands": cmd_counter.most_common(),
        "slash_command_unique": len(cmd_counter),
        "phase_keyword_counts": phase_counter.most_common(),
        "share": {
            "starts_with_slash": share("slash_command") if False else round(
                sum(1 for c in classified if c["slash_command"]) / n, 3
            ),
            "mentions_story": share("mentions_story"),
            "mentions_kb": share("mentions_kb"),
            "mentions_comment_concept": share("mentions_comment_concept"),
            "mentions_canonical_path": share("mentions_canonical_path"),
            "mentions_proposal_path": share("mentions_proposal_path"),
            "proposal_first_signal": share("proposal_first_signal"),
            "direct_write_signal": share("direct_write_signal"),
            "bloat_signal": share("bloat_signal"),
            "brevity_signal": share("brevity_signal"),
        },
        "proposal_discipline": {
            "n_canonical_path_prompts": len(canon_prompts),
            "proposal_first_rate": proposal_first_when_canonical,
            "direct_write_rate": direct_write_when_canonical,
        },
        "placement_discipline": {
            "n_story_with_board_verb": len(story_board),
            "rate_referenced_kb_or_comment": story_classifies,
        },
        "prompt_words": {
            "median": round(statistics.median(word_counts), 1),
            "p75": round(percentile(word_counts, 0.75), 1),
            "max": max(word_counts),
        },
        "command_coverage": {
            "used": sorted(cmd_counter.keys()),
            "unused": sorted(set(KNOWN_COMMANDS) - set(cmd_counter)),
            "unknown_invoked": sorted(set(cmd_counter) - set(KNOWN_COMMANDS)),
        },
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


def per_user_breakdown(sessions: list[dict]) -> list[dict]:
    by_user_sessions: dict[str, list[dict]] = defaultdict(list)
    for s in sessions:
        by_user_sessions[s["user"] or "unknown"].append(s)

    out = []
    for user, user_sessions in by_user_sessions.items():
        prompts = [p for s in user_sessions for p in s["prompts"]]
        classified = [classify_prompt(p["text"]) for p in prompts]
        out.append(
            {
                "user": user,
                "n_sessions": len(user_sessions),
                **aggregate(prompts, classified, user_sessions),
            }
        )
    out.sort(key=lambda u: -u["n_prompts"])
    return out


def collect_quotes(sessions: list[dict], limit_per_bucket: int = 5) -> dict:
    """Surface up-to-N verbatim quotes per bucket so the model can ground its report.

    The model is told never to invent quotes — these are the well from which to draw.
    Buckets cover: each intent label, each detected slash command, and the
    awow-vocabulary signals (proposal-first, direct-write-to-canonical,
    story-only, bloat/brevity).
    """
    buckets: dict[str, list[dict]] = defaultdict(list)
    for s in sessions:
        for p in s["prompts"]:
            c = classify_prompt(p["text"])
            evidence = {
                "user": s["user"] or "unknown",
                "session_id": s["session_id"],
                "ts_ms": p.get("request_time_ms"),
                "text": (p["text"] or "")[:600],
                "files_modified": (p.get("files_modified") or [])[:8],
            }
            buckets[f"intent:{c['intent']}"].append(evidence)
            if c["slash_command"]:
                buckets[f"slash:{c['slash_command']}"].append(evidence)
            if c["direct_write_signal"] and c["mentions_canonical_path"]:
                buckets["direct_write_to_canonical"].append(evidence)
            if c["proposal_first_signal"]:
                buckets["proposal_first"].append(evidence)
            if c["mentions_story"] and c["board_verbs"] and not (c["mentions_kb"] or c["mentions_comment_concept"]):
                buckets["story_only_no_placement"].append(evidence)
            if c["bloat_signal"]:
                buckets["bloat_signal"].append(evidence)
            if c["brevity_signal"]:
                buckets["brevity_signal"].append(evidence)

    return {k: v[:limit_per_bucket] for k, v in buckets.items()}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="path to mlflow_export directory")
    ap.add_argument("--out", required=True, help="path to write the analysis JSON")
    ap.add_argument(
        "--awow-root",
        default="../awow",
        help="path to the awow repo (default: ../awow relative to cwd)",
    )
    ap.add_argument(
        "--include-path",
        action="append",
        default=[],
        help="extra working_directory to treat as a target repo (repeatable). "
             "Useful when awow has no traces yet and you want to evaluate sequence "
             "patterns on a sibling repo as a stand-in.",
    )
    ap.add_argument(
        "--user",
        default=None,
        help="optional user id (email or short name) to isolate in 'subject' block",
    )
    ap.add_argument("--max-prompt-chars", type=int, default=1200)
    args = ap.parse_args()

    src = Path(args.input).expanduser().resolve()
    awow_root = Path(args.awow_root).expanduser().resolve()
    include_paths = [Path(p).expanduser().resolve() for p in args.include_path]

    all_sessions = load_mlflow_export(src)
    target_sessions = [s for s in all_sessions if is_target_session(s, awow_root, include_paths)]

    # Truncate prompts in-place to keep the JSON manageable.
    for s in target_sessions:
        for p in s["prompts"]:
            if len(p["text"]) > args.max_prompt_chars:
                p["text"] = p["text"][: args.max_prompt_chars] + f" …[+{len(p['text']) - args.max_prompt_chars} chars]"

    all_prompts = [p for s in target_sessions for p in s["prompts"]]
    all_classified = [classify_prompt(p["text"]) for p in all_prompts]
    team_aggregate = aggregate(all_prompts, all_classified, target_sessions)
    per_user = per_user_breakdown(target_sessions)
    quotes = collect_quotes(target_sessions)

    subject_user = normalize_user(args.user) if args.user else None
    subject_block = None
    baseline_block = None
    if subject_user:
        subj_sessions = [s for s in target_sessions if s["user"] == subject_user]
        base_sessions = [s for s in target_sessions if s["user"] != subject_user]
        subj_prompts = [p for s in subj_sessions for p in s["prompts"]]
        base_prompts = [p for s in base_sessions for p in s["prompts"]]
        subj_classified = [classify_prompt(p["text"]) for p in subj_prompts]
        base_classified = [classify_prompt(p["text"]) for p in base_prompts]
        subject_block = {
            "user": subject_user,
            "n_sessions": len(subj_sessions),
            **aggregate(subj_prompts, subj_classified, subj_sessions),
        }
        baseline_block = {
            "user": "rest_of_team",
            "n_sessions": len(base_sessions),
            "n_users": len({s["user"] for s in base_sessions}),
            **aggregate(base_prompts, base_classified, base_sessions),
        }

    out = {
        "input_path": str(src),
        "awow_root": str(awow_root),
        "include_paths": [str(p) for p in include_paths],
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "total_sessions_in_export": len(all_sessions),
        "target_sessions": len(target_sessions),
        "target_users": sorted({s["user"] for s in target_sessions if s["user"]}),
        "target_working_directories": sorted({s["working_directory"] for s in target_sessions}),
        "known_commands": KNOWN_COMMANDS,
        "intent_taxonomy": [label for label, _ in INTENT_PATTERNS] + ["other"],
        "team_aggregate": team_aggregate,
        "per_user": per_user,
        "evidence_quotes": quotes,
        "subject": subject_block,
        "baseline": baseline_block,
        "sessions": target_sessions,
    }

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, default=str)

    print(f"Wrote {out_path}")
    print(f"Sessions in export: {len(all_sessions)} | target sessions: {len(target_sessions)}")
    if target_sessions:
        users = sorted({s["user"] for s in target_sessions if s["user"]})
        print(f"Users: {', '.join(users) or '(none tagged)'}")
        print(f"Prompts: {team_aggregate['n_prompts']}")
        intents = team_aggregate.get("intent", {}).get("intent_counts") or []
        if intents:
            print("Intent mix: " + ", ".join(f"{lbl}×{n}" for lbl, n in intents))
        bigrams = team_aggregate.get("intent", {}).get("bigrams_top15") or []
        if bigrams:
            print("Top bigrams: " + ", ".join(f"{b['seq']}×{b['count']}" for b in bigrams[:5]))
        edit = team_aggregate.get("edit_footprint", {})
        if edit:
            print(
                f"Edit footprint: {edit.get('n_prompts_with_files', 0)} prompts modified files "
                f"({edit.get('share_prompts_with_files', 0):.0%}); buckets: {edit.get('file_buckets', {})}"
            )
        cmds = team_aggregate.get("slash_commands") or []
        if cmds:
            print("Top slash commands: " + ", ".join(f"{c}×{n}" for c, n in cmds[:5]))
    if subject_user:
        print(f"Subject user: {subject_user} ({subject_block['n_sessions']} sessions, {subject_block['n_prompts']} prompts)")


if __name__ == "__main__":
    main()
