#!/usr/bin/env python3
"""
Claude Code status-line script.

Reads the Claude Code JSON payload from stdin and writes a compact, ANSI-colored
status line to stdout.  Implemented in Python so it works without jq on Windows
(Git Bash / MSYS2), Linux, and macOS.

Displayed fields
----------------
  repo/branch  — git repo name + current branch, shown first.  On the default
                   branch ("main") only a branch symbol (⎇, green) is shown;
                   on any other branch the name is shown (yellow), e.g.
                   "repo ⎇ feat/x".  Omitted when the working directory is
                   not a git repo or git is unavailable.
  model        — display name of the active model
  effort       — effortLevel from settings.json (project then global);
                   falls back to output_style.name from payload, then "default"
  ctx          — context-window used %, color-coded
                   green  < 50 %
                   yellow  50 – 69 %
                   red    >= 70 %
  cache        — "<hit%> <HH:MM>" for the prompt cache
                   hit%: last API call's cache hit rate, computed from
                         cache_read_input_tokens /
                         (cache_read_input_tokens + cache_creation_input_tokens)
                     green  >= 90 %
                     yellow  50 – 89 %
                     red    <  50 %
                   HH:MM: local system time at which the last turn completed,
                          derived from the transcript file mtime (Claude Code
                          rewrites the transcript at the end of every turn).
                   Either field is omitted independently when its source data
                   is missing from the payload.
  5h           — Claude.ai 5-hour rolling-window status.  Combines usage %
                   (color-coded, same green/yellow/red thresholds as ctx) with
                   the time remaining until reset, e.g. "5h 42% · 2h34m".
                   Either field is omitted individually when missing from the
                   payload; both absent → slot is omitted entirely.
  7d           — Same as 5h, for the 7-day rolling window,
                   e.g. "7d 18% · 3d14h".
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_CYAN   = "\033[36m"
_RESET  = "\033[0m"

# Shown in place of the branch name when on the default branch ("main").
_BRANCH_SYMBOL = "⎇"


def _color_ctx(pct: float) -> str:
    """Return the ANSI color code appropriate for *pct* context used."""
    if pct >= 70:
        return _RED
    if pct >= 50:
        return _YELLOW
    return _GREEN


def _format_remaining(seconds: int) -> str:
    """Render a seconds-remaining integer as a compact, human-scanable string.

    - Below 1 hour:   "45m"
    - Below 1 day:    "2h34m"
    - A day or more:  "3d14h"
    - Already reset or non-positive: "0m"
    """
    if seconds <= 0:
        return "0m"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours, rem_min = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h{rem_min:02d}m" if rem_min else f"{hours}h"
    days, rem_hours = divmod(hours, 24)
    return f"{days}d{rem_hours:02d}h" if rem_hours else f"{days}d"


def _read_effort_from_settings() -> str:
    """Read effortLevel from project then global settings.json."""
    candidates = [
        os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", ""), ".claude", "settings.json"),
        os.path.expanduser("~/.claude/settings.json"),
    ]
    for path in candidates:
        try:
            with open(path) as f:
                val = json.load(f).get("effortLevel") or ""
            if val:
                return val
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    return ""


def _git_repo_and_branch(cwd: str) -> tuple[str, str]:
    """Return ``(repo_name, branch)`` for the git repo containing *cwd*.

    *repo_name* is the basename of the repository top level; *branch* is the
    current branch, or the short commit SHA when HEAD is detached.  Returns
    ``("", "")`` when *cwd* is not inside a git work tree or git is
    unavailable — the caller then omits the segment so the status line
    degrades silently (same philosophy as the rest of this script).
    """
    if not cwd:
        cwd = os.environ.get("CLAUDE_PROJECT_DIR", "") or os.getcwd()
    try:
        res = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=1,
        )
    except (OSError, subprocess.SubprocessError):
        return "", ""
    if res.returncode != 0:
        return "", ""
    lines = res.stdout.splitlines()
    toplevel = lines[0].strip() if lines else ""
    branch = lines[1].strip() if len(lines) > 1 else ""
    if not toplevel:
        return "", ""
    repo = os.path.basename(toplevel)
    if branch == "HEAD":  # detached HEAD — fall back to the short SHA
        try:
            sha = subprocess.run(
                ["git", "-C", cwd, "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=1,
            )
            branch = sha.stdout.strip() or "HEAD"
        except (OSError, subprocess.SubprocessError):
            branch = "HEAD"
    return repo, branch


def _format_git(repo: str, branch: str) -> str:
    """Render the leading ``<repo> <branch>`` segment.

    On the default branch ("main") only the branch symbol is shown (green);
    on any other branch the name is shown (yellow).  Returns "" when *repo*
    is empty so the caller can omit the whole segment.
    """
    if not repo:
        return ""
    out = f"{_CYAN}{repo}{_RESET}"
    if not branch:
        return out
    if branch == "main":
        return f"{out} {_GREEN}{_BRANCH_SYMBOL}{_RESET}"
    return f"{out} {_YELLOW}{_BRANCH_SYMBOL} {branch}{_RESET}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    # On Windows the status line is spawned with stdout as a pipe, so Python
    # encodes it with the locale code page (e.g. GBK/CP936) rather than UTF-8.
    # That code page cannot encode the branch glyph U+2387 (or other non-ASCII
    # output), so print() raises UnicodeEncodeError and the status line renders
    # blank on every refresh. Force UTF-8 (replace-on-error) so the line always
    # emits regardless of the system code page.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

    raw = sys.stdin.read()
    try:
        data: dict = json.loads(raw)
    except json.JSONDecodeError:
        # Gracefully degrade — emit nothing rather than crashing.
        return

    # --- model --------------------------------------------------------------
    model: str = (
        (data.get("model") or {}).get("display_name")
        or (data.get("model") or {}).get("id")
        or "?"
    )

    # --- effort / output style ----------------------------------------------
    # effortLevel lives in settings.json, not in the payload; output_style.name
    # is a payload field for response verbosity. Prefer settings effortLevel.
    effort: str = _read_effort_from_settings()
    if not effort:
        effort = (data.get("output_style") or {}).get("name") or "default"

    # --- context % ----------------------------------------------------------
    ctx_pct = (data.get("context_window") or {}).get("used_percentage")
    if ctx_pct is None:
        ctx_str = "ctx ?%"
    else:
        pct_val = float(ctx_pct)
        color   = _color_ctx(pct_val)
        # Round to nearest integer for display.
        ctx_str = f"ctx {color}{pct_val:.0f}%{_RESET}"

    # --- cache: hit rate + last-turn completion time -----------------------
    # hit% uses the authoritative payload counters from the last API call.
    # HH:MM is the local system time of the last turn completion, derived
    # from the transcript mtime (Claude Code rewrites the transcript at
    # turn end). Both fields omit independently when source data is absent.
    cache_str = ""
    cache_parts: list[str] = []

    usage = (data.get("context_window") or {}).get("current_usage") or {}
    cache_read = usage.get("cache_read_input_tokens")
    cache_create = usage.get("cache_creation_input_tokens")
    if cache_read is not None and cache_create is not None:
        total = cache_read + cache_create
        if total > 0:
            hit_pct = 100.0 * cache_read / total
            if hit_pct >= 90:
                hit_color = _GREEN
            elif hit_pct >= 50:
                hit_color = _YELLOW
            else:
                hit_color = _RED
            cache_parts.append(f"{hit_color}{hit_pct:.0f}%{_RESET}")

    transcript_path = data.get("transcript_path")
    if transcript_path:
        try:
            mtime = os.path.getmtime(transcript_path)
            cache_parts.append(time.strftime("%H:%M", time.localtime(mtime)))
        except OSError:
            pass

    if cache_parts:
        cache_str = "cache " + " ".join(cache_parts)

    # --- rate-limit windows: usage % + time remaining ----------------------
    # Render each window as "<label> <used%> · <time-to-reset>", e.g.
    # "5h 42% · 2h34m".  Percentage is colored with the same thresholds as
    # ctx so the eye catches approaching caps quickly.  Either piece can
    # be missing independently (e.g. at the start of a session only
    # resets_at may be populated) — in that case we render just the half
    # we have.  The whole slot disappears only when both pieces are absent.
    now_epoch = int(time.time())

    def _render_window(label: str, block: dict | None) -> str:
        if not block:
            return ""
        pieces: list[str] = []

        pct = block.get("used_percentage")
        if pct is not None:
            try:
                pct_val = float(pct)
                pieces.append(f"{_color_ctx(pct_val)}{pct_val:.0f}%{_RESET}")
            except (TypeError, ValueError):
                pass

        reset = block.get("resets_at")
        if reset is not None:
            try:
                remaining = int(reset) - now_epoch
                pieces.append(_format_remaining(remaining))
            except (TypeError, ValueError):
                pass

        if not pieces:
            return ""
        return f"{label} " + " · ".join(pieces)

    rate_limits = data.get("rate_limits") or {}
    five_str = _render_window("5h", rate_limits.get("five_hour"))
    week_str = _render_window("7d", rate_limits.get("seven_day"))

    # --- git repo / branch (shown first) ------------------------------------
    cwd = (
        data.get("cwd")
        or (data.get("workspace") or {}).get("current_dir")
        or (data.get("workspace") or {}).get("project_dir")
        or os.environ.get("CLAUDE_PROJECT_DIR", "")
    )
    repo, branch = _git_repo_and_branch(cwd)
    git_str = _format_git(repo, branch)

    # --- assemble -----------------------------------------------------------
    parts: list[str] = []
    if git_str:
        parts.append(git_str)
    parts.append(model)
    parts.append(effort)
    parts.append(ctx_str)
    if cache_str:
        parts.append(cache_str)
    if five_str:
        parts.append(five_str)
    if week_str:
        parts.append(week_str)

    print(" | ".join(parts))


if __name__ == "__main__":
    main()
