#!/bin/bash
# Point git at the tracked hooks directory. One config setting, once per clone.
#
# This script used to `cp .githooks/* .git/hooks/`. A copy is a SNAPSHOT: every
# later edit to the source silently diverged, and nothing detected it. On
# 2026-07-09 the installed copy dated from 2026-05 and ran 5 of the source's 9
# checks -- the crosslink gate (at --severity=error), the section-ownership gate
# and the depth-tier gate never ran on push at all. bugs/2026-07-09-10.
#
# `core.hooksPath` makes git read `.githooks/` directly. No copy, nothing to
# re-install after a pull, and drift is structurally impossible. The path is
# relative, so it resolves correctly inside a git worktree too -- which is why
# the old `--git-common-dir` dance is gone.
#
# `.githooks/pre-push` additionally refuses to run unless core.hooksPath points
# at .githooks, so a clone that overrides it cannot silently execute a stale gate.
#
# That guard covers a STALE gate. It cannot cover an ABSENT one: when core.hooksPath
# is UNSET -- the state of every fresh clone, including every cloud session container
# -- git never invokes .githooks/pre-push at all, so nothing runs and nothing says so
# (whole-harness audit, 2026-07-26). Two things now close that window:
#   * .claude/settings.json installs core.hooksPath at SessionStart (Claude Code only);
#   * .github/workflows/validate.yml runs the same gate on a push to ANY branch.
# Running this script remains the right move for a plain terminal clone -- it is the
# only path that also clears stale .git/hooks/ copies.

set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [ ! -d .githooks ]; then
    echo "ERROR: .githooks not found." >&2
    exit 1
fi

git config core.hooksPath .githooks
chmod +x .githooks/* 2>/dev/null || true

# A leftover copy from the old installer is dead code under core.hooksPath -- but
# it would spring back to life the moment anyone unset the config.
GIT_COMMON="$(git rev-parse --git-common-dir)"
for hook in .githooks/*; do
    stale="$GIT_COMMON/hooks/$(basename "$hook")"
    if [ -f "$stale" ]; then
        rm -f "$stale"
        echo "Removed stale copy: $stale"
    fi
done

echo "core.hooksPath = $(git config --get core.hooksPath)"
echo "Active hooks:"
ls -1 .githooks | sed 's/^/  /'
