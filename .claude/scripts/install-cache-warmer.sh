#!/usr/bin/env bash
# install-cache-warmer.sh — install, check, or uninstall /keep-cache-warm.
#
# Components managed:
#   - commands/keep-cache-warm.md     (the /keep-cache-warm slash command)
#   - hooks/log-turn-telemetry.py     (Stop hook — per-turn API diagnostics)
#   - hooks/detect-ttl.py             (CLI helper — reads diagnostics, returns TTL)
#   - hooks/cache-warmer-tick.sh      (per-firing helper — marker + TTL in one call)
#   - hooks/cache-warmer-extend.sh    (UserPromptSubmit hook — auto-extends on activity)
#   - settings(.local).json           (Stop + UserPromptSubmit registrations)
#   - .gitignore                      (project mode: .claude/diagnostics/ + marker pattern)
#
# Usage:
#   bash install-cache-warmer.sh                         # install, project = pwd
#   bash install-cache-warmer.sh --project <path>        # install into <path>
#   bash install-cache-warmer.sh --user                  # install into ~/.claude/
#   bash install-cache-warmer.sh --check [--user|--project]   # report install state (read-only)
#   bash install-cache-warmer.sh --uninstall [--user|--project] [--dry-run]
#   bash install-cache-warmer.sh --dry-run [...]         # show changes, write nothing
#   bash install-cache-warmer.sh --help
#
# Exit codes:
#   0 = success / fully installed (for --check)
#   1 = bad args / partially installed (--check)
#   2 = missing dependency / not installed (--check)
#   3 = missing source files (install mode)
#   4 = settings JSON malformed
#   5 = post-install verification failure
#
# Idempotent: re-running install skips unchanged files and won't double-register hooks.
# Pre-edit backups of settings(.local).json land in *.bak.<unix-ts>.

set -euo pipefail

# ─── pre-flight: shell + python3 ─────────────────────────────────────────────
if [ -z "${BASH_VERSION:-}" ]; then
  echo "ERROR: this installer requires bash (got non-bash shell). Run as: bash $0" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found in PATH. Install python3 and re-run." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── arg parsing ──────────────────────────────────────────────────────────────
ACTION="install"  # install | check | uninstall
MODE="project"
TARGET=""
DRY_RUN=false

usage() {
  sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user) MODE=user; shift;;
    --project)
      MODE=project
      if [[ $# -ge 2 && "$2" != --* ]]; then TARGET="$2"; shift 2; else shift; fi
      ;;
    --check) ACTION=check; shift;;
    --uninstall) ACTION=uninstall; shift;;
    --dry-run) DRY_RUN=true; shift;;
    --help|-h) usage; exit 0;;
    *) echo "ERROR: unknown arg: $1" >&2; usage >&2; exit 1;;
  esac
done

# --check is read-only; --dry-run is meaningless with it
if [[ "$ACTION" == "check" && "$DRY_RUN" == "true" ]]; then
  echo "ERROR: --check is read-only; --dry-run has no effect with it." >&2
  exit 1
fi

# ─── resolve paths ────────────────────────────────────────────────────────────
if [[ "$MODE" == "user" ]]; then
  TARGET_ROOT="$HOME/.claude"
  SETTINGS_FILE="$TARGET_ROOT/settings.json"
  HOOK_CMD_PATH='$HOME/.claude/hooks'
  SCOPE_LABEL="user (~/.claude/)"
else
  [[ -z "$TARGET" ]] && TARGET="$(pwd)"
  if [[ ! -d "$TARGET" ]]; then
    echo "ERROR: --project target does not exist: $TARGET" >&2
    exit 1
  fi
  TARGET="$(cd "$TARGET" && pwd)"
  TARGET_ROOT="$TARGET/.claude"
  SETTINGS_FILE="$TARGET_ROOT/settings.local.json"
  HOOK_CMD_PATH='$CLAUDE_PROJECT_DIR/.claude/hooks'
  SCOPE_LABEL="project ($TARGET)"
fi
COMMAND_DIR="$TARGET_ROOT/commands"
HOOK_DIR="$TARGET_ROOT/hooks"

# Target dir writable check (only for write actions)
if [[ "$ACTION" != "check" && "$DRY_RUN" != "true" ]]; then
  parent_dir="$TARGET_ROOT"
  while [[ ! -d "$parent_dir" ]]; do
    parent_dir="$(dirname "$parent_dir")"
  done
  if [[ ! -w "$parent_dir" ]]; then
    echo "ERROR: not writable: $parent_dir (need to create or write under $TARGET_ROOT)" >&2
    exit 2
  fi
fi

SRC_COMMAND="$SOURCE_ROOT/commands/keep-cache-warm.md"
SRC_TELEMETRY="$SOURCE_ROOT/hooks/log-turn-telemetry.py"
SRC_DETECT="$SOURCE_ROOT/hooks/detect-ttl.py"
SRC_TICK="$SOURCE_ROOT/hooks/cache-warmer-tick.sh"
SRC_EXTEND="$SOURCE_ROOT/hooks/cache-warmer-extend.sh"

# Cache-warmer command strings the installer writes (used for matching during
# uninstall and verification — substring match tolerates minor manual edits).
STOP_CMD='python3 "'"$HOOK_CMD_PATH"'/log-turn-telemetry.py"'
PROMPT_CMD='sh "'"$HOOK_CMD_PATH"'/cache-warmer-extend.sh"'

GITIGNORE_LINES=(
  ".claude/diagnostics/"
  ".claude/cache-warmer.*.active"
)

log() { echo "[$ACTION] $*"; }

# ─── helpers ──────────────────────────────────────────────────────────────────
validate_settings_json() {
  if [[ -f "$SETTINGS_FILE" ]]; then
    if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SETTINGS_FILE" 2>/dev/null; then
      echo "ERROR: $SETTINGS_FILE exists but is not valid JSON." >&2
      echo "       Inspect or remove it, then re-run. Aborting to avoid corruption." >&2
      exit 4
    fi
  fi
}

settings_has_hook() {
  # Args: hook_type cmd_substring → exit 0 if present, 1 if not
  local hook_type="$1" needle="$2"
  [[ -f "$SETTINGS_FILE" ]] || return 1
  python3 - "$SETTINGS_FILE" "$hook_type" "$needle" <<'PYEOF'
import json, sys
path, hook_type, needle = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.load(open(path))
for grp in data.get("hooks", {}).get(hook_type, []):
    for h in grp.get("hooks", []):
        if needle in h.get("command", ""):
            sys.exit(0)
sys.exit(1)
PYEOF
}

# ─── install action ───────────────────────────────────────────────────────────
copy_file() {
  local src="$1" dst="$2" make_exec="$3"
  if [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
    log "skip (unchanged): $dst"
    return
  fi
  if $DRY_RUN; then
    log "DRY: cp -p '$src' -> '$dst'"
    if $make_exec; then log "DRY: chmod +x '$dst'"; fi
  else
    cp -p "$src" "$dst"
    $make_exec && chmod +x "$dst"
    log "wrote: $dst"
  fi
}

merge_hook() {
  local hook_type="$1" cmd="$2" async_flag="$3"
  if $DRY_RUN; then
    log "DRY: merge $hook_type hook into $SETTINGS_FILE (async=$async_flag)"
    return
  fi
  python3 - "$SETTINGS_FILE" "$hook_type" "$cmd" "$async_flag" <<'PYEOF'
import json, sys, time
from pathlib import Path
path = Path(sys.argv[1])
hook_type = sys.argv[2]
cmd = sys.argv[3]
async_flag = sys.argv[4].lower() == "true"
data = json.loads(path.read_text()) if path.exists() else {}
hooks = data.setdefault("hooks", {})
groups = hooks.setdefault(hook_type, [])
already = any(
    h.get("type") == "command" and h.get("command") == cmd
    for grp in groups for h in grp.get("hooks", [])
)
if already:
    print(f"[install] skip ({hook_type} already registered)")
    sys.exit(0)
if path.exists():
    bak = path.with_suffix(path.suffix + f".bak.{int(time.time())}")
    bak.write_bytes(path.read_bytes())
    print(f"[install] backup: {bak}")
entry = {"type": "command", "command": cmd}
if async_flag: entry["async"] = True
groups.append({"hooks": [entry]})
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"[install] wrote {hook_type} hook -> {path}")
PYEOF
}

append_gitignore_line() {
  local line="$1" comment="$2" file="$TARGET/.gitignore"
  if [[ -f "$file" ]] && grep -qxF "$line" "$file"; then
    log "skip (already in .gitignore): $line"
  elif $DRY_RUN; then
    log "DRY: append $line -> $file"
  else
    if [[ -n "$comment" ]]; then
      printf '\n# %s\n%s\n' "$comment" "$line" >> "$file"
    else
      printf '%s\n' "$line" >> "$file"
    fi
    log "appended: $line"
  fi
}

verify_install() {
  local failed=0
  local f
  for f in "$COMMAND_DIR/keep-cache-warm.md" \
           "$HOOK_DIR/log-turn-telemetry.py" \
           "$HOOK_DIR/detect-ttl.py" \
           "$HOOK_DIR/cache-warmer-tick.sh" \
           "$HOOK_DIR/cache-warmer-extend.sh"; do
    if [[ -f "$f" ]]; then
      echo "  ✓ $f"
    else
      echo "  ✗ MISSING: $f" >&2; failed=$((failed+1))
    fi
  done
  if settings_has_hook "Stop" "log-turn-telemetry.py"; then
    echo "  ✓ Stop hook registered in $SETTINGS_FILE"
  else
    echo "  ✗ MISSING: Stop hook in $SETTINGS_FILE" >&2; failed=$((failed+1))
  fi
  if settings_has_hook "UserPromptSubmit" "cache-warmer-extend"; then
    echo "  ✓ UserPromptSubmit hook registered in $SETTINGS_FILE"
  else
    echo "  ✗ MISSING: UserPromptSubmit hook in $SETTINGS_FILE" >&2; failed=$((failed+1))
  fi
  if [[ "$MODE" == "project" ]]; then
    for line in "${GITIGNORE_LINES[@]}"; do
      if [[ -f "$TARGET/.gitignore" ]] && grep -qxF "$line" "$TARGET/.gitignore"; then
        echo "  ✓ .gitignore: $line"
      else
        echo "  ✗ MISSING: .gitignore line: $line" >&2; failed=$((failed+1))
      fi
    done
  fi
  if [[ $failed -gt 0 ]]; then
    echo "[install] VERIFY FAILED: $failed item(s) missing." >&2
    exit 5
  fi
}

cmd_install() {
  for f in "$SRC_COMMAND" "$SRC_TELEMETRY" "$SRC_DETECT" "$SRC_TICK" "$SRC_EXTEND"; do
    [[ -f "$f" ]] || { echo "ERROR: missing source $f" >&2; exit 3; }
  done

  log "scope:  $SCOPE_LABEL"
  log "source: $SOURCE_ROOT"
  $DRY_RUN && log "DRY-RUN: no files will be modified"

  validate_settings_json

  if $DRY_RUN; then
    log "DRY: mkdir -p '$COMMAND_DIR' '$HOOK_DIR'"
  else
    mkdir -p "$COMMAND_DIR" "$HOOK_DIR"
  fi

  copy_file "$SRC_TELEMETRY" "$HOOK_DIR/log-turn-telemetry.py"  true
  copy_file "$SRC_DETECT"    "$HOOK_DIR/detect-ttl.py"          true
  copy_file "$SRC_TICK"      "$HOOK_DIR/cache-warmer-tick.sh"   true
  copy_file "$SRC_EXTEND"    "$HOOK_DIR/cache-warmer-extend.sh" true

  # The command body is scope-agnostic: it falls back to ~/.claude/hooks/ when
  # the tick script is absent from the project, and the tick script resolves
  # its helpers as siblings of itself. No user-scope sed patching needed.
  local cmd_dest="$COMMAND_DIR/keep-cache-warm.md"
  copy_file "$SRC_COMMAND" "$cmd_dest" false

  merge_hook "Stop"             "$STOP_CMD"   true
  merge_hook "UserPromptSubmit" "$PROMPT_CMD" false

  if [[ "$MODE" == "project" ]]; then
    append_gitignore_line ".claude/diagnostics/"           "Claude Code cache-warmer diagnostics"
    append_gitignore_line ".claude/cache-warmer.*.active"  "Claude Code cache-warmer auto-extend markers"
  fi

  if ! $DRY_RUN; then
    echo
    log "Verifying install..."
    verify_install
    echo
    log "Done."
  else
    echo
    log "Dry-run complete; no changes written."
  fi
  log "  slash command: $cmd_dest"
  log "  hooks:         $HOOK_DIR/{log-turn-telemetry,detect-ttl,cache-warmer-extend}.py + cache-warmer-tick.sh"
  log "  settings:      $SETTINGS_FILE"
  [[ "$MODE" == "project" ]] && log "  gitignore:     $TARGET/.gitignore"
  echo
  log "Next: start a fresh Claude Code session (or reload settings) and run /keep-cache-warm."
  log "Options: --no-auto-extend (disable auto-extension), --staleness-days N (default 7)."
}

# ─── check action ─────────────────────────────────────────────────────────────
cmd_check() {
  validate_settings_json

  log "scope: $SCOPE_LABEL"
  local present=0 missing=0
  check_path() {
    local label="$1" path="$2"
    if [[ -f "$path" ]]; then
      log "  PRESENT: $label ($path)"
      present=$((present+1))
    else
      log "  MISSING: $label ($path)"
      missing=$((missing+1))
    fi
  }
  check_path "slash command"        "$COMMAND_DIR/keep-cache-warm.md"
  check_path "Stop hook script"     "$HOOK_DIR/log-turn-telemetry.py"
  check_path "TTL detector"         "$HOOK_DIR/detect-ttl.py"
  check_path "Tick helper"          "$HOOK_DIR/cache-warmer-tick.sh"
  check_path "Auto-extend hook"     "$HOOK_DIR/cache-warmer-extend.sh"

  if settings_has_hook "Stop" "log-turn-telemetry.py"; then
    log "  REGISTERED: Stop hook in $SETTINGS_FILE"
    present=$((present+1))
  else
    log "  NOT REGISTERED: Stop hook in $SETTINGS_FILE"
    missing=$((missing+1))
  fi
  if settings_has_hook "UserPromptSubmit" "cache-warmer-extend"; then
    log "  REGISTERED: UserPromptSubmit hook in $SETTINGS_FILE"
    present=$((present+1))
  else
    log "  NOT REGISTERED: UserPromptSubmit hook in $SETTINGS_FILE"
    missing=$((missing+1))
  fi

  if [[ "$MODE" == "project" ]]; then
    for line in "${GITIGNORE_LINES[@]}"; do
      if [[ -f "$TARGET/.gitignore" ]] && grep -qxF "$line" "$TARGET/.gitignore"; then
        log "  PRESENT: .gitignore line: $line"
        present=$((present+1))
      else
        log "  MISSING: .gitignore line: $line"
        missing=$((missing+1))
      fi
    done
  fi

  local total=$((present+missing))
  echo
  if [[ $missing -eq 0 ]]; then
    log "Summary: INSTALLED ($present/$total)"
    exit 0
  elif [[ $present -eq 0 ]]; then
    log "Summary: NOT INSTALLED (0/$total)"
    exit 2
  else
    log "Summary: PARTIAL ($present/$total)"
    exit 1
  fi
}

# ─── uninstall action ─────────────────────────────────────────────────────────
strip_hook() {
  local hook_type="$1" needle="$2"
  if $DRY_RUN; then
    log "DRY: strip $hook_type hook (cmd contains '$needle') from $SETTINGS_FILE"
    return
  fi
  [[ -f "$SETTINGS_FILE" ]] || { log "skip (settings absent): $SETTINGS_FILE"; return; }
  python3 - "$SETTINGS_FILE" "$hook_type" "$needle" <<'PYEOF'
import json, sys, time
from pathlib import Path
path = Path(sys.argv[1])
hook_type = sys.argv[2]
needle = sys.argv[3]
data = json.loads(path.read_text())
hooks = data.get("hooks", {})
groups = hooks.get(hook_type, [])
new_groups = []
removed = 0
for grp in groups:
    new_hooks = [h for h in grp.get("hooks", []) if needle not in h.get("command", "")]
    removed += len(grp.get("hooks", [])) - len(new_hooks)
    if new_hooks:
        new_grp = dict(grp); new_grp["hooks"] = new_hooks
        new_groups.append(new_grp)
if removed == 0:
    print(f"[uninstall] skip ({hook_type} hook not present in {path})")
    sys.exit(0)
bak = path.with_suffix(path.suffix + f".bak.{int(time.time())}")
bak.write_bytes(path.read_bytes())
print(f"[uninstall] backup: {bak}")
if new_groups:
    hooks[hook_type] = new_groups
else:
    hooks.pop(hook_type, None)
if not hooks:
    data.pop("hooks", None)
path.write_text(json.dumps(data, indent=2) + "\n")
print(f"[uninstall] stripped {removed} {hook_type} hook(s) -> {path}")
PYEOF
}

remove_gitignore_line() {
  local line="$1" file="$TARGET/.gitignore"
  if [[ ! -f "$file" ]] || ! grep -qxF "$line" "$file"; then
    log "skip (gitignore line absent): $line"
    return
  fi
  if $DRY_RUN; then
    log "DRY: remove gitignore line: $line"
    return
  fi
  # grep -v with exact-line match isn't trivial; use awk
  awk -v target="$line" '$0 != target' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
  log "removed gitignore line: $line"
}

remove_path() {
  local path="$1"
  if [[ ! -e "$path" ]]; then
    log "skip (absent): $path"
    return
  fi
  if $DRY_RUN; then
    log "DRY: rm -f $path"
  else
    rm -f "$path"
    log "removed: $path"
  fi
}

cmd_uninstall() {
  validate_settings_json

  log "scope: $SCOPE_LABEL"
  $DRY_RUN && log "DRY-RUN: nothing will be removed"
  if [[ "$MODE" == "user" ]]; then
    log "WARNING: --user uninstall affects every repo's CC session (removes user-scoped hooks)."
  fi

  remove_path "$COMMAND_DIR/keep-cache-warm.md"
  remove_path "$HOOK_DIR/log-turn-telemetry.py"
  remove_path "$HOOK_DIR/detect-ttl.py"
  remove_path "$HOOK_DIR/cache-warmer-tick.sh"
  # Both forms: .sh is current; .py lingers from pre-2026-06-11-12 installs.
  remove_path "$HOOK_DIR/cache-warmer-extend.sh"
  remove_path "$HOOK_DIR/cache-warmer-extend.py"

  strip_hook "Stop"             "log-turn-telemetry.py"
  strip_hook "UserPromptSubmit" "cache-warmer-extend"

  if [[ "$MODE" == "project" ]]; then
    for line in "${GITIGNORE_LINES[@]}"; do
      remove_gitignore_line "$line"
    done
    # Marker files (per-session)
    local markers=("$TARGET_ROOT"/cache-warmer.*.active)
    if [[ -e "${markers[0]}" ]]; then
      if $DRY_RUN; then
        log "DRY: remove ${#markers[@]} marker file(s) in $TARGET_ROOT/"
      else
        rm -f "$TARGET_ROOT"/cache-warmer.*.active
        log "removed ${#markers[@]} marker file(s)"
      fi
    fi
    # Diagnostics dir — warn, do NOT remove
    if [[ -d "$TARGET_ROOT/diagnostics" ]]; then
      local logcount
      logcount=$(find "$TARGET_ROOT/diagnostics" -name "*.jsonl" 2>/dev/null | wc -l | tr -d ' ')
      log "Note: $TARGET_ROOT/diagnostics/ NOT removed (contains $logcount log file(s)). Remove manually if desired:"
      log "    rm -rf '$TARGET_ROOT/diagnostics/'"
    fi
  fi

  echo
  log "Done."
}

# ─── dispatch ─────────────────────────────────────────────────────────────────
case "$ACTION" in
  install)    cmd_install;;
  check)      cmd_check;;
  uninstall)  cmd_uninstall;;
esac
