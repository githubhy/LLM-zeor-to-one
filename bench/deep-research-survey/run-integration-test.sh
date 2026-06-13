#!/usr/bin/env bash
# run-integration-test.sh — one headless deep-research-survey run, scored.
#
# Modelled on superpowers tests/claude-code/test-*.sh: launch a real headless
# Claude Code session, then verify behaviour by PARSING THE TRANSCRIPT (not the
# user-facing output), plus token/cost analysis and (if a survey was produced)
# mechanical quality metrics.
#
# REQUIRES the `claude` CLI. A full survey run is EXPENSIVE (10-60+ min, large
# token spend). Start with one topic before scaling to the A/B matrix.
#
# Usage:
#   bash run-integration-test.sh --arm baseline --topic-id prach \
#        --prompt "Use the deep-research-survey skill to produce a survey on <topic>." \
#        [--survey-out surveys/_bench/prach.md] [--results-dir results]
set -euo pipefail

ARM=baseline; TOPIC_ID=topic; PROMPT=""; SURVEY_OUT=""; RESULTS_DIR=results
while [[ $# -gt 0 ]]; do case "$1" in
  --arm) ARM="$2"; shift 2;;
  --topic-id) TOPIC_ID="$2"; shift 2;;
  --prompt) PROMPT="$2"; shift 2;;
  --survey-out) SURVEY_OUT="$2"; shift 2;;
  --results-dir) RESULTS_DIR="$2"; shift 2;;
  *) echo "unknown arg: $1" >&2; exit 1;;
esac; done
[[ -n "$PROMPT" ]] || { echo "ERROR: --prompt required" >&2; exit 1; }
command -v claude >/dev/null || { echo "ERROR: 'claude' CLI not found in PATH" >&2; exit 2; }

ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
HERE="$ROOT/bench/deep-research-survey"
mkdir -p "$RESULTS_DIR"
STAMP="${ARM}_${TOPIC_ID}"   # pass a unique stamp via --topic-id per repeat, e.g. prach-r1
echo "=== running headless: arm=$ARM topic=$TOPIC_ID ==="

# 1. Run the session headless. bypassPermissions so it can fetch/write unattended.
timeout 5400 claude -p "$PROMPT" \
  --allowed-tools=all \
  --permission-mode bypassPermissions \
  2>&1 | tee "$RESULTS_DIR/${STAMP}.log" || echo "(claude exited non-zero or timed out)"

# 2. Locate the freshest session transcript for this project.
SLUG="$(echo "$ROOT" | sed 's|/|-|g')"
SESSION_DIR="$HOME/.claude/projects/$SLUG"
TRANSCRIPT="$(find "$SESSION_DIR" -maxdepth 1 -name '*.jsonl' -mmin -120 2>/dev/null | xargs ls -t 2>/dev/null | head -1)"
[[ -n "$TRANSCRIPT" ]] || { echo "ERROR: no recent transcript in $SESSION_DIR" >&2; exit 3; }
echo "transcript: $TRANSCRIPT"

# 3. Behavioural assertions + token/cost (process metrics).
ASSERT_JSON="$(python3 "$HERE/assert_transcript.py" "$TRANSCRIPT" --json || true)"
TOKEN_JSON="$(python3 "$HERE/analyze_tokens.py" "$TRANSCRIPT" --json || true)"
python3 "$HERE/assert_transcript.py" "$TRANSCRIPT" || true
python3 "$HERE/analyze_tokens.py" "$TRANSCRIPT" || true

# 4. Mechanical quality metrics, if a survey deliverable was named.
MECH_JSON='{}'
if [[ -n "$SURVEY_OUT" && -e "$SURVEY_OUT" ]]; then
  MECH_JSON="$(bash "$HERE/mechanical_metrics.sh" --json "$SURVEY_OUT" || true)"
  bash "$HERE/mechanical_metrics.sh" "$SURVEY_OUT" || true
fi

# 5. Emit a single result record for ab_compare.py.
python3 - "$ARM" "$RESULTS_DIR/${STAMP}.result.json" "$ASSERT_JSON" "$TOKEN_JSON" "$MECH_JSON" <<'PY'
import json, sys
arm, out, a, t, m = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
def j(s, d=None):
    try: return json.loads(s)
    except Exception: return d or {}
a, t, m = j(a), j(t), j(m, {})
checks = {c["name"]: (c["status"] == "PASS") for c in a.get("checks", [])}
metrics = {**{f"assert_{k}": v for k, v in checks.items()},
           "process_passed": a.get("passed", False),
           "total_cost_usd": t.get("total_cost_usd", 0.0)}
for k, v in (m.get("metrics") or {}).items():
    if isinstance(v, bool): metrics[f"mech_{k}"] = v
json.dump({"arm": arm, "metrics": metrics}, open(out, "w"), indent=2)
print(f"\nwrote result -> {out}")
PY
echo "Tip: also run score_rubric.py on the deliverable and add a judge run for Tier-2 quality."
