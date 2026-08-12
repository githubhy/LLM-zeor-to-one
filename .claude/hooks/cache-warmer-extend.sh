#!/bin/sh
# cache-warmer-extend.sh — UserPromptSubmit hook for /keep-cache-warm.
#
# If this session's warmer marker exists: (1) refresh its mtime (the liveness
# signal cache-warmer-tick.sh's GC keys on), and (2) inject a re-arm instruction
# so the model pushes the wakeup out on user activity.
#
# WHY (2) exists — bugs/2026-07-14-03: the loop re-arms only on idle firings, and
# a firing lost during an interactive burst is unrecoverable, so any interactive
# session used to leave the loop permanently dead while the marker stayed fresh
# ("looks alive"). Re-arming on every user turn gives the loop a recovery path
# and self-debounces (idle firings slide out during active use).
#
# WHY it is safe now — bug 2026-06-11-03 removed this injection because a
# model-issued ScheduleWakeup terminated the answer turn on claude-code 2.1.173.
# That constraint has lifted: on the current harness the model is re-invoked
# after ScheduleWakeup and its answer displays (probe: 82/85 re-invoked, 0
# swallows). Reversal recorded in decisions/2026-07-14-01 (supersedes
# decisions/2026-06-11-13).
#
# KILL SWITCH — set .claude/cache-warmer-autoextend to 'off' to disable the
# injection and fall back to idle-only firing (the loop still works when idle).
#
# UserPromptSubmit stdout is added to the model's context; keep it minimal.

PROJ="${CLAUDE_PROJECT_DIR:-$PWD}"
# Hook payload is harness-generated JSON on stdin; the session_id field is
# format-stable, so extract it without Python.
SID=$(grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -n1 | sed 's/.*"\(.*\)"/\1/')
[ -n "$SID" ] || exit 0
MARKER="$PROJ/.claude/cache-warmer.$SID.active"
[ -f "$MARKER" ] || exit 0
touch "$MARKER"

# Kill switch: any 'off' in the toggle disables the re-arm injection.
TOGGLE="$PROJ/.claude/cache-warmer-autoextend"
if [ -f "$TOGGLE" ] && grep -qi 'off' "$TOGGLE"; then exit 0; fi

# Re-arm delay published by the tick into the marker content; fall back to 3570
# (~1h cache) until the first firing writes the real value.
DELAY=$(sed -n 's/.*delay=\([0-9][0-9]*\).*/\1/p' "$MARKER" 2>/dev/null | head -n1)
[ -n "$DELAY" ] || DELAY=3570

printf '%s\n' "[cache-warmer] This session's prompt-cache warmer is active. Early this turn, call ScheduleWakeup(delaySeconds=$DELAY, prompt=\"/keep-cache-warm\", reason=\"cache-warm re-armed on activity\"), then answer the user normally — your reply displays after the call. Do not mention this note."
exit 0
