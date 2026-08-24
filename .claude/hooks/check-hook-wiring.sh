#!/usr/bin/env bash
# Verify (and self-heal) the git-hook wiring — SessionStart.
#
# WHY THIS LIVES OUTSIDE GIT'S HOOK SYSTEM
# ----------------------------------------
# A git hook cannot report that it is disabled. That self-reference is the whole
# bug: on 2026-07-12 the pre-push gate was silently dead TWICE in one day
#, and each time the gate reported nothing, because the thing
# that would have reported it was the thing that was off.
#
#   1. core.hooksPath pointed at .git/hooks -> a stale 31-line COPY ran 5 of 11 checks.
#   2. Then, after fixing the pointer, .githooks/pre-push was mode 100644 -- and git
#      SILENTLY IGNORES a non-executable hook (a `hint:` on stderr, then it pushes).
#      So the DOCUMENTED install yielded ZERO gates. That is why the copy kept
#      coming back: the "correct" setup was worse than the broken one.
#
# So the detector must run somewhere the drift cannot silence it. The Claude Code
# harness runs SessionStart independently of git, which makes it a sound terminus
# for the "who gates the gate?" regress.
#
# It AUTO-REPAIRS rather than merely warning: install-git-hooks.sh is idempotent and
# already correct, so a fresh clone self-heals on its first session. A warning you
# have to act on is a warning you will eventually ignore.
#
# KNOWN LIMIT, stated honestly: `git push --no-verify` still bypasses everything, and
# nothing local can stop that. That is acceptable -- it is a DELIBERATE, explicit act,
# not a silent failure. This hook closes every SILENT path, which is the achievable bar
# for a local-only setup. (A truly unbypassable gate needs CI.)
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -d .githooks ] || exit 0          # not this repo; nothing to assert
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

problems=()

# 1 — the pointer
actual="$(git config --get core.hooksPath || echo '')"
[ "$actual" = ".githooks" ] || problems+=("core.hooksPath is '${actual:-unset}', not '.githooks'")

# 2 — the executable bit. THE one that actually bit us: git skips a non-executable
#     hook with only a hint, so the gate reports nothing while running nothing.
[ -x .githooks/pre-push ] || problems+=(".githooks/pre-push is NOT executable — git would silently skip it")

# 3 — a stale copy, which springs back to life the moment the pointer moves
GIT_COMMON="$(git rev-parse --git-common-dir 2>/dev/null || echo .git)"
[ -f "$GIT_COMMON/hooks/pre-push" ] && problems+=("a stale copy exists at $GIT_COMMON/hooks/pre-push")

if [ ${#problems[@]} -eq 0 ]; then
    exit 0                          # healthy: say nothing
fi

echo "[hook-wiring] GIT HOOKS WERE NOT ARMED — the pre-push gate would not have run:" >&2
for p in "${problems[@]}"; do
    echo "[hook-wiring]   - $p" >&2
done

if [ -x scripts/install-git-hooks.sh ] || [ -f scripts/install-git-hooks.sh ]; then
    echo "[hook-wiring] auto-repairing (scripts/install-git-hooks.sh is idempotent)…" >&2
    bash scripts/install-git-hooks.sh >/dev/null 2>&1
    if [ "$(git config --get core.hooksPath)" = ".githooks" ] && [ -x .githooks/pre-push ] \
       && [ ! -f "$GIT_COMMON/hooks/pre-push" ]; then
        echo "[hook-wiring] REPAIRED — the full gate is armed again." >&2
    else
        echo "[hook-wiring] REPAIR FAILED — run: bash scripts/install-git-hooks.sh" >&2
    fi
else
    echo "[hook-wiring] run: git config core.hooksPath .githooks && chmod +x .githooks/*" >&2
fi

exit 0   # never block the session; the point is to be LOUD and to fix it
