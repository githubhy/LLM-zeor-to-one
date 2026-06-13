#!/bin/bash
# Post-edit hook: lint math, renumber equations, link references.
# Runs after Edit or Write on markdown files.
# Exit 2 = blocking (lint errors force Claude to fix).
# Exit 0 = non-blocking (auto-fix succeeded or file skipped).

set -uo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python -c "import sys,json; print(json.load(sys.stdin)['tool_input'].get('file_path',''))")

# Skip non-markdown files
[[ "$FILE_PATH" != *.md ]] && exit 0
# Skip if file was deleted or doesn't exist
[[ ! -f "$FILE_PATH" ]] && exit 0
# Skip .claude/ directory (command templates, config — not prose).
# Path may be Windows-style (backslashes) or POSIX-style; match either.
case "$FILE_PATH" in
    */.claude/*|*\\.claude\\*) exit 0 ;;
esac

# Flag surveys/ edits for the Stop-hook cross-reference gate (bug
# 2026-06-11-05): validate-refs-on-dirty.sh runs the survey-wide validator
# only when this flag exists, instead of on every turn end.
case "$FILE_PATH" in
    */surveys/*|*\\surveys\\*) touch "$CLAUDE_PROJECT_DIR/.claude/validate-refs.dirty" ;;
esac

TOOLS="$CLAUDE_PROJECT_DIR/viewer/tools"

# 1. Lint math (blocking on errors)
LINT_OUT=$(python "$TOOLS/lint-math.py" "$FILE_PATH" --errors-only 2>&1)
LINT_RC=$?
if [ $LINT_RC -ne 0 ]; then
    echo "$LINT_OUT" >&2
    exit 2
fi

# 1b. Check for bare refs (blocking on errors during Phase 3; warn-only earlier).
# Severity is read from .claude/bare-refs-severity (default: warn during migration).
SEVERITY=$(cat "$CLAUDE_PROJECT_DIR/.claude/bare-refs-severity" 2>/dev/null || echo "warn")
BARE_OUT=$(python "$TOOLS/validate-refs.py" --bare-refs-only \
    --severity="$SEVERITY" "$FILE_PATH" 2>&1)
BARE_RC=$?
if [ "$SEVERITY" = "error" ] && [ $BARE_RC -ne 0 ]; then
    echo "$BARE_OUT" >&2
    exit 2
fi
# In warn mode, surface findings without blocking
if [ "$SEVERITY" = "warn" ] && [ -n "$BARE_OUT" ]; then
    echo "$BARE_OUT" >&2
fi

# 2. Renumber equations (auto-fix, non-blocking, suppress all output on success)
python "$TOOLS/renumber-equations.py" "$FILE_PATH" >/dev/null 2>/dev/null || true

# 3. Link references (auto-fix, non-blocking, suppress all output on success)
python "$TOOLS/link-references.py" "$FILE_PATH" >/dev/null 2>/dev/null || true

exit 0
