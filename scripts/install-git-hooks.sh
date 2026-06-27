#!/bin/bash
# Install tracked git hooks into .git/hooks/.
# Re-run after pulling new hook templates.

set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC="$REPO_ROOT/.githooks"
# Use --git-common-dir so the hooks land in the main repo's .git/hooks/
# even when run from inside a git worktree.
GIT_COMMON="$(git rev-parse --git-common-dir)"
DST="$GIT_COMMON/hooks"

if [ ! -d "$SRC" ]; then
    echo "ERROR: $SRC not found." >&2
    exit 1
fi

for hook in "$SRC"/*; do
    name=$(basename "$hook")
    cp "$hook" "$DST/$name"
    chmod +x "$DST/$name"
    echo "Installed: .git/hooks/$name"
done

echo "Done. Hooks active for this clone."
