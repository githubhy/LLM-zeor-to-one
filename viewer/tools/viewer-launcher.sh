#!/bin/bash
# Start / stop / inspect the local markdown viewer without a terminal.
#
# This is the logic behind "Survey Viewer.app" (built by tools/make-mac-app.sh).
# The .app bundle is a thin shim that calls `start` here, so editing this file
# takes effect immediately -- no rebuild.
#
#   viewer-launcher.sh start   [-p PORT] [-- <serve.js args>]
#   viewer-launcher.sh stop
#   viewer-launcher.sh restart [-p PORT] [-- <serve.js args>]
#   viewer-launcher.sh status
#   viewer-launcher.sh open
#
# Env overrides: VIEWER_PORT, VIEWER_NODE, VIEWER_STATE_DIR, VIEWER_NO_BROWSER,
#                VIEWER_GUI (1 = report failures as a Finder dialog too).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIEWER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$VIEWER_DIR/.." && pwd)"

STATE_DIR="${VIEWER_STATE_DIR:-$HOME/Library/Application Support/SurveyViewer}"
PID_FILE="$STATE_DIR/viewer.pid"
PORT_FILE="$STATE_DIR/viewer.port"
REPO_FILE="$STATE_DIR/viewer.repo"
LOG_FILE="$STATE_DIR/viewer.log"

die() {
  echo "viewer-launcher: $*" >&2
  if [ "${VIEWER_GUI:-}" = "1" ]; then
    /usr/bin/osascript -e "display alert \"Survey Viewer\" message \"$* \n\nLog: $LOG_FILE\" as critical" >/dev/null 2>&1
  fi
  exit 1
}

# --- node discovery -----------------------------------------------------------
# A Finder-launched .app inherits PATH=/usr/bin:/bin:/usr/sbin:/sbin -- NOT the
# login shell's. Homebrew, nvm, fnm, volta and asdf all install outside that, so
# a bare `node` works in Terminal and fails on double-click. Search explicitly.
resolve_node() {
  if [ -n "${VIEWER_NODE:-}" ]; then
    [ -x "$VIEWER_NODE" ] || die "VIEWER_NODE is set but not executable: $VIEWER_NODE"
    NODE="$VIEWER_NODE"; return 0
  fi
  local c
  for c in "$(command -v node 2>/dev/null)" /opt/homebrew/bin/node /usr/local/bin/node /usr/bin/node; do
    if [ -n "$c" ] && [ -x "$c" ]; then NODE="$c"; return 0; fi
  done
  for c in "$HOME"/.volta/bin/node \
           "$HOME"/.nvm/versions/node/*/bin/node \
           "$HOME"/Library/Application\ Support/fnm/node-versions/*/installation/bin/node \
           "$HOME"/.local/share/fnm/node-versions/*/installation/bin/node \
           "$HOME"/.asdf/installs/nodejs/*/bin/node; do
    if [ -x "$c" ]; then NODE="$c"; return 0; fi
  done
  die "no node executable found. Install Node 18+ (brew install node), or set VIEWER_NODE to its full path."
}

# --- port / identity probes ---------------------------------------------------
port_busy() { /usr/bin/nc -z 127.0.0.1 "$1" >/dev/null 2>&1; }

# True only when the port serves OUR viewer. Guards against attaching to an
# unrelated dev server that happens to hold port 3000.
probe_viewer() {
  local body
  body="$(/usr/bin/curl -fsS --max-time 2 "http://127.0.0.1:$1/api/files" 2>/dev/null)" || return 1
  case "$body" in *'"schema"'*'"roots"'*) return 0 ;; esac
  return 1
}

running_pid() {
  [ -f "$PID_FILE" ] || return 1
  local pid; pid="$(tr -d '[:space:]' <"$PID_FILE" 2>/dev/null)"
  [ -n "$pid" ] || return 1
  kill -0 "$pid" 2>/dev/null || return 1
  printf '%s' "$pid"
}

saved_port() {
  # The -f guard is load-bearing: an input redirection from a missing file is
  # reported by the SHELL, so `2>/dev/null` on the command does not silence it.
  local p=""
  [ -f "$PORT_FILE" ] && p="$(tr -d '[:space:]' <"$PORT_FILE" 2>/dev/null)"
  printf '%s' "${p:-${VIEWER_PORT:-3000}}"
}

saved_repo() {
  local r=""
  [ -f "$REPO_FILE" ] && r="$(cat "$REPO_FILE" 2>/dev/null)"
  printf '%s' "$r"
}

clear_state() { rm -f "$PID_FILE" "$PORT_FILE" "$REPO_FILE"; }

# --- browser ------------------------------------------------------------------
# Chromium's --app= yields a standalone window with no tab strip or omnibox --
# the native-app feel, from the browser the test suite already targets.
open_browser() {
  [ -n "${VIEWER_NO_BROWSER:-}" ] && return 0
  local url="http://localhost:$1/" app
  for app in "/Applications/Google Chrome.app" \
             "$HOME/Applications/Google Chrome.app" \
             "/Applications/Microsoft Edge.app" \
             "/Applications/Brave Browser.app"; do
    if [ -d "$app" ]; then
      /usr/bin/open -na "$app" --args --app="$url" >/dev/null 2>&1 && return 0
    fi
  done
  /usr/bin/open "$url" >/dev/null 2>&1
}

# --- commands -----------------------------------------------------------------
cmd_status() {
  local pid port; port="$(saved_port)"
  if pid="$(running_pid)"; then
    if probe_viewer "$port"; then
      echo "running (pid $pid, port $port) -- http://localhost:$port/"
      local r; r="$(saved_repo)"
      [ -n "$r" ] && echo "  repo: $r"
      return 0
    fi
    echo "starting or not responding (pid $pid, port $port) -- log: $LOG_FILE"
    return 2
  fi
  clear_state
  echo "stopped"
  return 1
}

cmd_start() {
  local port="${PORT_OPT:-${VIEWER_PORT:-3000}}" pid

  if probe_viewer "$port"; then
    local live_repo; live_repo="$(saved_repo)"
    # One serve.js on one port serves ONE repo. If the live server belongs to a
    # different repo, "already running" would silently show the wrong corpus --
    # the failure mode being fixed here, not a new one. Hand the port over.
    if [ -n "$live_repo" ] && [ "$live_repo" != "$REPO_ROOT" ]; then
      echo "port $port is serving a different repo ($live_repo) -- switching to $REPO_ROOT"
      cmd_stop >/dev/null
    else
      if pid="$(running_pid)"; then
        echo "already running (pid $pid, port $port)"
      else
        echo "already running (port $port, started outside this launcher)"
      fi
      open_browser "$port"
      return 0
    fi
  fi

  port_busy "$port" && die "port $port is held by something that is not the viewer. Stop it, or pass -p to pick another port."

  resolve_node
  clear_state
  mkdir -p "$STATE_DIR" || die "cannot create state dir: $STATE_DIR"

  # No args after `--` means serve.js discovers viewer.content.json by walking
  # up from cwd, which is why we cd to the repo root first.
  cd "$REPO_ROOT" || die "cannot cd to repo root: $REPO_ROOT"
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') starting: $NODE $VIEWER_DIR/serve.js ${PASSTHRU[*]:-} -p $port" >>"$LOG_FILE" 2>&1

  "$NODE" "$VIEWER_DIR/serve.js" ${PASSTHRU[@]+"${PASSTHRU[@]}"} -p "$port" >>"$LOG_FILE" 2>&1 &
  pid=$!
  printf '%s\n' "$pid"  >"$PID_FILE"
  printf '%s\n' "$port" >"$PORT_FILE"
  printf '%s\n' "$REPO_ROOT" >"$REPO_FILE"

  local i
  for i in $(seq 1 100); do
    probe_viewer "$port" && break
    if ! kill -0 "$pid" 2>/dev/null; then
      clear_state
      die "viewer exited during startup. Last log lines:
$(tail -n 5 "$LOG_FILE" 2>/dev/null)"
    fi
    sleep 0.2
  done

  probe_viewer "$port" || { clear_state; kill "$pid" 2>/dev/null; die "viewer did not answer on port $port within 20s -- log: $LOG_FILE"; }

  echo "running (pid $pid, port $port) -- http://localhost:$port/"
  open_browser "$port"
  return 0
}

cmd_stop() {
  local pid port i; port="$(saved_port)"
  if ! pid="$(running_pid)"; then
    clear_state
    if probe_viewer "$port"; then
      echo "a viewer is running on port $port but was not started by this launcher -- stop it where it was started"
      return 1
    fi
    echo "stopped"
    return 0
  fi

  kill "$pid" 2>/dev/null
  for i in $(seq 1 50); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
  kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null

  # Do not return until the socket is actually free, or the next start races it.
  for i in $(seq 1 50); do
    port_busy "$port" || break
    sleep 0.1
  done
  clear_state
  echo "stopped"
  return 0
}

# --- arg parsing --------------------------------------------------------------
CMD="${1:-status}"; shift 2>/dev/null || true
PORT_OPT=""
PASSTHRU=()
while [ $# -gt 0 ]; do
  case "$1" in
    -p|--port) PORT_OPT="${2:-}"; shift 2 ;;
    --) shift; PASSTHRU=("$@"); break ;;
    -h|--help) CMD="help"; shift ;;
    *) PASSTHRU+=("$1"); shift ;;
  esac
done

case "$CMD" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  restart) cmd_stop >/dev/null; cmd_start ;;
  status)  cmd_status ;;
  open)    open_browser "$(saved_port)" ;;
  help|-h|--help)
    sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    ;;
  *) die "unknown command: $CMD (expected start|stop|restart|status|open)" ;;
esac
