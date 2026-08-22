#!/bin/bash
# Resolve WHICH viewer repository the Mac app should serve.
#
# This is the app's bootstrap: it runs before any repo is known, so a copy of it
# lives inside the .app bundle (Contents/Resources/pick-repo.sh). It is the only
# copied file -- everything else still runs from the selected repo, so there is
# nothing here that can drift out of sync with viewer logic. Re-run
# make-mac-app.sh to refresh the copy.
#
#   pick-repo.sh resolve  [--no-ui]   # env > remembered > ask; prints the repo
#   pick-repo.sh choose   [--no-ui]   # always ask (recents menu); prints the repo
#   pick-repo.sh list                 # print the valid recents, most recent first
#   pick-repo.sh remember <path>      # push a repo to the top of the recents
#   pick-repo.sh forget  [<path>]     # drop one repo, or all of them
#   pick-repo.sh validate <path>      # exit 0 if <path> is a viewer repo
#
# Env: VIEWER_REPO (wins over everything), VIEWER_STATE_DIR, VIEWER_MRU_MAX.

set -uo pipefail

STATE_DIR="${VIEWER_STATE_DIR:-$HOME/Library/Application Support/SurveyViewer}"
MRU_FILE="$STATE_DIR/repos.txt"
MRU_MAX="${VIEWER_MRU_MAX:-10}"
NO_UI=""

note() { echo "pick-repo: $*" >&2; }

# A directory is a viewer repo when it can actually serve: it must carry BOTH the
# launcher we are about to exec and the server that launcher runs. Checking only
# for a .git dir would accept any clone; checking only the launcher would accept a
# half-copied tree.
is_repo() {
  [ -n "${1:-}" ] || return 1
  [ -x "$1/viewer/tools/viewer-launcher.sh" ] && [ -f "$1/viewer/serve.js" ]
}

# --- recents (MRU) ------------------------------------------------------------
read_mru() {
  [ -f "$MRU_FILE" ] || return 0
  # Entries that no longer validate are skipped on read, so a deleted or moved
  # repo silently ages out of the menu instead of offering a dead choice.
  local line
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    is_repo "$line" && printf '%s\n' "$line"
  done <"$MRU_FILE"
}

remember() {
  local repo="$1" existing
  [ -n "$repo" ] || return 1
  mkdir -p "$STATE_DIR" || return 1
  existing="$( [ -f "$MRU_FILE" ] && grep -vxF "$repo" "$MRU_FILE" 2>/dev/null )"
  { printf '%s\n' "$repo"; [ -n "$existing" ] && printf '%s\n' "$existing"; } \
    | grep -v '^$' | head -n "$MRU_MAX" >"$MRU_FILE.tmp" 2>/dev/null
  mv "$MRU_FILE.tmp" "$MRU_FILE" 2>/dev/null
}

forget() {
  if [ -n "${1:-}" ]; then
    [ -f "$MRU_FILE" ] || return 0
    grep -vxF "$1" "$MRU_FILE" >"$MRU_FILE.tmp" 2>/dev/null
    mv "$MRU_FILE.tmp" "$MRU_FILE" 2>/dev/null
  else
    rm -f "$MRU_FILE"
  fi
}

# --- dialogs ------------------------------------------------------------------
# Every UI entry point goes through here, so --no-ui makes the whole script
# headless and testable rather than each call site having to remember.
ui_blocked() {
  if [ -n "$NO_UI" ]; then
    note "would prompt for a repository, but --no-ui was given"
    return 0
  fi
  return 1
}

browse_for_repo() {
  ui_blocked && return 1
  local chosen
  chosen="$(/usr/bin/osascript -e 'try' \
    -e 'POSIX path of (choose folder with prompt "Select a viewer repository (the folder containing viewer/)")' \
    -e 'on error' -e 'return ""' -e 'end try' 2>/dev/null)"
  chosen="${chosen%/}"
  [ -n "$chosen" ] || return 1
  printf '%s' "$chosen"
}

# Recents menu, with a trailing "Other..." that falls through to the folder
# browser. With no recents there is nothing to choose from, so go straight there.
choose_repo() {
  local recents other="Other (browse)..." picked
  recents="$(read_mru)"
  if [ -z "$recents" ]; then
    browse_for_repo
    return $?
  fi
  ui_blocked && return 1

  picked="$(printf '%s\n' "$recents" \
    | /usr/bin/osascript - "Open which repository?" "$other" 2>/dev/null <<'AS'
on run argv
  set prompt_ to item 1 of argv
  set otherLabel to item 2 of argv
  set raw to (do shell script "cat")
  set AppleScript's text item delimiters to linefeed
  set opts to text items of raw
  set AppleScript's text item delimiters to ""
  set opts to opts & {otherLabel}
  set chosen to choose from list opts with prompt prompt_ default items {item 1 of opts}
  if chosen is false then return ""
  return item 1 of chosen
end run
AS
)"

  [ -n "$picked" ] || return 1
  if [ "$picked" = "$other" ]; then
    browse_for_repo
    return $?
  fi
  printf '%s' "$picked"
}

# Ask until we get a real repo or the user cancels. A wrong pick is the most
# likely mistake here (picking viewer/ instead of its parent), so name the fix.
choose_repo_validated() {
  local candidate
  while :; do
    candidate="$(choose_repo)" || return 1
    [ -n "$candidate" ] || return 1
    if is_repo "$candidate"; then
      remember "$candidate"
      printf '%s' "$candidate"
      return 0
    fi
    if is_repo "$(dirname "$candidate")"; then
      candidate="$(dirname "$candidate")"
      remember "$candidate"
      printf '%s' "$candidate"
      return 0
    fi
    note "not a viewer repository: $candidate"
    if [ -n "$NO_UI" ]; then return 1; fi
    /usr/bin/osascript -e "display alert \"Survey Viewer\" message \"That folder is not a viewer repository:

$candidate

Pick the folder that CONTAINS viewer/ -- not viewer/ itself.\" as warning" >/dev/null 2>&1
  done
}

resolve_repo() {
  # 1. An explicit environment override always wins, and is never remembered --
  #    a one-off override should not reorder the menu.
  if [ -n "${VIEWER_REPO:-}" ]; then
    if is_repo "$VIEWER_REPO"; then printf '%s' "$VIEWER_REPO"; return 0; fi
    note "VIEWER_REPO is not a viewer repository: $VIEWER_REPO"
    return 1
  fi
  # 2. The last repo actually used, with no dialog: the common path.
  #
  #    Read the RAW head, not the head of the validated list. If the last-used
  #    repo has moved, falling through to the next valid entry would open a
  #    DIFFERENT corpus with no indication -- the reader would have no way to
  #    tell they are looking at the wrong repo. A vanished head is a question,
  #    not something to silently paper over, so drop to the chooser (which still
  #    lists the surviving recents).
  local head=""
  [ -f "$MRU_FILE" ] && head="$(grep -v '^$' "$MRU_FILE" 2>/dev/null | head -n 1)"
  if [ -n "$head" ]; then
    if is_repo "$head"; then printf '%s' "$head"; return 0; fi
    note "last used repository is gone or moved: $head"
  fi
  # 3. Nothing remembered, or the last one went stale -- ask.
  choose_repo_validated
}

# --- dispatch -----------------------------------------------------------------
CMD="${1:-resolve}"; shift 2>/dev/null || true
ARG=""
while [ $# -gt 0 ]; do
  case "$1" in
    --no-ui) NO_UI=1; shift ;;
    *) ARG="$1"; shift ;;
  esac
done

case "$CMD" in
  resolve)  resolve_repo ;;
  choose)   choose_repo_validated ;;
  list)     read_mru ;;
  remember) is_repo "$ARG" || { note "not a viewer repository: $ARG"; exit 1; }; remember "$ARG" ;;
  forget)   forget "$ARG" ;;
  validate) is_repo "$ARG" ;;
  help|-h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' ;;
  *) note "unknown command: $CMD"; exit 1 ;;
esac
