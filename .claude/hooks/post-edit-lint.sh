#!/bin/bash
# Post-edit hook: lint math, renumber equations, link references.
# Runs after Edit or Write on markdown files.
# Exit 2 = blocking (lint errors force Claude to fix).
# Exit 0 = non-blocking (auto-fix succeeded or file skipped).

set -uo pipefail

# Resolve a working Python >= 3 (skip the Windows Store app-execution stub);
# if none is available, degrade silently so an edit never hard-fails.
PY=""
for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && "$c" --version >/dev/null 2>&1; then
        PY="$c"; break
    fi
done
[ -z "$PY" ] && exit 0

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | "$PY" -c "import sys,json; print(json.load(sys.stdin)['tool_input'].get('file_path',''))")

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

# Each math tool is optional: a not-yet-ported / removed tool no-ops instead of
# blocking the edit. The full toolchain is present in this repo; the -f guards
# below keep the hook robust on a partial checkout or mid-refactor.

# 1. Lint math (blocking on real errors only).
if [ -f "$TOOLS/lint-math.py" ]; then
    LINT_OUT=$("$PY" "$TOOLS/lint-math.py" "$FILE_PATH" --errors-only 2>&1); LINT_RC=$?
    if [ $LINT_RC -ne 0 ]; then
        echo "$LINT_OUT" >&2
        exit 2
    fi
fi

# 1b. Bare-ref check. Severity from .claude/bare-refs-severity (default: warn).
# Error-severity BLOCKING is scoped to the survey corpus (surveys/) — the corpus
# the bare-ref / cross-link rules target (mirrors .claude/crosslink-scope). Audit-
# trail markdown (decisions/, todos/, plans/, prompts/, reports/, field-notes/)
# legitimately carries bare prose §refs like "§3.4"; those surface in warn mode
# but must never block, so the flip to error doesn't tax normal note-taking.
if [ -f "$TOOLS/validate-refs.py" ]; then
    SEVERITY=$(cat "$CLAUDE_PROJECT_DIR/.claude/bare-refs-severity" 2>/dev/null || echo "warn")
    IN_CORPUS=0
    case "$FILE_PATH" in
        */surveys/*|*\\surveys\\*) IN_CORPUS=1 ;;
    esac
    BARE_OUT=$("$PY" "$TOOLS/validate-refs.py" --bare-refs-only \
        --severity="$SEVERITY" "$FILE_PATH" 2>&1); BARE_RC=$?
    if [ "$SEVERITY" = "error" ] && [ "$IN_CORPUS" = "1" ] && [ $BARE_RC -ne 0 ]; then
        echo "$BARE_OUT" >&2
        exit 2
    fi
    # warn mode (any file): surface findings without blocking. error mode on a
    # non-corpus file: stay silent — bare prose §refs there are expected.
    if [ "$SEVERITY" = "warn" ] && [ -n "$BARE_OUT" ]; then
        echo "$BARE_OUT" >&2
    fi
fi

# 2. Renumber equations (auto-fix, non-blocking, suppress all output on success)
if [ -f "$TOOLS/renumber-equations.py" ]; then
    "$PY" "$TOOLS/renumber-equations.py" "$FILE_PATH" >/dev/null 2>/dev/null || true
fi

# 3. Link references (auto-fix, non-blocking, suppress all output on success)
if [ -f "$TOOLS/link-references.py" ]; then
    "$PY" "$TOOLS/link-references.py" "$FILE_PATH" >/dev/null 2>/dev/null || true
fi

exit 0
