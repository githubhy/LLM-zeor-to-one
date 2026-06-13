#!/bin/sh
# cache-warmer-extend.sh — UserPromptSubmit hook for /keep-cache-warm.
#
# If this session's warmer marker exists: refresh its mtime (the liveness
# signal cache-warmer-tick.sh's GC keys on). Prints NOTHING.
#
# No re-arm instruction is injected — bug 2026-06-11-03 (reopened):
# ScheduleWakeup is turn-terminal on claude-code >= 2.1.173 (the model is
# never re-invoked after the tool result), so a user-turn re-arm either
# kills the answer before generation (arm-first) or hides it behind the
# trailing call (arm-last). User turns therefore never call ScheduleWakeup;
# the wakeup armed by the last firing simply fires on schedule, and firing
# turns are cheap once the cache is warm.
#
# Minimal-moving-parts redesign (decision 2026-06-11-12): no per-prompt
# TTL detection, no command-body injection, no Python dependency.

PROJ="${CLAUDE_PROJECT_DIR:-$PWD}"
# Hook payload is harness-generated JSON on stdin; the session_id field is
# format-stable, so extract it without Python.
SID=$(grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed 's/.*"\(.*\)"/\1/')
[ -n "$SID" ] || exit 0
MARKER="$PROJ/.claude/cache-warmer.$SID.active"
[ -f "$MARKER" ] || exit 0
touch "$MARKER"
exit 0
