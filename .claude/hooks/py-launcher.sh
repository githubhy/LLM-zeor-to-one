#!/usr/bin/env bash
# Cross-platform Python 3 launcher for the cache-warmer hooks.
#
# Resolves a working Python >= 3.8 interpreter and execs it with the given arguments,
# handling all three environments the hooks run in:
#   - Linux / macOS: `python3` exists (canonical); `python` is often absent or is python2.
#   - Windows: `python` is the real interpreter; `python3` resolves to the Microsoft Store
#     app-execution-alias stub, which prints "Python was not found" and exits non-zero.
#
# Strategy: try python3 FIRST (correct on POSIX), but VERIFY each candidate actually runs
# Python 3.8+ via a `-c` probe — this rejects the Windows stub (probe fails) and python2
# (version check fails), then falls through to `python` / `py`.
#
# Usage:  bash py-launcher.sh /path/to/hook.py [args...]
set -u
for cand in python3 python py; do
  if "$cand" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 8) else 1)' >/dev/null 2>&1; then
    exec "$cand" "$@"
  fi
done
echo "py-launcher.sh: no working Python >= 3.8 interpreter found (tried python3, python, py)" >&2
exit 1
