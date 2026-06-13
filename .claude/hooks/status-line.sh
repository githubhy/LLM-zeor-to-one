#!/bin/bash
# Status line wrapper — delegates all JSON parsing to Python so the script works
# on Windows (Git Bash / MSYS2), Linux, and macOS without requiring jq.
#
# The full implementation lives alongside this file as status-line.py.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Probe candidates in order. On Windows, `python3` often resolves to the
# Microsoft Store App Execution Alias stub which prints an install prompt
# and exits non-zero; `--version` lets us skip it and fall through to a
# real interpreter.
PYTHON=""
for candidate in python python3 py; do
  if command -v "$candidate" >/dev/null 2>&1 \
     && "$candidate" --version >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  # No interpreter available — stay silent so Claude Code's status line
  # degrades gracefully instead of surfacing a hook error.
  exit 0
fi

exec "$PYTHON" "$SCRIPT_DIR/status-line.py"
