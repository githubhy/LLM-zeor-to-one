#!/bin/bash
# Launch the markdown viewer, auto-installing viewer/ dependencies on first run.
#
# Fixes the common "Error: Cannot find module 'ws'" crash, which happens when
# `node viewer/serve.js ...` is run before `cd viewer && npm install` — serve.js
# hard-requires `ws` (and uses `chokidar`/`ignore`), so a missing
# viewer/node_modules aborts startup. This wrapper installs the deps once, then
# forwards all arguments to serve.js unchanged. If no content root is supplied
# it defaults to serving surveys/, so a bare `-p <port>` invocation just works.
#
# Usage (relative paths resolve the same as serve.js, from the repo root):
#   scripts/serve-viewer.sh                              # serves surveys/ on :3000
#   scripts/serve-viewer.sh -p 3500                      # serves surveys/ on :3500
#   scripts/serve-viewer.sh surveys/llms-for-coding -p 3500
#   scripts/serve-viewer.sh reports/ --allow .
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIEWER_DIR="$REPO_ROOT/viewer"

# `ws` is the hard dependency whose absence produces the MODULE_NOT_FOUND crash;
# use it as the canary for "dependencies installed". A bare node_modules/ dir is
# not enough — a partial install can have the dir without ws.
if [ ! -d "$VIEWER_DIR/node_modules/ws" ]; then
  echo "viewer/node_modules missing — installing dependencies (one-time)…" >&2
  if [ -f "$VIEWER_DIR/package-lock.json" ]; then
    ( cd "$VIEWER_DIR" && npm ci )
  else
    ( cd "$VIEWER_DIR" && npm install )
  fi
fi

# Detect whether the caller already named a content root (a positional dir/file,
# --root, or --config). serve.js aborts with "no content roots" when none is
# given, so default to surveys/ for a friction-free `-p <port>` launch.
have_root=0
argv=("$@")
i=0
while [ "$i" -lt "${#argv[@]}" ]; do
  case "${argv[$i]}" in
    --root|--config) have_root=1; i=$((i + 2)); continue ;;  # flag + value, provides a root
    -p|--port|--allow) i=$((i + 2)); continue ;;             # flag + value, no root
    -*) i=$((i + 1)); continue ;;                            # bare flag, no value
    *) have_root=1; i=$((i + 1)); continue ;;                # positional dir/file = a root
  esac
done

if [ "$have_root" -eq 0 ]; then
  echo "No content root given — defaulting to $REPO_ROOT/surveys" >&2
  set -- "$REPO_ROOT/surveys" "$@"
fi

# CWD is left as the caller's so any relative paths they pass resolve as documented.
exec node "$VIEWER_DIR/serve.js" "$@"
