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
exit "$rc"
