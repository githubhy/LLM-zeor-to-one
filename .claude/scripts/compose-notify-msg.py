#!/usr/bin/env python3
"""compose-notify-msg.py — compose HTML message for the Pushover notify hook.

Uses ONLY Pushover-supported HTML tags: <b>, <i>, <u>, <font color="...">, <a>.
Line breaks are real \\n characters (Pushover does NOT render <br>).
Symbols are raw Unicode chars (Pushover does NOT decode HTML entities like
&#x25CF; or &middot;).

Invocation modes:
  1. stdin = Stop-hook JSON (has transcript_path): emits rich message
     Line 1: end-of-turn assistant summary (html-escaped)
     Blank line
     Line 3: colored-dot + <b>branch</b> + gray metadata
  2. stdin = empty / non-JSON / missing transcript: emits basic fallback
  3. --text MSG: emits html-escaped MSG verbatim (no enrichment)

Never errors — falls through to basic output on any parse problem.
"""
import argparse
import html
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import List, Optional


try:
    # utf-8 for the ● ⚠ · glyphs; newline='\n' so Windows Python doesn't
    # translate \n into \r\n (Pushover treats stray \r as literal).
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')
except Exception:
    pass


# Raw Unicode, NOT HTML entities (Pushover doesn't decode entities).
DOT_OK = '●'          # U+25CF — wrapped in <font color=GREEN>
DOT_ERR = '⚠'         # U+26A0 — wrapped in <font color=RED>
SEP = ' · '           # U+00B7 middle dot with spaces
GREEN = '#2ea043'
RED = '#f85149'
GRAY = '#888'
SUMMARY_MAX_CHARS = 450


def resolve_path(p: str) -> str:
    """Accept both Git-Bash `/c/foo` and Windows `C:/foo` / `C:\\foo`."""
    if not p:
        return p
    if os.path.exists(p):
        return p
    if len(p) >= 3 and p[0] == '/' and p[2] == '/' and p[1].isalpha():
        converted = p[1].upper() + ':' + p[2:]
        if os.path.exists(converted):
            return converted
    return p


def parse_iso(ts: str) -> datetime:
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)


def fmt_duration(seconds: float) -> str:
    s = max(int(seconds), 0)
    if s < 60:
        return f'{s}s'
    m, s = divmod(s, 60)
    if m < 60:
        return f'{m}m {s}s'
    h, m = divmod(m, 60)
    return f'{h}h {m}m'


def git_branch(cwd: str) -> Optional[str]:
    try:
        r = subprocess.run(
            ['git', '-C', cwd, 'branch', '--show-current'],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode == 0:
            br = r.stdout.strip()
            return br or None
    except Exception:
        pass
    return None


def is_real_user_prompt(record: dict) -> bool:
    msg = record.get('message') or {}
    content = msg.get('content') if isinstance(msg, dict) else None
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'tool_result':
                return False
        return True
    return False


def smart_truncate(s: str, max_chars: int = SUMMARY_MAX_CHARS) -> str:
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars]
    for mark in ('. ', '! ', '? '):
        i = cut.rfind(mark)
        if i > max_chars // 2:
            return cut[:i + 1].rstrip() + '…'
    i = cut.rfind(' ')
    if i > 0:
        return cut[:i] + '…'
    return cut + '…'


def analyze_turn(path: str) -> dict:
    info = {
        'tool_uses': 0,
        'errors': 0,
        'turn_start_ts': None,
        'summary': None,
    }
    text_only_texts: List[str] = []
    mixed_texts: List[str] = []
    first_ts: Optional[str] = None

    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            ts = d.get('timestamp')
            if ts and first_ts is None:
                first_ts = ts
            if d.get('type') == 'user' and is_real_user_prompt(d):
                info['turn_start_ts'] = ts
                info['tool_uses'] = 0
                info['errors'] = 0
                text_only_texts = []
                mixed_texts = []
                continue
            msg = d.get('message') or {}
            content = msg.get('content') if isinstance(msg, dict) else None
            if isinstance(content, list):
                has_tool_use = False
                record_texts: List[str] = []
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    itype = item.get('type')
                    if itype == 'tool_use':
                        info['tool_uses'] += 1
                        has_tool_use = True
                    elif itype == 'tool_result' and item.get('is_error'):
                        info['errors'] += 1
                    elif itype == 'text' and d.get('type') == 'assistant':
                        t = item.get('text', '').strip()
                        if t:
                            record_texts.append(t)
                if record_texts:
                    if has_tool_use:
                        mixed_texts = record_texts
                    else:
                        text_only_texts = record_texts
            if d.get('isError') is True:
                info['errors'] += 1

    if info['turn_start_ts'] is None:
        info['turn_start_ts'] = first_ts
    chosen = text_only_texts or mixed_texts
    if chosen:
        joined = ' '.join(chosen)
        collapsed = ' '.join(joined.split())
        if collapsed:
            info['summary'] = smart_truncate(collapsed)

    return info


def compose_from_hook(hook: dict) -> Optional[str]:
    tp = resolve_path(hook.get('transcript_path') or '')
    if not tp or not os.path.exists(tp):
        return None
    cwd = resolve_path(hook.get('cwd') or os.getcwd())
    branch = git_branch(cwd)

    try:
        info = analyze_turn(tp)
    except Exception:
        return None

    duration_str = ''
    t0 = info.get('turn_start_ts')
    if t0:
        try:
            now = datetime.now(tz=timezone.utc)
            dur = (now - parse_iso(t0)).total_seconds()
            if dur > 0:
                duration_str = fmt_duration(dur)
        except Exception:
            pass

    errors = info.get('errors', 0)
    tool_uses = info.get('tool_uses', 0)
    summary = info.get('summary')

    if errors > 0:
        dot = f'<font color="{RED}">{DOT_ERR}</font>'
    else:
        dot = f'<font color="{GREEN}">{DOT_OK}</font>'

    meta_parts: List[str] = []
    if branch:
        meta_parts.append(f'<b>{html.escape(branch)}</b>')
    if errors == 0:
        meta_parts.append('done')
    if duration_str:
        meta_parts.append(duration_str)
    if tool_uses:
        meta_parts.append(f'{tool_uses} tool call' + ('s' if tool_uses != 1 else ''))
    if errors > 0:
        err_label = f'{errors} error' + ('s' if errors != 1 else '')
        meta_parts.append(f'<b><font color="{RED}">{err_label}</font></b>')
    meta_line = f'{dot} <font color="{GRAY}">{SEP.join(meta_parts)}</font>'

    if summary:
        return f'{html.escape(summary)}\n\n{meta_line}'

    dir_name = os.path.basename(cwd.rstrip('/\\')) or '?'
    header = f'<b>{html.escape(dir_name)}</b>'
    if branch:
        header += f'{SEP}{html.escape(branch)}'
    return f'{header}\n{meta_line}'


def compose_basic() -> str:
    cwd = resolve_path(os.getcwd())
    dir_name = os.path.basename(cwd.rstrip('/\\')) or '?'
    branch = git_branch(cwd)
    line1 = f'<font color="{GREEN}">{DOT_OK}</font> <b>{html.escape(dir_name)}</b>'
    if branch:
        line1 += f'{SEP}{html.escape(branch)}'
    return f'{line1}\n<font color="{GRAY}">done</font>'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text', default=None,
                        help='user text; html-escaped, skip transcript parsing')
    args = parser.parse_args()

    if args.text is not None:
        print(html.escape(args.text))
        return 0

    stdin_data = ''
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
        except Exception:
            stdin_data = ''

    if stdin_data.strip():
        try:
            hook = json.loads(stdin_data)
            if isinstance(hook, dict):
                rich = compose_from_hook(hook)
                if rich:
                    print(rich)
                    return 0
        except Exception:
            pass

    print(compose_basic())
    return 0


if __name__ == '__main__':
    sys.exit(main())
