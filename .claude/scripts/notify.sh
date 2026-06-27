#!/usr/bin/env bash
# notify.sh — flag-gated Pushover notifier with HTML-formatted messages.
#
# Subcommands:
#   notify.sh on               enable (create flag file)
#   notify.sh off              disable (remove flag file)
#   notify.sh status           print on/off
#   notify.sh once [MSG]       fire one message, bypasses flag
#   notify.sh send [MSG]       fire only if flag is present (default for hooks)
#
# When MSG is omitted, notify.sh pipes its stdin to compose-notify-msg.py,
# which emits an HTML message with a color status dot, worktree/branch,
# turn duration, tool-call count, and error count. The Stop hook passes its
# stdin JSON (containing transcript_path) through this pipeline automatically.
#
# Required env:
#   PUSHOVER_TOKEN   app API token from https://pushover.net/apps
#   PUSHOVER_USER    user key from https://pushover.net/ dashboard
#
# Optional env:
#   NOTIFY_FLAG      flag file path (default: $HOME/.notify-on)
#   NOTIFY_TITLE     Pushover title (default: "Claude Code")
#   NOTIFY_PRIORITY  Pushover priority -2..2 (default: -1, silent popup)
#   NOTIFY_TTL       seconds before Pushover auto-clears (default: 86400)

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPER="$SCRIPT_DIR/compose-notify-msg.py"

FLAG="${NOTIFY_FLAG:-$HOME/.notify-on}"
TITLE="${NOTIFY_TITLE:-Claude: $(basename "$PWD")}"
PRIORITY="${NOTIFY_PRIORITY:--1}"
TTL="${NOTIFY_TTL:-86400}"
API="https://api.pushover.net/1/messages.json"

fallback_msg() {
  # Pure-bash fallback when the python helper is unavailable.
  local dir branch
  dir="$(basename "$PWD")"
  branch="$(git -C "$PWD" branch --show-current 2>/dev/null || true)"
  if [ -n "$branch" ]; then
    printf 'Claude done: %s (%s)' "$dir" "$branch"
  else
    printf 'Claude done: %s' "$dir"
  fi
}

compose_msg() {
  # $1 = user-provided text (may be empty)
  # When user_text is non-empty, bypass hook-JSON parsing by disconnecting stdin.
  local user_text="${1:-}"
  local out=""
  if [ -n "$user_text" ]; then
    out="$(python "$HELPER" --text "$user_text" </dev/null 2>/dev/null)"
  else
    out="$(python "$HELPER" 2>/dev/null)"
  fi
  if [ -z "$out" ]; then
    fallback_msg
  else
    printf '%s' "$out"
  fi
}

send_pushover() {
  local msg="$1"
  if [ -z "${PUSHOVER_TOKEN:-}" ] || [ -z "${PUSHOVER_USER:-}" ]; then
    return 0  # no creds → silent no-op
  fi
  curl -s --max-time 5 --noproxy '*' \
    --form-string "token=$PUSHOVER_TOKEN" \
    --form-string "user=$PUSHOVER_USER" \
    --form-string "title=$TITLE" \
    --form-string "message=$msg" \
    --form-string "html=1" \
    --form-string "priority=$PRIORITY" \
    --form-string "ttl=$TTL" \
    "$API" >/dev/null 2>&1 || true
}

cmd="${1:-send}"
[ $# -gt 0 ] && shift
user_msg="$*"

case "$cmd" in
  on)     touch "$FLAG"; echo "notify: on ($FLAG)" ;;
  off)    rm -f "$FLAG"; echo "notify: off" ;;
  status) if [ -f "$FLAG" ]; then echo on; else echo off; fi ;;
  once)
    msg="$(compose_msg "$user_msg")"
    send_pushover "$msg"
    ;;
  send)
    if [ -f "$FLAG" ]; then
      msg="$(compose_msg "$user_msg")"
      send_pushover "$msg"
    fi
    ;;
  *)
    echo "Usage: notify.sh {on|off|status|once [MSG]|send [MSG]}" >&2; exit 2
    ;;
esac
