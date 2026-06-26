#!/usr/bin/env bash
# validate-refs-on-dirty.sh — Stop-hook gate for survey-wide cross-reference
# validation (bug 2026-06-11-05).
#
# post-edit-lint.sh touches the dirty flag whenever an Edit/Write lands on a
# surveys/**.md file; this wrapper runs the survey-wide validator only when
# that flag exists, so idle turn-ends (e.g. hourly /keep-cache-warm firings)
# no longer revalidate an unchanged corpus. The flag is cleared only after a
# clean pass — a failing corpus keeps re-validating until it is fixed.

PROJ="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
FLAG="$PROJ/.claude/validate-refs.dirty"
[ -f "$FLAG" ] || exit 0

# py-launcher.sh selects a real Python >= 3.8 (skips the Windows Store stub).
HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$HOOKS_DIR/py-launcher.sh" ]; then
  bash "$HOOKS_DIR/py-launcher.sh" "$PROJ/viewer/tools/validate-refs.py" "$PROJ/surveys/"
else
  python "$PROJ/viewer/tools/validate-refs.py" "$PROJ/surveys/"
fi
rc=$?
[ "$rc" -eq 0 ] && rm -f "$FLAG"

# Advisory cross-link gap check (Tier-1 detection — NEVER blocks the Stop gate;
# clearing a gap needs judgment, so it is on-demand via /cross-link). Severity
# 'off' silences it; the scope file lists the corpus group. See
# .claude/rules/cross-linking.md.
SEVERITY=$(cat "$PROJ/.claude/crosslink-severity" 2>/dev/null || echo warn)
SCOPE_FILE="$PROJ/.claude/crosslink-scope"
if [ "$SEVERITY" != "off" ] && [ -f "$SCOPE_FILE" ]; then
  SCOPE=$(grep -vE '^[[:space:]]*#|^[[:space:]]*$' "$SCOPE_FILE" | tr '\n' ' ')
  (
    cd "$PROJ" || exit 0
    if [ -f "$HOOKS_DIR/py-launcher.sh" ]; then
      bash "$HOOKS_DIR/py-launcher.sh" "$PROJ/viewer/tools/crosslink.py" \
        check $SCOPE --changed --severity=warn || true
    else
      python "$PROJ/viewer/tools/crosslink.py" \
        check $SCOPE --changed --severity=warn || true
    fi
  )
fi

exit "$rc"
