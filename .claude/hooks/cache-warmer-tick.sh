#!/usr/bin/env bash
# cache-warmer-tick.sh — one firing of the /keep-cache-warm loop.
#
# Refreshes this session's auto-extend marker, prunes dead-session markers,
# then prints the detected live cache TTL (integer seconds) on stdout.
#
# Usage: cache-warmer-tick.sh   (no arguments)
#
# Marker contract (decision 2026-06-11-12): presence enables the
# cache-warmer-extend.sh UserPromptSubmit reminder for this session; mtime is
# the liveness signal — refreshed here on every firing and by the extend hook
# on every user prompt, so a marker older than GC_WINDOW belongs to a dead
# session. Content is unused.
#
# Windows accommodations carry over from bugs 2026-06-01-01 / 2026-06-01-02.

SID="${CLAUDE_CODE_SESSION_ID:-}"

# CLAUDE_PROJECT_DIR is not reliably exported to the Bash tool (empty on
# Windows); fall back to the git toplevel, then PWD. Normalize to a
# forward-slash drive path (C:/Users/..) via cygpath -m so native-Windows
# Python can read it; on POSIX cygpath is absent and the path passes through.
PROJ="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
command -v cygpath >/dev/null 2>&1 && PROJ="$(cygpath -m "$PROJ")"

MARKER="$PROJ/.claude/cache-warmer.${SID}.active"
mkdir -p "$(dirname "$MARKER")"
touch "$MARKER"

# ── dead-session marker GC (bug 2026-06-11-05) ──
GC_WINDOW=86400
NOW=$(date +%s)
for M in "$PROJ/.claude/"cache-warmer.*.active; do
  [ -f "$M" ] || continue
  # GNU first, BSD second, each in its OWN substitution.  `$(A || B)` is wrong here:
  # GNU `stat -f` means "filesystem status", so it dumps a block of filesystem info to
  # stdout and *then* exits non-zero on the unknown %m format — the fallback's output
  # is appended to that garbage and the later $((NOW - MT)) dies with a syntax error.
  # Consequence: this GC never ran on Git Bash, and dead markers accumulated forever.
  MT=$(stat -c %Y "$M" 2>/dev/null) || MT=$(stat -f %m "$M" 2>/dev/null) || continue
  case "$MT" in ''|*[!0-9]*) continue ;; esac   # never feed non-numeric to $(( ))
  [ $((NOW - MT)) -gt "$GC_WINDOW" ] && rm -f "$M"
done

# ── TTL detection ──
# Locate the transcript by its (unique) session-id filename instead of
# rebuilding the mangled project-folder slug; normalize for Windows Python.
TRANSCRIPT="$(ls "$HOME/.claude/projects/"*/"$SID.jsonl" 2>/dev/null | head -n1)"
command -v cygpath >/dev/null 2>&1 && [ -n "$TRANSCRIPT" ] && TRANSCRIPT="$(cygpath -m "$TRANSCRIPT")"

# Helpers resolve as siblings of this script so the same file works in both
# project scope (.claude/hooks/) and user scope (~/.claude/hooks/).
HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
command -v cygpath >/dev/null 2>&1 && HOOKS_DIR="$(cygpath -m "$HOOKS_DIR")"

# py-launcher.sh selects a real Python >= 3.8 (skips the Windows Store python3
# stub); fall back to bare python3 if a user-scope install didn't copy it.
if [ -f "$HOOKS_DIR/py-launcher.sh" ]; then
  TTL="$(bash "$HOOKS_DIR/py-launcher.sh" "$HOOKS_DIR/detect-ttl.py" \
    --session-id "$SID" --project-dir "$PROJ" --transcript "$TRANSCRIPT")"
else
  TTL="$(python3 "$HOOKS_DIR/detect-ttl.py" \
    --session-id "$SID" --project-dir "$PROJ" --transcript "$TRANSCRIPT")"
fi

# Publish the TTL and derived re-arm delay into the marker CONTENT (previously
# unused) so the UserPromptSubmit extend hook can re-arm the wakeup on user
# activity with the correct delay — the recovery path for bugs/2026-07-14-03.
# delay = max(60, TTL-30), matching the skill's Step 2 arithmetic.
case "$TTL" in ''|*[!0-9]*) TTL=300 ;; esac
DELAY=$((TTL - 30)); [ "$DELAY" -lt 60 ] && DELAY=60
printf 'ttl=%s delay=%s\n' "$TTL" "$DELAY" > "$MARKER"

echo "$TTL"   # preserve the stdout contract: Step 1 reads this integer
