#!/usr/bin/env python3
"""TTL detector for the Claude Code prompt-cache warmer.

Reads the latest assistant turn's cache_creation TTL bucket and
returns the effective TTL in seconds. Prefers the slim diagnostic
log (faster) and falls back to the live transcript.

Library use:
    from importlib import import_module
    ttl = detect_ttl(session_id, project_dir, transcript_path)

CLI use:
    python3 detect-ttl.py --session-id <sid> --project-dir <dir> --transcript <path>
    # prints "3600" or "300" to stdout
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_TTL_SECONDS = 300  # cold-start / unreadable fallback


def _ttl_from_buckets(cache_1h: int, cache_5m: int) -> int | None:
    if cache_1h > 0:
        return 3600
    if cache_5m > 0:
        return 300
    return None


def _ttl_from_diag_log(log_path: Path) -> int | None:
    try:
        lines = log_path.read_text().splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        ttl = _ttl_from_buckets(
            rec.get("cache_create_1h", 0),
            rec.get("cache_create_5m", 0),
        )
        # Pure cache-read turns tell us nothing about which TTL bucket is in
        # use; fall through to keep scanning earlier records.
        if ttl is not None:
            return ttl
    return None


def _ttl_from_transcript(transcript_path: Path) -> int | None:
    try:
        lines = transcript_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "assistant":
            continue
        msg = rec.get("message") or {}
        if not isinstance(msg, dict):
            continue
        usage = msg.get("usage") or {}
        cc = usage.get("cache_creation") or {}
        ttl = _ttl_from_buckets(
            cc.get("ephemeral_1h_input_tokens", 0),
            cc.get("ephemeral_5m_input_tokens", 0),
        )
        # Pure cache-read turns tell us nothing about which TTL bucket is in
        # use; fall through to keep scanning earlier records.
        if ttl is not None:
            return ttl
    return None


def detect_ttl(session_id: str, project_dir: str, transcript_path: str) -> int:
    """Return the effective cache TTL in seconds. Pure function.

    Order of preference:
      1. diagnostic log at <project_dir>/.claude/diagnostics/<session_id>.jsonl
      2. transcript at <transcript_path>
      3. cold-start fallback (300s)

    Always returns a positive int; never raises.
    """
    log_path = Path(project_dir) / ".claude" / "diagnostics" / f"{session_id}.jsonl"
    ttl = _ttl_from_diag_log(log_path)
    if ttl is not None:
        return ttl
    ttl = _ttl_from_transcript(Path(transcript_path))
    if ttl is not None:
        return ttl
    return DEFAULT_TTL_SECONDS


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect Claude Code prompt-cache TTL.")
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--transcript", required=True, help="path to transcript JSONL")
    args = ap.parse_args()
    print(detect_ttl(args.session_id, args.project_dir, args.transcript))
    return 0


if __name__ == "__main__":
    sys.exit(main())
