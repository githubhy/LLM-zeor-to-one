#!/usr/bin/env python3
"""Claude Code Stop-hook: append per-turn API-response metadata to a
structured diagnostic log.

Hook payload (stdin JSON): {session_id, transcript_path, cwd, ...}.
Output: appends one JSONL line to `<cwd>/.claude/diagnostics/<session_id>.jsonl`.
Failure mode: prints to stderr and exits non-zero so the hook log
captures it; never raises.
"""

import json
import sys
from pathlib import Path


def extract_record(rec: dict, session_id: str) -> dict | None:
    """Reduce a raw transcript assistant record to the slim telemetry shape.
    Returns None only if `message` is not a dict (structurally unusable);
    records with missing/empty `usage` resolve to all-zero counters via .get defaults."""
    msg = rec.get("message") or {}
    if not isinstance(msg, dict):
        return None
    usage = msg.get("usage") or {}
    if not isinstance(usage, dict):
        return None
    cc = usage.get("cache_creation") or {}
    stu = usage.get("server_tool_use") or {}
    diag = msg.get("diagnostics") or {}
    cache_miss_raw = diag.get("cache_miss_reason") if isinstance(diag, dict) else None
    cache_miss = None
    if isinstance(cache_miss_raw, dict):
        cache_miss = {
            "type": cache_miss_raw.get("type"),
            "tokens": cache_miss_raw.get("cache_missed_input_tokens"),
        }
    iterations = usage.get("iterations") or []
    return {
        "ts":             rec.get("timestamp"),
        "session_id":     session_id,
        "model":          msg.get("model"),
        "stop_reason":    msg.get("stop_reason"),
        "service_tier":   usage.get("service_tier"),
        "speed":          usage.get("speed"),
        "inference_geo":  usage.get("inference_geo"),
        "input":          usage.get("input_tokens", 0),
        "output":         usage.get("output_tokens", 0),
        "cache_read":     usage.get("cache_read_input_tokens", 0),
        "cache_create_1h": cc.get("ephemeral_1h_input_tokens", 0),
        "cache_create_5m": cc.get("ephemeral_5m_input_tokens", 0),
        "iterations":     len(iterations) if isinstance(iterations, list) else 0,
        "web_search":     stu.get("web_search_requests", 0) if isinstance(stu, dict) else 0,
        "web_fetch":      stu.get("web_fetch_requests", 0) if isinstance(stu, dict) else 0,
        "cache_miss":     cache_miss,
    }


def find_latest_assistant_turn(transcript_path: Path) -> dict | None:
    """Scan the transcript JSONL backwards for the most recent assistant turn."""
    try:
        with transcript_path.open(encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as e:
        print(f"log-turn-telemetry: cannot read transcript {transcript_path}: {e}", file=sys.stderr)
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") == "assistant":
            return rec
    return None


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError) as e:
        print(f"log-turn-telemetry: bad stdin payload: {e}", file=sys.stderr)
        return 1

    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")
    cwd = payload.get("cwd")
    if not (session_id and transcript_path and cwd):
        print(f"log-turn-telemetry: missing required payload fields: {payload}", file=sys.stderr)
        return 1

    rec = find_latest_assistant_turn(Path(transcript_path))
    if rec is None:
        # No assistant turn yet — nothing to log. Clean exit.
        return 0

    slim = extract_record(rec, session_id)
    if slim is None:
        return 0

    diag_dir = Path(cwd) / ".claude" / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    log_path = diag_dir / f"{session_id}.jsonl"
    with log_path.open("a") as fh:
        fh.write(json.dumps(slim) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
